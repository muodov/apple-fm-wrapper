import json
import sys
import time
import uuid

from aiohttp import web

import apple_fm_sdk as fm

_request_count = 0


def _normalize_schema(obj):
    """Ensure every object node has x-order (required by Apple FM) and strip other x-* keys."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.startswith("x-") and k != "x-order":
                continue
            out[k] = _normalize_schema(v)
        if out.get("type") == "object" and "properties" in out and "x-order" not in out:
            out["x-order"] = list(out["properties"].keys())
        return out
    if isinstance(obj, list):
        return [_normalize_schema(item) for item in obj]
    return obj


def _log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


async def handle_chat_completions(request):
    global _request_count
    _request_count += 1
    req_id = _request_count
    t0 = time.monotonic()

    body = await request.json()

    messages = body.get("messages", [])
    temperature = body.get("temperature")
    response_format = body.get("response_format")

    system_prompt = None
    user_prompt = ""
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            user_prompt = msg.get("content") or ""

    if not user_prompt.strip():
        user_prompt = "(empty)"

    options = None
    if temperature is not None:
        options = fm.GenerationOptions(temperature=temperature)

    model = fm.SystemLanguageModel(
        guardrails=request.app["guardrails"],
    )
    session = fm.LanguageModelSession(instructions=system_prompt, model=model)

    json_schema = None
    if response_format and response_format.get("type") == "json_schema":
        schema_wrapper = response_format.get("json_schema", {})
        raw_schema = schema_wrapper.get("schema")
        if raw_schema:
            json_schema = _normalize_schema(raw_schema)
            if "title" not in json_schema:
                json_schema["title"] = schema_wrapper.get("name", "Response")

    schema_name = json_schema.get("title") if json_schema else None
    sys_text = (system_prompt or '(none)').replace('\n', ' ')
    sys_preview = sys_text[:60] + ('...' if len(sys_text) > 60 else '')
    prompt_text = user_prompt.replace('\n', ' ')
    prompt_preview = prompt_text[:80] + ('...' if len(prompt_text) > 80 else '')
    _log(f"#{req_id} system=\"{sys_preview}\" prompt={len(user_prompt)} chars schema={schema_name} temp={temperature} \"{prompt_preview}\"")

    try:
        if json_schema:
            result = await session.respond(user_prompt, json_schema=json_schema, options=options)
            content = result.to_json()
        else:
            content = await session.respond(user_prompt, options=options)
    except fm.FoundationModelsError as e:
        elapsed = time.monotonic() - t0
        _log(f"#{req_id} ERROR {elapsed:.1f}s {e}")
        return web.json_response(
            {"error": {"message": str(e), "type": "server_error"}},
            status=500,
        )

    elapsed = time.monotonic() - t0
    content_preview = content[:100].replace('\n', ' ')
    _log(f"#{req_id} OK {elapsed:.1f}s \"{content_preview}\"")

    return web.json_response({
        "id": f"afm-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "apple-fm-on-device",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "finish_reason": "stop",
        }],
    })


def create_app(*, permissive=False):
    app = web.Application()
    app["guardrails"] = (
        fm.SystemLanguageModelGuardrails.PERMISSIVE_CONTENT_TRANSFORMATIONS
        if permissive
        else fm.SystemLanguageModelGuardrails.DEFAULT
    )
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    return app


def run_server(host="127.0.0.1", port=8000, permissive=False):
    model = fm.SystemLanguageModel()
    available, reason = model.is_available()
    if not available:
        raise RuntimeError(f"Apple Foundation Model is not available: {reason}")

    guardrail_label = "permissive" if permissive else "default"
    print(f"Apple FM server listening on http://{host}:{port}/v1/chat/completions (guardrails: {guardrail_label})")
    app = create_app(permissive=permissive)
    web.run_app(app, host=host, port=port, print=None)