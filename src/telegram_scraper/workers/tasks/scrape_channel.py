"""Channel scraping task implementation."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import (
    Message as TelegramMessage,
    MessageMediaDocument,
    MessageMediaPhoto,
    MessageMediaWebPage,
)

from telegram_scraper.config import settings
from telegram_scraper.models.channel import Channel
from telegram_scraper.models.media import Media
from telegram_scraper.models.message import Message
from telegram_scraper.models.scraping_job import ScrapingJob
from telegram_scraper.models.telegram_session import TelegramSession
from telegram_scraper.models.user_channel import UserChannel
from telegram_scraper.services.telegram_service import decrypt_session_string

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncSession:
    """Create a database session for the worker."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def get_telegram_client(
    db: AsyncSession, session_id: uuid.UUID
) -> TelegramClient | None:
    """Get a Telegram client for a session."""
    result = await db.execute(
        select(TelegramSession).where(TelegramSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session or not session.session_string:
        return None

    string_session = StringSession(decrypt_session_string(session.session_string))
    client = TelegramClient(string_session, session.api_id, session.api_hash)
    await client.connect()
    return client


def get_media_type(message: TelegramMessage) -> str | None:
    """Determine the media type from a Telegram message."""
    if not message.media:
        return None

    if isinstance(message.media, MessageMediaPhoto):
        return "photo"
    elif isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        if doc:
            mime = doc.mime_type or ""
            if mime.startswith("video"):
                return "video"
            elif mime.startswith("audio"):
                return "audio"
            elif mime.startswith("image"):
                return "photo"
            else:
                return "document"
    elif isinstance(message.media, MessageMediaWebPage):
        return "webpage"

    return "other"


async def scrape_channel(
    job_id: str,
    user_id: str,
    channel_id: str,
    session_id: str,
    from_message_id: int = 0,
    scrape_media: bool = True,
) -> dict[str, Any]:
    """
    Scrape messages from a Telegram channel.

    Args:
        job_id: The scraping job ID
        user_id: The user ID
        channel_id: The channel database ID
        session_id: The Telegram session ID
        from_message_id: Start scraping from this message ID (for incremental)
        scrape_media: Whether to queue media downloads

    Returns:
        Dict with job results
    """
    db = await get_db_session()
    client = None
    messages_processed = 0
    media_found = 0

    try:
        # Update job status to running
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

        # Get channel info
        result = await db.execute(
            select(Channel).where(Channel.id == uuid.UUID(channel_id))
        )
        channel = result.scalar_one_or_none()
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        # Get Telegram client
        client = await get_telegram_client(db, uuid.UUID(session_id))
        if not client:
            raise ValueError("Could not create Telegram client")

        # Get the Telegram entity - need to get dialogs first to cache entities
        await client.get_dialogs()

        # Now get the entity
        try:
            entity = await client.get_entity(channel.telegram_id)
        except Exception:
            # Try by username if available
            if channel.username:
                entity = await client.get_entity(channel.username)
            else:
                raise ValueError(f"Could not find channel {channel.telegram_id}")
        logger.info(f"Scraping channel: {channel.title} ({channel.telegram_id})")

        # Get total message count estimate for progress calculation
        total_messages_estimate = 0
        try:
            # Get the channel's full info to estimate total messages
            full_channel = await client.get_entity(entity)
            # Try to get message count - this works for channels/supergroups
            async for msg in client.iter_messages(entity, limit=1):
                if msg:
                    total_messages_estimate = msg.id  # Approximate total by highest message ID
                    break
            logger.info(f"Estimated total messages: {total_messages_estimate}")
        except Exception as e:
            logger.warning(f"Could not estimate total messages: {e}")
            total_messages_estimate = 10000  # Fallback estimate

        # Iterate through messages
        batch = []
        batch_size = settings.batch_size

        async for message in client.iter_messages(
            entity,
            min_id=from_message_id,
            reverse=True,  # Start from oldest
        ):
            if not isinstance(message, TelegramMessage):
                continue

            # Check if job was cancelled
            if messages_processed % 100 == 0:
                result = await db.execute(
                    select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
                )
                job = result.scalar_one_or_none()
                if job and job.status == "cancelled":
                    logger.info(f"Job {job_id} was cancelled")
                    break

            # Check if message already exists
            result = await db.execute(
                select(Message).where(
                    Message.channel_id == channel.id,
                    Message.telegram_message_id == message.id,
                )
            )
            if result.scalar_one_or_none():
                continue  # Skip existing messages

            media_type = get_media_type(message)

            # Extract sender info
            sender_id = None
            first_name = None
            last_name = None
            username = None

            if message.sender:
                sender_id = message.sender.id
                first_name = getattr(message.sender, "first_name", None)
                last_name = getattr(message.sender, "last_name", None)
                username = getattr(message.sender, "username", None)

            # Extract reactions
            reactions = None
            if message.reactions:
                reactions = {
                    "results": [
                        {
                            "emoji": str(r.reaction),
                            "count": r.count,
                        }
                        for r in message.reactions.results
                    ]
                }

            msg_record = Message(
                channel_id=channel.id,
                telegram_message_id=message.id,
                date=message.date.replace(tzinfo=timezone.utc),
                sender_id=sender_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                message_text=message.text or message.message,
                media_type=media_type,
                reply_to_message_id=message.reply_to_msg_id if message.reply_to else None,
                post_author=message.post_author,
                views=message.views,
                forwards=message.forwards,
                reactions=reactions,
            )
            batch.append(msg_record)

            # Track media
            if media_type and scrape_media and media_type not in ["webpage"]:
                media_record = Media(
                    channel_id=channel.id,
                    telegram_message_id=message.id,
                    media_type=media_type,
                    download_status="pending",
                )
                db.add(media_record)
                media_found += 1

            messages_processed += 1

            # Batch insert
            if len(batch) >= batch_size:
                db.add_all(batch)
                await db.commit()
                batch = []

                # Update progress
                result = await db.execute(
                    select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
                )
                job = result.scalar_one_or_none()
                if job:
                    job.messages_processed = messages_processed
                    job.media_downloaded = media_found
                    # Calculate progress percentage
                    if total_messages_estimate > 0:
                        progress = min(95, (messages_processed / total_messages_estimate) * 100)
                        job.progress_percent = progress
                    await db.commit()

                logger.info(f"Processed {messages_processed} messages ({job.progress_percent:.1f}%)...")

        # Insert remaining batch
        if batch:
            db.add_all(batch)
            await db.commit()

        # Update user_channel with last scraped message
        result = await db.execute(
            select(UserChannel).where(
                UserChannel.user_id == uuid.UUID(user_id),
                UserChannel.channel_id == uuid.UUID(channel_id),
            )
        )
        user_channel = result.scalar_one_or_none()
        if user_channel and messages_processed > 0:
            # Get the max message ID we scraped
            result = await db.execute(
                select(Message.telegram_message_id)
                .where(Message.channel_id == channel.id)
                .order_by(Message.telegram_message_id.desc())
                .limit(1)
            )
            max_msg_id = result.scalar()
            if max_msg_id:
                user_channel.last_scraped_message_id = max_msg_id
                await db.commit()

        # Update job as completed
        result = await db.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job and job.status != "cancelled":
            job.status = "completed"
            job.progress_percent = 100
            job.messages_processed = messages_processed
            job.media_downloaded = media_found
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(
            f"Completed scraping job {job_id}: {messages_processed} messages, {media_found} media"
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "messages_processed": messages_processed,
            "media_found": media_found,
        }

    except Exception as e:
        logger.error(f"Error in scrape job {job_id}: {e}")

        # Update job as failed
        try:
            result = await db.execute(
                select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                job.messages_processed = messages_processed
                await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")

        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "messages_processed": messages_processed,
        }

    finally:
        if client:
            await client.disconnect()
        await db.close()
