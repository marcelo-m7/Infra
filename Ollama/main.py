import os
import json
import time
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

# =========================
# Config
# =========================
REMOTE_OLLAMA_BASE = os.getenv("REMOTE_OLLAMA_BASE", "https://api.ai.monynha.com").rstrip("/")
VERIFY_TLS = os.getenv("VERIFY_TLS", "true").lower() in ("1", "true", "yes", "y")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "600"))

# Optional: pin a default model if Dyad sends none
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "")

app = FastAPI(title="Ollama ↔ Dyad (OpenAI Adapter)", version="1.0.0")


# =========================
# Helpers
# =========================
def _ollama_url(path: str) -> str:
    return f"{REMOTE_OLLAMA_BASE}{path}"

def _req(method: str, path: str, **kwargs):
    try:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs.setdefault("verify", VERIFY_TLS)
        return requests.request(method, _ollama_url(path), **kwargs)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e

def _to_openai_models(ollama_tags: Dict[str, Any]) -> Dict[str, Any]:
    models = ollama_tags.get("models", []) or []
    return {
        "object": "list",
        "data": [
            {
                "id": m.get("name"),
                "object": "model",
                "owned_by": "ollama",
            }
            for m in models
            if m.get("name")
        ],
    }

def _extract_last_user_message(messages: List[Dict[str, Any]]) -> str:
    # fallback if needed
    for m in reversed(messages):
        if m.get("role") == "user" and isinstance(m.get("content"), str):
            return m["content"]
    return ""


# =========================
# Health
# =========================
@app.get("/health")
def health():
    return {
        "ok": True,
        "remote": REMOTE_OLLAMA_BASE,
        "verify_tls": VERIFY_TLS,
        "ts": int(time.time()),
    }


# =========================
# OpenAI-compatible: Models
# =========================
@app.get("/v1/models")
def list_models():
    r = _req("GET", "/api/tags")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Upstream /api/tags failed: {r.status_code} {r.text}")
    return JSONResponse(_to_openai_models(r.json()))


# =========================
# OpenAI-compatible: Chat Completions
# =========================
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    model = body.get("model") or DEFAULT_MODEL
    messages = body.get("messages") or []
    stream = bool(body.get("stream", False))

    if not model:
        raise HTTPException(status_code=400, detail="Missing 'model' (and DEFAULT_MODEL is not set)")
    if not isinstance(messages, list) or len(messages) == 0:
        raise HTTPException(status_code=400, detail="Missing/invalid 'messages'")

    # Map OpenAI -> Ollama chat
    # Keep options minimal (tweak as needed)
    ollama_payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    # Optional OpenAI knobs -> Ollama options
    options = {}
    if "temperature" in body:
        options["temperature"] = body["temperature"]
    if "top_p" in body:
        options["top_p"] = body["top_p"]
    if "max_tokens" in body:
        # Ollama uses num_predict
        options["num_predict"] = body["max_tokens"]

    if options:
        ollama_payload["options"] = options

    if stream:
        # Ollama returns JSON per line. We'll wrap as SSE "data: ..."
        upstream = _req("POST", "/api/chat", json=ollama_payload, stream=True)
        if upstream.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream /api/chat failed: {upstream.status_code} {upstream.text}")

        def sse_gen():
            # Each line from Ollama is a JSON object
            for line in upstream.iter_lines(decode_unicode=True):
                if not line:
                    continue
                # Pass-through as SSE
                yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(sse_gen(), media_type="text/event-stream")

    upstream = _req("POST", "/api/chat", json=ollama_payload)
    if upstream.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Upstream /api/chat failed: {upstream.status_code} {upstream.text}")

    out = upstream.json()
    content = (out.get("message") or {}).get("content") or ""

    # Return OpenAI-ish format
    return JSONResponse(
        {
            "id": "chatcmpl-ollama-local",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        }
    )
