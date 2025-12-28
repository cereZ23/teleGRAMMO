"""Telegram service for managing Telethon clients and authentication."""

import base64
import io
import uuid
from datetime import UTC, datetime
from typing import Any

import qrcode
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ExportLoginTokenRequest, ImportLoginTokenRequest
from telethon.tl.types import auth

from telegram_scraper.config import settings
from telegram_scraper.models.telegram_session import TelegramSession


def get_encryption_key() -> bytes:
    """Get or derive a valid Fernet key from settings."""
    key = settings.session_encryption_key.encode()
    if len(key) == 32:
        return base64.urlsafe_b64encode(key)
    return base64.urlsafe_b64encode(key.ljust(32)[:32])


def encrypt_session_string(session_string: str) -> str:
    """Encrypt a session string for storage."""
    fernet = Fernet(get_encryption_key())
    return fernet.encrypt(session_string.encode()).decode()


def decrypt_session_string(encrypted: str) -> str:
    """Decrypt a session string from storage."""
    fernet = Fernet(get_encryption_key())
    return fernet.decrypt(encrypted.encode()).decode()


class TelegramService:
    """Service for managing Telegram sessions and clients."""

    # Store active clients and auth state in memory
    _clients: dict[str, TelegramClient] = {}
    _auth_state: dict[str, dict[str, Any]] = {}

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        api_id: int,
        api_hash: str,
        session_name: str | None = None,
    ) -> TelegramSession:
        """Create a new Telegram session record."""
        session = TelegramSession(
            user_id=user_id,
            api_id=api_id,
            api_hash=api_hash,
            session_name=session_name,
            is_authenticated=False,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def get_sessions(cls, db: AsyncSession, user_id: uuid.UUID) -> list[TelegramSession]:
        """Get all Telegram sessions for a user."""
        result = await db.execute(select(TelegramSession).where(TelegramSession.user_id == user_id))
        return list(result.scalars().all())

    @classmethod
    async def get_session(
        cls, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> TelegramSession | None:
        """Get a specific session by ID."""
        result = await db.execute(
            select(TelegramSession).where(
                TelegramSession.id == session_id,
                TelegramSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def delete_session(
        cls, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete a Telegram session."""
        session = await cls.get_session(db, session_id, user_id)
        if not session:
            return False

        # Disconnect client if active
        session_key = str(session_id)
        if session_key in cls._clients:
            try:
                await cls._clients[session_key].disconnect()
            except Exception:
                pass
            del cls._clients[session_key]

        if session_key in cls._auth_state:
            del cls._auth_state[session_key]

        await db.delete(session)
        await db.commit()
        return True

    @classmethod
    async def get_client(
        cls, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> TelegramClient | None:
        """Get or create a Telegram client for a session."""
        session = await cls.get_session(db, session_id, user_id)
        if not session:
            return None

        session_key = str(session_id)

        # Return existing client if connected
        if session_key in cls._clients:
            client = cls._clients[session_key]
            if client.is_connected():
                return client

        # Create new client
        if session.session_string:
            string_session = StringSession(decrypt_session_string(session.session_string))
        else:
            string_session = StringSession()

        client = TelegramClient(string_session, session.api_id, session.api_hash)
        await client.connect()

        cls._clients[session_key] = client
        return client

    @classmethod
    async def send_code(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        phone_number: str,
    ) -> dict[str, Any]:
        """Send verification code to phone number."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session_key = str(session_id)

        try:
            result = await client.send_code_request(phone_number)
            cls._auth_state[session_key] = {
                "phone_number": phone_number,
                "phone_code_hash": result.phone_code_hash,
            }

            # Update session with phone number
            session = await cls.get_session(db, session_id, user_id)
            if session:
                session.phone_number = phone_number
                await db.commit()

            return {
                "phone_code_hash": result.phone_code_hash,
                "timeout": getattr(result, "timeout", 120),
            }
        except Exception as e:
            raise ValueError(f"Failed to send code: {str(e)}")

    @classmethod
    async def verify_code(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        code: str,
        phone_code_hash: str | None = None,
    ) -> dict[str, Any]:
        """Verify the SMS/Telegram code."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session_key = str(session_id)
        auth_state = cls._auth_state.get(session_key, {})

        phone_number = auth_state.get("phone_number")
        if not phone_number:
            session = await cls.get_session(db, session_id, user_id)
            phone_number = session.phone_number if session else None

        if not phone_number:
            raise ValueError("Phone number not found. Send code first.")

        hash_to_use = phone_code_hash or auth_state.get("phone_code_hash")
        if not hash_to_use:
            raise ValueError("Phone code hash not found. Send code first.")

        try:
            await client.sign_in(phone_number, code, phone_code_hash=hash_to_use)

            # Save session string and mark as authenticated
            session = await cls.get_session(db, session_id, user_id)
            if session:
                session_string = client.session.save()
                session.session_string = encrypt_session_string(session_string)
                session.is_authenticated = True
                session.last_used_at = datetime.now(UTC)

                me = await client.get_me()
                if me:
                    session.telegram_user_id = me.id

                await db.commit()

            # Clear auth state
            if session_key in cls._auth_state:
                del cls._auth_state[session_key]

            return {"authenticated": True}

        except Exception as e:
            error_msg = str(e).lower()
            if "2fa" in error_msg or "password" in error_msg:
                return {"authenticated": False, "needs_2fa": True}
            raise ValueError(f"Verification failed: {str(e)}")

    @classmethod
    async def verify_2fa(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        password: str,
    ) -> dict[str, Any]:
        """Verify 2FA password."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session_key = str(session_id)

        try:
            await client.sign_in(password=password)

            # Save session string and mark as authenticated
            session = await cls.get_session(db, session_id, user_id)
            if session:
                session_string = client.session.save()
                session.session_string = encrypt_session_string(session_string)
                session.is_authenticated = True
                session.last_used_at = datetime.now(UTC)

                me = await client.get_me()
                if me:
                    session.telegram_user_id = me.id

                await db.commit()

            # Clear auth state
            if session_key in cls._auth_state:
                del cls._auth_state[session_key]

            return {"authenticated": True}

        except Exception as e:
            raise ValueError(f"2FA verification failed: {str(e)}")

    @classmethod
    async def start_qr_login(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Start QR code login process."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session_key = str(session_id)

        try:
            result = await client(
                ExportLoginTokenRequest(
                    api_id=client.api_id,
                    api_hash=client.api_hash,
                    except_ids=[],
                )
            )

            if isinstance(result, auth.LoginToken):
                token = base64.urlsafe_b64encode(result.token).decode()
                qr_url = f"tg://login?token={token}"

                # Generate QR code image
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                qr_image = base64.b64encode(buffer.getvalue()).decode()

                cls._auth_state[session_key] = {
                    "qr_token": result.token,
                    "expires": result.expires,
                }

                return {
                    "qr_url": qr_url,
                    "qr_image": f"data:image/png;base64,{qr_image}",
                    "expires_at": datetime.fromtimestamp(result.expires, tz=UTC).isoformat(),
                }

            raise ValueError("Unexpected response from Telegram")

        except Exception as e:
            raise ValueError(f"Failed to start QR login: {str(e)}")

    @classmethod
    async def check_qr_login(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Check if QR code has been scanned and authenticated."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session_key = str(session_id)
        auth_state = cls._auth_state.get(session_key, {})
        qr_token = auth_state.get("qr_token")

        if not qr_token:
            return {"authenticated": False, "expired": True}

        try:
            result = await client(ImportLoginTokenRequest(token=qr_token))

            if isinstance(result, auth.LoginTokenSuccess):
                # Save session
                session = await cls.get_session(db, session_id, user_id)
                if session:
                    session_string = client.session.save()
                    session.session_string = encrypt_session_string(session_string)
                    session.is_authenticated = True
                    session.last_used_at = datetime.now(UTC)

                    me = await client.get_me()
                    if me:
                        session.telegram_user_id = me.id
                        session.phone_number = me.phone

                    await db.commit()

                if session_key in cls._auth_state:
                    del cls._auth_state[session_key]

                return {"authenticated": True}

            return {"authenticated": False, "expired": False}

        except Exception as e:
            error_msg = str(e).lower()
            if "expired" in error_msg:
                return {"authenticated": False, "expired": True}
            return {"authenticated": False, "expired": False}

    @classmethod
    async def get_dialogs(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Get available channels/groups from Telegram account."""
        client = await cls.get_client(db, session_id, user_id)
        if not client:
            raise ValueError("Session not found")

        session = await cls.get_session(db, session_id, user_id)
        if not session or not session.is_authenticated:
            raise ValueError("Session not authenticated")

        try:
            dialogs = await client.get_dialogs()
            channels = []

            for dialog in dialogs:
                entity = dialog.entity
                if hasattr(entity, "broadcast") or hasattr(entity, "megagroup"):
                    channel_type = "channel" if getattr(entity, "broadcast", False) else "group"
                    channels.append(
                        {
                            "id": entity.id,
                            "title": dialog.title,
                            "username": getattr(entity, "username", None),
                            "type": channel_type,
                            "participants_count": getattr(entity, "participants_count", None),
                        }
                    )

            # Update last used
            session.last_used_at = datetime.now(UTC)
            await db.commit()

            return channels

        except Exception as e:
            raise ValueError(f"Failed to get channels: {str(e)}")
