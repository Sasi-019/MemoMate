import os
import tempfile

import httpx
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_STT_MODEL = os.getenv(
    "GROQ_STT_MODEL",
    "whisper-large-v3-turbo",
)


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "recording.webm",
):

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is missing."
        )

    temp_path = None

    try:

        suffix = ".webm"

        if "." in filename:
            suffix = "." + filename.rsplit(".", 1)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        url = (
            "https://api.groq.com/openai/v1/"
            "audio/transcriptions"
        )

        headers = {
            "Authorization":
                f"Bearer {GROQ_API_KEY}",
        }

        with open(
            temp_path,
            "rb",
        ) as audio_file:

            files = {
                "file": (
                    filename,
                    audio_file,
                    "audio/webm",
                )
            }

            data = {
                "model": GROQ_STT_MODEL,
                "response_format": "json",
                "temperature": "0",
            }

            async with httpx.AsyncClient(
                timeout=120
            ) as client:

                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                )

        if response.status_code >= 400:

            try:
                error = response.json()
            except Exception:
                error = response.text

            raise RuntimeError(
                f"Groq transcription failed: {error}"
            )

        result = response.json()

        text = result.get(
            "text",
            "",
        ).strip()

        if not text:
            raise RuntimeError(
                "No speech was detected."
            )

        return text

    finally:

        if temp_path:

            try:
                os.remove(temp_path)
            except OSError:
                pass