# afm — Apple Foundation Model CLI

Thin CLI wrapper around [apple-fm-sdk](https://github.com/apple/python-apple-fm-sdk) for quick interactive testing of Apple's on-device Foundation Model (~3B params).

## Requirements

- macOS 26.0+
- Xcode 26.0+
- Python 3.10+
- Apple Intelligence enabled

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Chat

### One-shot prompt

```bash
afm "What is a cookie consent popup?"
```

### Interactive chat

```bash
afm
# you> Hello!
# afm> Hi there! How can I help you?
# you> exit
```

### Chat options

```
-s, --system        System instructions for the session
-t, --temperature   Sampling temperature (e.g. 0.7)
--no-stream         Wait for the full response instead of streaming
```

```bash
afm -s "You are a privacy expert." "Explain GDPR in one sentence."
afm -t 0.9 "Write a haiku about cookies."
```

## OpenAI-compatible server

Exposes the on-device model as a local HTTP endpoint that speaks the OpenAI chat completions protocol. Any tool that uses the OpenAI API can target it by changing the base URL.

```bash
afm serve --port 8000
```

### Server options

```
--host HOST       Bind address (default: 127.0.0.1)
--port PORT       Port (default: 8000)
--permissive      Use permissive guardrails (less content filtering)
```

### Usage with OpenAI clients

Point any OpenAI-compatible client at `http://localhost:8000/v1`:

```bash
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

```javascript
const openai = new OpenAI({
    baseURL: 'http://localhost:8000/v1',
    apiKey: 'unused',
});
const result = await openai.chat.completions.create({
    model: 'anything',
    messages: [{ role: 'user', content: 'Hello' }],
});
```

Structured output (`response_format` with JSON schema) is supported — the server translates it to Apple FM's guided generation.

### Notes

- The `model` field is ignored (there is only one on-device model).
- Requests are processed sequentially — set parallelism to 1 when running batch jobs.
- Streaming is not implemented on the server; use the CLI for streaming.
