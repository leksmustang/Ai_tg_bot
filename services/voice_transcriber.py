from faster_whisper import WhisperModel
import asyncio
import logging

logger = logging.getLogger(__name__)
model = None
try:
    model = WhisperModel("base", device="cpu", compute_type="int8")
    logger.info("Whisper loaded")
except Exception as e:
    logger.error(f"Whisper load failed: {e}")

async def transcribe_voice(file_path: str) -> str:
    if model is None:
        return ""
    try:
        loop = asyncio.get_event_loop()
        segments, _ = await loop.run_in_executor(
            None,
            lambda: model.transcribe(file_path, language="ru", task="transcribe")
        )
        return " ".join(seg.text for seg in segments)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""