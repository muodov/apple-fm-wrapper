import argparse
import asyncio
import sys

import apple_fm_sdk as fm


def parse_args():
    parser = argparse.ArgumentParser(
        prog="afm",
        description="Chat with Apple's on-device Foundation Model.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="One-shot prompt. Omit to enter interactive chat mode.",
    )
    parser.add_argument(
        "-s", "--system",
        default=None,
        help="System instructions for the session.",
    )
    parser.add_argument(
        "-t", "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (e.g. 0.7).",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming and wait for the full response.",
    )
    return parser.parse_args()


def _build_options(args):
    if args.temperature is not None:
        return fm.GenerationOptions(temperature=args.temperature)
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
    options = _build_options(args)
    await _send(session, args.prompt, stream=not args.no_stream, options=options)


async def _interactive(args):
    session = fm.LanguageModelSession(instructions=args.system)
    options = _build_options(args)
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


async def _run():
    args = parse_args()

    model = fm.SystemLanguageModel()
    available, reason = model.is_available()
    if not available:
        print(f"Apple Foundation Model is not available: {reason}", file=sys.stderr)
        sys.exit(1)

    if args.prompt:
        await _one_shot(args)
    else:
        await _interactive(args)


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
