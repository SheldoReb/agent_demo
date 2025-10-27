"""Entrypoint for running the AG2 demo agent inside Docker."""
from __future__ import annotations

import argparse
import asyncio
import base64
from pathlib import Path

from ag2 import AssistantAgent, UserProxyAgent
from ag2.runtime import Runtime

try:  # pragma: no cover - import location differs across ag2 versions
    from ag2.tools.python.local import LocalCommandLineCodeExecutor
except ImportError:  # pragma: no cover - fallback for legacy package layout
    from ag2.tools.python import LocalCommandLineCodeExecutor  # type: ignore

from .tools.markitdown_tool import MarkItDownTool


async def run_demo(prompt: str, attachment: Path | None) -> None:
    runtime = Runtime.from_config("config/runtime.yaml")

    assistant = AssistantAgent(
        name="assistant",
        instructions=(
            "You are an assistant that can execute Python or shell commands using "
            "the configured code executor and convert documents to Markdown using "
            "the markitdown tool. Use the tools when helpful to achieve the user's "
            "goal."
        ),
        tools=[MarkItDownTool()],
        runtime=runtime,
    )

    user = UserProxyAgent(
        name="user",
        runtime=runtime,
        human_input_mode="NEVER",
        code_execution_config={
            "executor": LocalCommandLineCodeExecutor(),
        },
    )

    if attachment is not None:
        data = attachment.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        prompt = (
            f"{prompt}\n\nA supporting document is included as base64 data. "
            "Use markitdown_convert to read it.\n\n" + encoded
        )

    await user.initiate_chat(assistant, message=prompt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AG2 demo agent")
    parser.add_argument("prompt", help="Initial prompt for the agent to solve")
    parser.add_argument(
        "--attachment",
        type=Path,
        help="Optional path to a file that should be converted to Markdown",
    )
    args = parser.parse_args()

    asyncio.run(run_demo(args.prompt, args.attachment))


if __name__ == "__main__":
    main()
