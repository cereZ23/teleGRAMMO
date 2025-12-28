"""Telegram session management endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from telegram_scraper.api.deps import CurrentUser, DbSession
from telegram_scraper.schemas.telegram_session import (
    PhoneLoginRequest,
    SessionStatusResponse,
    TelegramSessionCreate,
    TelegramSessionResponse,
    Verify2FARequest,
    VerifyCodeRequest,
)
from telegram_scraper.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post(
    "/sessions", response_model=TelegramSessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    session_data: TelegramSessionCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TelegramSessionResponse:
    """Create a new Telegram session."""
    session = await TelegramService.create_session(
        db=db,
        user_id=current_user.id,
        api_id=session_data.api_id,
        api_hash=session_data.api_hash,
        session_name=session_data.session_name,
    )
    return TelegramSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[TelegramSessionResponse])
async def list_sessions(
    db: DbSession,
    current_user: CurrentUser,
) -> list[TelegramSessionResponse]:
    """List all Telegram sessions for the current user."""
    sessions = await TelegramService.get_sessions(db, current_user.id)
    return [TelegramSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=TelegramSessionResponse)
async def get_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> TelegramSessionResponse:
    """Get a specific Telegram session."""
    session = await TelegramService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return TelegramSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a Telegram session."""
    deleted = await TelegramService.delete_session(db, session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/sessions/{session_id}/send-code")
async def send_code(
    session_id: UUID,
    request: PhoneLoginRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Send verification code to phone number."""
    try:
        result = await TelegramService.send_code(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            phone_number=request.phone_number,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/verify-code")
async def verify_code(
    session_id: UUID,
    request: VerifyCodeRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Verify the SMS/Telegram code."""
    try:
        result = await TelegramService.verify_code(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            code=request.code,
            phone_code_hash=request.phone_hash,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/verify-2fa")
async def verify_2fa(
    session_id: UUID,
    request: Verify2FARequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Verify 2FA password."""
    try:
        result = await TelegramService.verify_2fa(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            password=request.password,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/qr-login")
async def start_qr_login(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Start QR code login process."""
    try:
        result = await TelegramService.start_qr_login(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/qr-status")
async def check_qr_status(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Check QR code login status."""
    try:
        result = await TelegramService.check_qr_login(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> SessionStatusResponse:
    """Get session authentication status."""
    session = await TelegramService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStatusResponse(
        is_authenticated=session.is_authenticated,
        needs_code=False,
        needs_2fa=False,
    )


@router.get("/sessions/{session_id}/dialogs")
async def get_dialogs(
    session_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[dict]:
    """Get available channels/groups from Telegram account."""
    try:
        return await TelegramService.get_dialogs(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
