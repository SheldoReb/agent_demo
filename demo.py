"""Demo Autogen agent using MarkItDown and a local command executor."""
from __future__ import annotations

import os
from pathlib import Path

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

    try:
        user_proxy.register_for_execution(
            function_map={"convert_with_markitdown": convert_with_markitdown},
            description_map={"convert_with_markitdown": description},
        )
        assistant.register_for_llm(
            function_map={"convert_with_markitdown": convert_with_markitdown},
            description_map={"convert_with_markitdown": description},
        )
    except TypeError:
        user_proxy.register_for_execution(
            name="convert_with_markitdown",
            function=convert_with_markitdown,
            description=description,
        )
        assistant.register_for_llm(
            name="convert_with_markitdown",
            function=convert_with_markitdown,
            description=description,
        )


def build_agents() -> tuple[UserProxyAgent, AssistantAgent]:
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

    executor = LocalCommandLineExecutor(work_dir=str(WORK_DIR))
    user_proxy = UserProxyAgent(
        name="operator",
        human_input_mode="NEVER",
        description="Executes commands and orchestrates tools for the assistant.",
        code_execution_config={"executor": executor},
    )

    register_markitdown_tool(user_proxy, assistant)

    return user_proxy, assistant


def run_demo() -> None:
    user_proxy, assistant = build_agents()

    instructions = (
        "Use the MarkItDown tool to summarise README.md, then run 'ls' using the "
        "code executor to list generated files."
    )

    user_proxy.initiate_chat(
        assistant,
        message=instructions,
    )


if __name__ == "__main__":
    run_demo()
