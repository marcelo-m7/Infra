import os
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama-api:11434")

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/models")
def v1_models():
    r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=10)
    r.raise_for_status()
    data = r.json()
    models = data.get("models", [])
    return {
        "object": "list",
        "data": [
            {"id": m["name"], "object": "model", "owned_by": "ollama"}
            for m in models
        ],
    }

@app.post("/v1/chat/completions")
async def v1_chat_completions(req: Request):
    body = await req.json()
    model = body.get("model")
    messages = body.get("messages", [])
    stream = bool(body.get("stream", False))
    temperature = body.get("temperature", 0.2)

    if not model:
        raise HTTPException(status_code=400, detail="Missing 'model'")
    if not messages:
        raise HTTPException(status_code=400, detail="Missing 'messages'")

    # Converte OpenAI -> Ollama
    ollama_payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
        },
    }

    if stream:
        r = requests.post(
            f"{OLLAMA_BASE}/api/chat",
            json=ollama_payload,
            stream=True,
            timeout=600,
        )
        r.raise_for_status()

        # Re-empacota SSE-like em chunks no estilo OpenAI
        def gen():
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    r = requests.post(f"{OLLAMA_BASE}/api/chat", json=ollama_payload, timeout=600)
    r.raise_for_status()
    out = r.json()

    # Converte resposta Ollama -> OpenAI
    content = out.get("message", {}).get("content", "")
    return JSONResponse(
        {
            "id": "chatcmpl-ollama",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "model": model,
        }
    )
