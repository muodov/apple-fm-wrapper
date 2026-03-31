# afm — Apple Foundation Model CLI

Thin CLI wrapper around [apple-fm-sdk](https://github.com/apple/python-apple-fm-sdk) for quick interactive testing of Apple's on-device Foundation Model.

## Requirements

- macOS 26.0+
- Xcode 26.0+
- Python 3.10+
- Apple Intelligence enabled

## Install

```bash
pip install -e .
```

## Usage

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

### Options

```
-s, --system    System instructions for the session
-t, --temperature   Sampling temperature (e.g. 0.7)
--no-stream     Wait for the full response instead of streaming
```

Examples:

```bash
afm -s "You are a privacy expert." "Explain GDPR in one sentence."
afm -t 0.9 "Write a haiku about cookies."
afm --no-stream "List three facts about ducks."
```
