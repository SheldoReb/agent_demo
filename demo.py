"""Autogen demo featuring MarkItDown, timers, and shell execution inside Docker."""
from __future__ import annotations

import argparse
import asyncio
import os
import time
from pathlib import Path
from typing import Annotated, Any

import autogen
from autogen.coding import LocalCommandLineCodeExecutor
from markitdown import MarkItDown

PROJECT_ROOT = Path.cwd().resolve()
WORK_DIR = Path(os.environ.get("AGENT_WORKDIR", PROJECT_ROOT / "coding")).resolve()


def _ensure_work_dir() -> None:
    """Create the working directory used by the code executor."""

    WORK_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_config_list(allow_mock: bool = False) -> list[dict[str, Any]]:
    """Return the LLM configuration list, falling back to HF router if needed."""

    try:
        config_list = autogen.config_list_from_json(
            "OAI_CONFIG_LIST",
            filter_dict={"tags": ["gpt-4o"]},
        )
        if config_list:
            return config_list
    except (FileNotFoundError, ValueError):
        pass

    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        return [
            {
                "model": "openai/gpt-oss-120b",
                "api_key": hf_token,
                "base_url": "https://router.huggingface.co/v1",
            }
        ]

    if allow_mock:
        return [
            {
                "model": "openai/gpt-oss-120b",
                "api_key": "DUMMY",  # never used without a real chat
                "base_url": "https://router.huggingface.co/v1",
            }
        ]

    raise RuntimeError(
        "No LLM configuration found. Set HF_TOKEN or provide an OAI_CONFIG_LIST file."
    )


async def _timer_impl(num_seconds: str) -> str:
    """Simple async timer used by the registered timer tool."""

    seconds = int(num_seconds)
    for _ in range(seconds):
        await asyncio.sleep(1)
    return "Timer is done!"


def _stopwatch_impl(num_seconds: str) -> str:
    """Simple blocking stopwatch used by the registered stopwatch tool."""

    seconds = int(num_seconds)
    for _ in range(seconds):
        time.sleep(1)
    return "Stopwatch is done!"


def _markitdown_impl(path: str) -> str:
    """Convert the target file to Markdown using MarkItDown."""

    candidate = Path(path)
    file_path = candidate if candidate.is_absolute() else PROJECT_ROOT.joinpath(candidate).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    mid = MarkItDown()
    result = mid.convert(file_path)
    return result.text_content


def build_agents(*, allow_mock_llm: bool = False) -> tuple[autogen.UserProxyAgent, autogen.AssistantAgent, LocalCommandLineCodeExecutor]:
    """Create the user proxy and assistant agents and register demo tools."""

    _ensure_work_dir()

    config_list = _resolve_config_list(allow_mock=allow_mock_llm)
    llm_config = {"config_list": config_list}

    coder = autogen.AssistantAgent(
        name="chatbot",
        system_message=(
            "For coding tasks, only use the functions you have been provided with. "
            "You have a stopwatch and a timer, these tools can and should be used in parallel. "
            "Reply TERMINATE when the task is done."
        ),
        llm_config=llm_config,
    )

    executor = LocalCommandLineCodeExecutor(work_dir=str(WORK_DIR))
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        system_message="A proxy for the user for executing code.",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config={"executor": executor},
    )

    @user_proxy.register_for_execution()
    @coder.register_for_llm(description="create a timer for N seconds")
    async def timer(num_seconds: Annotated[str, "Number of seconds in the timer."]) -> str:  # noqa: D401
        """Timer tool exposed to the assistant."""

        return await _timer_impl(num_seconds)

    def stopwatch(num_seconds: Annotated[str, "Number of seconds in the stopwatch."]) -> str:
        """Stopwatch tool exposed to the assistant."""

        return _stopwatch_impl(num_seconds)

    autogen.agentchat.register_function(
        stopwatch,
        caller=coder,
        executor=user_proxy,
        description="create a stopwatch for N seconds",
    )

    @user_proxy.register_for_execution()
    @coder.register_for_llm(description="Convert a local file to Markdown using MarkItDown.")
    def convert_with_markitdown(path: Annotated[str, "Relative or absolute path to the file."]) -> str:  # noqa: D401
        """Expose MarkItDown conversions as an Autogen tool."""

        return _markitdown_impl(path)

    return user_proxy, coder, executor


def _build_summary_prompt() -> str:
    """Create the default conversation prompt."""

    return (
        "Summarise README.md with the MarkItDown tool, then run `ls` in the workspace using the code executor. "
        "After that, start a 2 second timer and report when both the timer and stopwatch complete."
    )


def run_demo_chat(user_proxy: autogen.UserProxyAgent, assistant: autogen.AssistantAgent, *, message: str | None = None) -> None:
    """Kick off the Autogen chat loop with the supplied message."""

    user_proxy.initiate_chat(
        assistant,
        message=message or _build_summary_prompt(),
        summary_method="reflection_with_llm",
    )


def run_smoke_tests(executor: LocalCommandLineCodeExecutor) -> None:
    """Execute lightweight checks that do not hit the network."""

    print("[dry-run] Executing LocalCommandLineCodeExecutor smoke test...")
    result = executor.execute("echo Autogen demo ready")
    exit_code = result.get("exit_code", 1)
    if exit_code != 0:
        raise RuntimeError(f"Smoke test command failed: {result}")

    print("[dry-run] Rendering README.md with MarkItDown...")
    preview = _markitdown_impl("README.md")
    if "Autogen" not in preview:
        raise RuntimeError("Unexpected MarkItDown output; README summary missing keyword 'Autogen'.")

    print("[dry-run] Timer and stopwatch sanity checks...")
    asyncio.run(_timer_impl("0"))
    _stopwatch_impl("0")
    print("[dry-run] All smoke tests passed.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Run the Autogen MarkItDown demo.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run offline smoke tests instead of initiating an Autogen chat.",
    )
    parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Override the default task description sent to the assistant.",
    )
    return parser.parse_args()


def main() -> None:
    """Entrypoint for CLI usage."""

    args = parse_args()
    allow_mock = args.dry_run
    user_proxy, assistant, executor = build_agents(allow_mock_llm=allow_mock)

    if args.dry_run:
        run_smoke_tests(executor)
        return

    run_demo_chat(user_proxy, assistant, message=args.message)


if __name__ == "__main__":
    main()
