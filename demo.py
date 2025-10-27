"""Demo Autogen agent using MarkItDown and async tool + code execution flows."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from textwrap import shorten

from autogen import AssistantAgent, UserProxyAgent
from autogen.agentchat.executors import LocalCommandLineExecutor
from markitdown import MarkItDown

WORK_DIR = Path(os.environ.get("AGENT_WORKDIR", Path.cwd()))


def convert_with_markitdown(path: str) -> str:
    """Return the Markdown + text summary for ``path`` using MarkItDown."""
    file_path = (WORK_DIR / path).resolve() if not Path(path).is_absolute() else Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    mid = MarkItDown()
    result = mid.convert(file_path)
    return result.text_content


def register_markitdown_tool(user_proxy: UserProxyAgent, assistant: AssistantAgent) -> None:
    """Register the MarkItDown tool with both the user proxy and the assistant."""
    description = (
        "Convert a local document to Markdown/plain text using markItDown. "
        "Provide a relative or absolute file path."
    )

    user_proxy.register_for_execution(
        function_map={"convert_with_markitdown": convert_with_markitdown},
        description_map={"convert_with_markitdown": description},
    )
    assistant.register_for_llm(
        function_map={"convert_with_markitdown": convert_with_markitdown},
        description_map={"convert_with_markitdown": description},
    )


class AutoFeedbackCommandExecutor(LocalCommandLineExecutor):
    """Local executor that emits short feedback messages after each run."""

    def __init__(self, *args, **kwargs):  # type: ignore[override]
        super().__init__(*args, **kwargs)
        self.last_feedback: str | None = None

    def _format_feedback(self, command: str, exit_code: int, output: str) -> str:
        status = "succeeded" if exit_code == 0 else "failed"
        snippet = shorten(output.strip(), width=220, placeholder="...") if output else "(no output)"
        return (
            f"Command `{command}` {status} with exit code {exit_code}.\n"
            f"Output snippet:\n{snippet}"
        )

    async def aexecute(self, command: str, **kwargs):  # type: ignore[override]
        result = await super().aexecute(command, **kwargs)
        feedback = self._format_feedback(command, result.get("exit_code", 0), result.get("content", ""))
        self.last_feedback = feedback
        result.setdefault("metadata", {})["auto_feedback"] = feedback
        return result

    def execute(self, command: str, **kwargs):  # type: ignore[override]
        result = super().execute(command, **kwargs)
        feedback = self._format_feedback(command, result.get("exit_code", 0), result.get("content", ""))
        self.last_feedback = feedback
        result.setdefault("metadata", {})["auto_feedback"] = feedback
        return result


async def build_agents() -> tuple[UserProxyAgent, AssistantAgent]:
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN environment variable must be set.")

    config_list = [
        {
            "model": "openai/gpt-oss-120b",
            "api_key": hf_token,
            "base_url": "https://router.huggingface.co/v1",
        }
    ]

    assistant = AssistantAgent(
        name="assistant",
        system_message=(
            "You are a helpful assistant that uses tools when needed. "
            "Prefer MarkItDown for document understanding and run shell commands "
            "via the local executor when asked."
        ),
        llm_config={
            "config_list": config_list,
            "cache_seed": 42,
        },
    )

    executor = AutoFeedbackCommandExecutor(work_dir=str(WORK_DIR))
    user_proxy = UserProxyAgent(
        name="operator",
        human_input_mode="NEVER",
        description="Executes commands and orchestrates tools for the assistant.",
        code_execution_config={"executor": executor},
    )

    register_markitdown_tool(user_proxy, assistant)

    @user_proxy.register_for_execution(name="relay_code_feedback")
    def _relay_feedback() -> str:
        """Return a concise summary of the previous shell command."""

        return executor.last_feedback or "No feedback available."

    assistant.register_for_llm(
        name="relay_code_feedback",
        function=_relay_feedback,
        description=(
            "Summarise the result of the most recent command executed by the "
            "local shell executor."
        ),
    )

    return user_proxy, assistant


async def run_demo() -> None:
    user_proxy, assistant = await build_agents()

    instructions = (
        "First, call the MarkItDown tool to summarise README.md. Then run 'ls' using the "
        "code executor. After each command, use the relay_code_feedback tool to review the "
        "execution summary."
    )

    await user_proxy.a_initiate_chat(
        assistant,
        message=instructions,
    )


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
