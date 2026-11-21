# AI Telegram Assistant

[Русская версия](./README_RU.md)

A multimodal Telegram assistant that routes each request to the appropriate AI model or deterministic tool.

This repository is a **portfolio prototype**. It demonstrates integration and orchestration patterns; it is not presented as a turnkey production service.

## Capabilities

- LLM conversations through an OpenAI-compatible OpenRouter endpoint
- selectable strict and friendly system behavior with bounded conversation history
- image analysis with configurable Gemini or Nemotron vision models
- local Russian voice transcription with Faster-Whisper
- PDF, DOCX and TXT extraction followed by summarization or question answering
- FLUX image generation through Replicate
- deterministic equations, derivatives and integrals through SymPy
- web-page extraction, weather lookup and task routing
- free-usage limits, subscription state, admin controls and scheduled reminders

## Why it is designed this way

Not every request should be delegated directly to a language model. Mathematical operations are calculated by SymPy, document text is extracted by dedicated parsers, voice is transcribed locally, and only then is the result passed to an LLM for explanation or formatting. This makes the behavior easier to verify and extend.

## Project structure

- `handlers/` — Telegram commands and message routing
- `services/ai_client.py` — LLM conversation and history
- `services/vision_analyzer.py` — image/PDF vision requests
- `services/voice_transcriber.py` — Faster-Whisper integration
- `services/document_parser.py` — PDF, DOCX and TXT extraction
- `services/math_engine.py` — deterministic math
- `services/image_generator.py` — FLUX/Replicate integration
- `database.py` — local user, quota and subscription state

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Configure at least `TELEGRAM_TOKEN` and `OPENROUTER_API_KEY`. Optional functions require the corresponding tokens and local dependencies documented in `.env.example`.

## Current boundaries

- SQLite/local state and polling are intended for a prototype deployment.
- Payment buttons represent subscription workflow state; a production payment provider still needs to be connected and verified.
- Model identifiers are configurable because provider availability changes.
- Production use would additionally require automated tests, structured migrations, observability and a deployment-specific security review.

## Stack

Python · python-telegram-bot · OpenRouter · OpenAI-compatible API · Faster-Whisper · Replicate/FLUX · SymPy · PyPDF2 · python-docx · aiohttp
