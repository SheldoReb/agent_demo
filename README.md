# Autogen MarkItDown Demo Agent

This repository contains a minimal demonstration of running a [Microsoft Autogen](https://github.com/microsoft/autogen) agent inside a Docker container. The agent is configured to use the Hugging Face text-generation inference router via the OpenAI-compatible endpoint, integrates the [markItDown](https://github.com/microsoft/markitdown) document understanding tool, and asynchronously executes shell commands through an auto-feedback enabled `LocalCommandLineExecutor`.

## Features

- **Hugging Face router model** – Uses `openai/gpt-oss-120b` through the Hugging Face router with an `HF_TOKEN` API key.
- **MarkItDown tool** – Exposes a `convert_with_markitdown` tool so the assistant can transform local files into Markdown and plain text.
- **Local command execution** – Enables the assistant to run shell commands inside the container using an auto-feedback `LocalCommandLineExecutor` implementation inspired by the Autogen code-execution notebook.
- **Async tool calling** – Uses Autogen's async `a_initiate_chat` flow, mirroring the function-call example notebook, so tool invocations and code execution integrate cleanly.
- **Docker ready** – Includes a Dockerfile that installs dependencies and runs the demo script.

## Prerequisites

- Docker
- A valid Hugging Face API token stored in the environment variable `HF_TOKEN`

## Quick start

```bash
docker build -t autogen-markitdown-demo .
docker run --rm -e HF_TOKEN=$HF_TOKEN autogen-markitdown-demo
```

The container executes `demo.py`, which builds a user proxy agent equipped with the MarkItDown tool and a local command executor, and then initiates a sample conversation with an assistant agent. The assistant is prompted to summarise the repository's `README.md` using MarkItDown and list the files in the working directory using the local command executor.

## Project structure

- `demo.py` – Script that wires together the Autogen agents, registers the MarkItDown and feedback tools, and runs an async sample dialogue.
- `requirements.txt` – Python dependencies for the demo.
- `Dockerfile` – Container definition for running the agent.
