from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.voice_service import (
    transcribe_audio,
)


router = APIRouter(
    prefix="/voice",
    tags=["Voice Assistant"],
)


@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
):
    try:

        audio_bytes = await file.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty.",
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