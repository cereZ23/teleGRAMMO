"""Channel service for managing tracked channels."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_scraper.models.channel import Channel
from telegram_scraper.models.media import Media
from telegram_scraper.models.message import Message
from telegram_scraper.models.user_channel import UserChannel
from telegram_scraper.services.telegram_service import TelegramService


class ChannelService:
    """Service for managing channels."""

    @classmethod
    async def add_channel(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        telegram_id: int,
        username: str | None = None,
        title: str | None = None,
        channel_type: str | None = None,
    ) -> Channel:
        """Add a channel to track."""
        # Check if channel already exists in DB
        result = await db.execute(select(Channel).where(Channel.telegram_id == telegram_id))
        channel = result.scalar_one_or_none()

        if not channel:
            # Get channel info from Telegram if not provided
            if not title:
                try:
                    client = await TelegramService.get_client(db, session_id, user_id)
                    if client:
                        entity = await client.get_entity(telegram_id)
                        title = getattr(entity, "title", None)
                        username = getattr(entity, "username", None)
                        channel_type = "channel" if getattr(entity, "broadcast", False) else "group"
                except Exception:
                    pass

            channel = Channel(
                telegram_id=telegram_id,
                username=username,
                title=title or f"Channel {telegram_id}",
                channel_type=channel_type,
            )
            db.add(channel)
            await db.flush()

        # Check if user already tracks this channel
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == user_id,
                UserChannel.channel_id == channel.id,
            )
        )
        user_channel = result.scalar_one_or_none()

        if not user_channel:
            user_channel = UserChannel(
                user_id=user_id,
                channel_id=channel.id,
                is_active=True,
            )
            db.add(user_channel)

        await db.commit()
        await db.refresh(channel)
        return channel

    @classmethod
    async def get_channels(cls, db: AsyncSession, user_id: uuid.UUID) -> list[dict[str, Any]]:
        """Get all channels tracked by a user with stats."""
        result = await db.execute(
            select(Channel, UserChannel)
            .join(UserChannel, UserChannel.channel_id == Channel.id)
            .where(UserChannel.user_id == user_id, UserChannel.is_active)
        )
        rows = result.all()

        channels = []
        for channel, user_channel in rows:
            # Get message count
            msg_count_result = await db.execute(
                select(func.count(Message.id)).where(Message.channel_id == channel.id)
            )
            message_count = msg_count_result.scalar() or 0

            # Get media count
            media_count_result = await db.execute(
                select(func.count(Media.id)).where(Media.channel_id == channel.id)
            )
            media_count = media_count_result.scalar() or 0

            channels.append(
                {
                    "id": channel.id,
                    "telegram_id": channel.telegram_id,
                    "username": channel.username,
                    "title": channel.title,
                    "channel_type": channel.channel_type,
                    "message_count": message_count,
                    "media_count": media_count,
                    "last_scraped_message_id": user_channel.last_scraped_message_id,
                    "scrape_media": user_channel.scrape_media,
                    "added_at": user_channel.added_at,
                }
            )

        return channels

    @classmethod
    async def get_channel(
        cls, db: AsyncSession, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict[str, Any] | None:
        """Get a specific channel with stats."""
        result = await db.execute(
            select(Channel, UserChannel)
            .join(UserChannel, UserChannel.channel_id == Channel.id)
            .where(
                Channel.id == channel_id,
                UserChannel.user_id == user_id,
                UserChannel.is_active,
            )
        )
        row = result.first()
        if not row:
            return None

        channel, user_channel = row

        # Get message count
        msg_count_result = await db.execute(
            select(func.count(Message.id)).where(Message.channel_id == channel.id)
        )
        message_count = msg_count_result.scalar() or 0

        # Get media count
        media_count_result = await db.execute(
            select(func.count(Media.id)).where(Media.channel_id == channel.id)
        )
        media_count = media_count_result.scalar() or 0

        return {
            "id": channel.id,
            "telegram_id": channel.telegram_id,
            "username": channel.username,
            "title": channel.title,
            "channel_type": channel.channel_type,
            "message_count": message_count,
            "media_count": media_count,
            "last_scraped_message_id": user_channel.last_scraped_message_id,
            "scrape_media": user_channel.scrape_media,
            "added_at": user_channel.added_at,
        }

    @classmethod
    async def remove_channel(
        cls, db: AsyncSession, channel_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Remove a channel from user's tracking (soft delete)."""
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.channel_id == channel_id,
                UserChannel.user_id == user_id,
            )
        )
        user_channel = result.scalar_one_or_none()

        if not user_channel:
            return False

        user_channel.is_active = False
        await db.commit()
        return True

    @classmethod
    async def get_available_channels(
        cls,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Get available channels from Telegram account."""
        return await TelegramService.get_dialogs(db, session_id, user_id)

    @classmethod
    async def get_messages(
        cls,
        db: AsyncSession,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        search_query: str | None = None,
        media_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        sender_id: int | None = None,
    ) -> dict[str, Any]:
        """Get messages for a channel with advanced filters."""
        # Verify user has access to channel
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.channel_id == channel_id,
                UserChannel.user_id == user_id,
                UserChannel.is_active,
            )
        )
        if not result.scalar_one_or_none():
            return {"messages": [], "total": 0, "limit": limit, "offset": offset}

        # Build filters list
        filters = [Message.channel_id == channel_id]

        # Full-text search using indexed tsvector column (web-style syntax)
        if search_query:
            search_tsquery = func.websearch_to_tsquery("simple", search_query)
            filters.append(Message.search_vector.op("@@")(search_tsquery))

        # Media type filter
        if media_type:
            filters.append(Message.media_type == media_type)

        # Date range filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=UTC)
                filters.append(Message.date >= from_date)
            except ValueError:
                pass  # Invalid date format, skip filter

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=UTC
                )
                filters.append(Message.date <= to_date)
            except ValueError:
                pass  # Invalid date format, skip filter

        # Sender filter
        if sender_id:
            filters.append(Message.sender_id == sender_id)

        # Combine all filters
        combined_filter = and_(*filters)

        # Get total count
        count_result = await db.execute(select(func.count(Message.id)).where(combined_filter))
        total = count_result.scalar() or 0

        # Get messages
        result = await db.execute(
            select(Message)
            .where(combined_filter)
            .order_by(Message.date.desc())
            .limit(limit)
            .offset(offset)
        )
        messages = result.scalars().all()

        return {
            "messages": [
                {
                    "id": msg.id,
                    "telegram_message_id": msg.telegram_message_id,
                    "date": msg.date,
                    "sender_id": msg.sender_id,
                    "first_name": msg.first_name,
                    "last_name": msg.last_name,
                    "username": msg.username,
                    "message_text": msg.message_text,
                    "media_type": msg.media_type,
                    "views": msg.views,
                    "forwards": msg.forwards,
                    "reactions": msg.reactions,
                }
                for msg in messages
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
