from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.voice_service import (
    transcribe_audio,
)


router = APIRouter(
    prefix="/voice",
    tags=["Voice Assistant"],
)

# 10 MB is plenty for a short voice command.
MAX_AUDIO_BYTES = 10 * 1024 * 1024


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:

        audio_bytes = await file.read(MAX_AUDIO_BYTES + 1)

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty.",
            )

        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Audio file is too large (max 10 MB).",
            )

        transcript = await transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.webm",
        )

        return {
            "text": transcript,
        }

    except HTTPException:
        raise

    except Exception as exc:

        print("\n========== VOICE ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("=================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"Voice transcription failed: {str(exc)}",
        )
