import argparse
import asyncio
import sys

import apple_fm_sdk as fm


def _check_model():
    model = fm.SystemLanguageModel()
    available, reason = model.is_available()
    if not available:
        print(f"Apple Foundation Model is not available: {reason}", file=sys.stderr)
        sys.exit(1)


def _build_options(temperature):
    if temperature is not None:
        return fm.GenerationOptions(temperature=temperature)
    return None


async def _send(session, prompt, *, stream=True, options=None):
    """Send a prompt and print the response, streaming by default."""
    if stream:
        prev = ""
        async for snapshot in session.stream_response(prompt, options=options):
            new = snapshot[len(prev):]
            print(new, end="", flush=True)
            prev = snapshot
        print()
    else:
        response = await session.respond(prompt, options=options)
        print(response)


async def _one_shot(args):
    session = fm.LanguageModelSession(instructions=args.system)
    options = _build_options(args.temperature)
    await _send(session, args.prompt, stream=not args.no_stream, options=options)


async def _interactive(args):
    session = fm.LanguageModelSession(instructions=args.system)
    options = _build_options(args.temperature)
    print("Apple FM interactive chat (Ctrl-D or 'exit' to quit)\n")
    while True:
        try:
            prompt = input("you> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not prompt.strip():
            continue
        if prompt.strip().lower() in ("exit", "quit"):
            break
        print("afm> ", end="", flush=True)
        try:
            await _send(session, prompt, stream=not args.no_stream, options=options)
        except fm.FoundationModelsError as e:
            print(f"\n[error] {e}", file=sys.stderr)


async def _run_chat(args):
    _check_model()
    if args.prompt:
        await _one_shot(args)
    else:
        await _interactive(args)


def _run_serve(args):
    _check_model()
    from afm.server import run_server
    run_server(host=args.host, port=args.port, permissive=args.permissive)


def main():
    parser = argparse.ArgumentParser(
        prog="afm",
        description="Chat with Apple's on-device Foundation Model.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # -- serve subcommand --
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start an OpenAI-compatible HTTP server.",
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1).",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port (default: 8000).",
    )
    serve_parser.add_argument(
        "--permissive", action="store_true",
        help="Use permissive guardrails (less content filtering).",
    )

    # -- chat (default) --
    parser.add_argument(
        "prompt", nargs="?", default=None,
        help="One-shot prompt. Omit to enter interactive chat mode.",
    )
    parser.add_argument(
        "-s", "--system", default=None,
        help="System instructions for the session.",
    )
    parser.add_argument(
        "-t", "--temperature", type=float, default=None,
        help="Sampling temperature (e.g. 0.7).",
    )
    parser.add_argument(
        "--no-stream", action="store_true",
        help="Disable streaming and wait for the full response.",
    )

    args = parser.parse_args()

    if args.command == "serve":
        _run_serve(args)
    else:
        asyncio.run(_run_chat(args))


if __name__ == "__main__":
    main()
