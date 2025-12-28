"""Media download task implementation."""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from telethon import TelegramClient
from telethon.sessions import StringSession

from telegram_scraper.config import settings
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.media import Media
from telegram_scraper.models.telegram_session import TelegramSession
from telegram_scraper.services.telegram_service import decrypt_session_string

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Create a database session for the worker."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def get_telegram_client(db: AsyncSession, session_id: uuid.UUID) -> TelegramClient | None:
    """Get a Telegram client for a session."""
    result = await db.execute(select(TelegramSession).where(TelegramSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session or not session.session_string:
        return None

    string_session = StringSession(decrypt_session_string(session.session_string))
    client = TelegramClient(string_session, session.api_id, session.api_hash)
    await client.connect()
    return client


async def download_single_media(
    media_id: str,
    session_id: str,
) -> dict[str, Any]:
    """
    Download a single media file.

    Args:
        media_id: The media record ID
        session_id: The Telegram session ID

    Returns:
        Dict with download results
    """
    db = await get_db_session()
    client = None

    try:
        # Get media record
        result = await db.execute(select(Media).where(Media.id == uuid.UUID(media_id)))
        media = result.scalar_one_or_none()
        if not media:
            return {"status": "error", "error": "Media not found"}

        # Get channel info
        result = await db.execute(select(Channel).where(Channel.id == media.channel_id))
        channel = result.scalar_one_or_none()
        if not channel:
            return {"status": "error", "error": "Channel not found"}

        # Update status to downloading
        media.download_status = "downloading"
        media.download_attempts += 1
        await db.commit()

        # Get Telegram client
        client = await get_telegram_client(db, uuid.UUID(session_id))
        if not client:
            media.download_status = "failed"
            media.error_message = "Could not create Telegram client"
            await db.commit()
            return {"status": "error", "error": "Could not create Telegram client"}

        # Get dialogs to cache entities
        await client.get_dialogs()

        # Get the channel entity
        try:
            entity = await client.get_entity(channel.telegram_id)
        except Exception:
            if channel.username:
                entity = await client.get_entity(channel.username)
            else:
                raise ValueError(f"Could not find channel {channel.telegram_id}")

        # Get the message with media
        message = await client.get_messages(entity, ids=media.telegram_message_id)
        if not message or not message.media:
            media.download_status = "failed"
            media.error_message = "Message or media not found"
            await db.commit()
            return {"status": "error", "error": "Message or media not found"}

        # Create download directory
        media_path = Path(settings.media_storage_path)
        channel_dir = media_path / str(channel.id)
        channel_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        ext = ""
        if hasattr(message.media, "document") and message.media.document:
            for attr in message.media.document.attributes:
                if hasattr(attr, "file_name") and attr.file_name:
                    ext = Path(attr.file_name).suffix
                    break
            if not ext:
                mime = message.media.document.mime_type or ""
                ext_map = {
                    "video/mp4": ".mp4",
                    "audio/mpeg": ".mp3",
                    "audio/ogg": ".ogg",
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "application/pdf": ".pdf",
                }
                ext = ext_map.get(mime, ".bin")
        elif hasattr(message.media, "photo"):
            ext = ".jpg"

        filename = f"{media.telegram_message_id}_{media.id}{ext}"
        file_path = channel_dir / filename

        # Download the media
        logger.info(f"Downloading media {media_id} to {file_path}")
        await client.download_media(message, file=str(file_path))

        # Update media record
        media.file_path = str(file_path)
        media.file_name = filename
        media.download_status = "completed"
        media.downloaded_at = datetime.now(UTC)

        # Get file size
        if file_path.exists():
            media.file_size = file_path.stat().st_size

        await db.commit()

        logger.info(f"Successfully downloaded media {media_id}")
        return {
            "status": "completed",
            "media_id": media_id,
            "file_path": str(file_path),
            "file_size": media.file_size,
        }

    except Exception as e:
        logger.error(f"Error downloading media {media_id}: {e}")

        try:
            result = await db.execute(select(Media).where(Media.id == uuid.UUID(media_id)))
            media = result.scalar_one_or_none()
            if media:
                media.download_status = "failed"
                media.error_message = str(e)
                await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update media status: {db_error}")

        return {"status": "error", "error": str(e)}

    finally:
        if client:
            await client.disconnect()
        await db.close()


async def download_media_batch(
    channel_id: str,
    session_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Download a batch of pending media for a channel.

    Args:
        channel_id: The channel ID
        session_id: The Telegram session ID
        limit: Maximum number of media to download

    Returns:
        Dict with batch download results
    """
    db = await get_db_session()
    client = None
    downloaded = 0
    failed = 0

    try:
        # Get pending media
        result = await db.execute(
            select(Media)
            .where(
                Media.channel_id == uuid.UUID(channel_id),
                Media.download_status == "pending",
            )
            .limit(limit)
        )
        media_list = result.scalars().all()

        if not media_list:
            return {
                "status": "completed",
                "downloaded": 0,
                "failed": 0,
                "message": "No pending media",
            }

        # Get channel info
        result = await db.execute(select(Channel).where(Channel.id == uuid.UUID(channel_id)))
        channel = result.scalar_one_or_none()
        if not channel:
            return {"status": "error", "error": "Channel not found"}

        # Get Telegram client
        client = await get_telegram_client(db, uuid.UUID(session_id))
        if not client:
            return {"status": "error", "error": "Could not create Telegram client"}

        # Get dialogs and entity
        await client.get_dialogs()
        try:
            entity = await client.get_entity(channel.telegram_id)
        except Exception:
            if channel.username:
                entity = await client.get_entity(channel.username)
            else:
                raise ValueError(f"Could not find channel {channel.telegram_id}")

        # Create download directory
        media_path = Path(settings.media_storage_path)
        channel_dir = media_path / str(channel.id)
        channel_dir.mkdir(parents=True, exist_ok=True)

        # Download each media
        for media in media_list:
            try:
                media.download_status = "downloading"
                media.download_attempts += 1
                await db.commit()

                # Get the message
                message = await client.get_messages(entity, ids=media.telegram_message_id)
                if not message or not message.media:
                    media.download_status = "failed"
                    media.error_message = "Message or media not found"
                    await db.commit()
                    failed += 1
                    continue

                # Generate filename
                ext = ""
                if hasattr(message.media, "document") and message.media.document:
                    for attr in message.media.document.attributes:
                        if hasattr(attr, "file_name") and attr.file_name:
                            ext = Path(attr.file_name).suffix
                            break
                    if not ext:
                        mime = message.media.document.mime_type or ""
                        ext_map = {
                            "video/mp4": ".mp4",
                            "audio/mpeg": ".mp3",
                            "audio/ogg": ".ogg",
                            "image/jpeg": ".jpg",
                            "image/png": ".png",
                            "image/gif": ".gif",
                            "application/pdf": ".pdf",
                        }
                        ext = ext_map.get(mime, ".bin")
                elif hasattr(message.media, "photo"):
                    ext = ".jpg"

                filename = f"{media.telegram_message_id}_{media.id}{ext}"
                file_path = channel_dir / filename

                # Download
                await client.download_media(message, file=str(file_path))

                # Update record
                media.file_path = str(file_path)
                media.file_name = filename
                media.download_status = "completed"
                media.downloaded_at = datetime.now(UTC)
                if file_path.exists():
                    media.file_size = file_path.stat().st_size
                await db.commit()

                downloaded += 1
                logger.info(f"Downloaded {downloaded}/{len(media_list)}: {filename}")

            except Exception as e:
                logger.error(f"Error downloading media {media.id}: {e}")
                media.download_status = "failed"
                media.error_message = str(e)
                await db.commit()
                failed += 1

        return {
            "status": "completed",
            "downloaded": downloaded,
            "failed": failed,
            "total": len(media_list),
        }

    except Exception as e:
        logger.error(f"Error in batch download: {e}")
        return {"status": "error", "error": str(e), "downloaded": downloaded, "failed": failed}

    finally:
        if client:
            await client.disconnect()
        await db.close()
