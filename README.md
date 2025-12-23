# Autogen MarkItDown Demo Agent

This repository contains a minimal demonstration of running a [Microsoft Autogen](https://github.com/microsoft/autogen) agent inside a Docker container. The agent is configured to use the Hugging Face text-generation inference router via the OpenAI-compatible endpoint, integrates the [markItDown](https://github.com/microsoft/markitdown) document understanding tool, and exposes timer/stopwatch helpers alongside a local shell executor inspired by Autogen's code-execution notebook examples.

## Features

- **Hugging Face router model** – Uses `openai/gpt-oss-120b` through the Hugging Face router with an `HF_TOKEN` API key.
- **MarkItDown tool** – Exposes a `convert_with_markitdown` tool so the assistant can transform local files into Markdown and plain text.
- **Local command execution** – Enables the assistant to run shell commands inside the container using `LocalCommandLineCodeExecutor` from Autogen's coding utilities.
- **Timer and stopwatch tools** – Registers the timer/stopwatch helpers exactly as demonstrated in the Autogen async function-call documentation.
- **Docker ready** – Includes a Dockerfile that installs dependencies and runs the demo script.

## Prerequisites

- Docker
- A valid Hugging Face API token stored in the environment variable `HF_TOKEN`

## Quick start

```bash
docker build -t autogen-markitdown-demo .
docker run --rm -e HF_TOKEN=$HF_TOKEN autogen-markitdown-demo
```

The container executes `demo.py`, which builds a user proxy agent equipped with the MarkItDown tool, timer/stopwatch helpers, and a local command executor, and then initiates a sample conversation with an assistant agent. The assistant is prompted to summarise the repository's `README.md` using MarkItDown, list the files in the working directory using the local command executor, and exercise the timer/stopwatch tools.

If you would like to verify the setup without contacting the model endpoint, run the included dry-run smoke tests:

```bash
python demo.py --dry-run
```

## Project structure

- `demo.py` – Script that wires together the Autogen agents, registers the MarkItDown/timer/stopwatch tools, and can run either the demo dialogue or offline smoke tests.
- `requirements.txt` – Python dependencies for the demo.
- `Dockerfile` – Container definition for running the agent.
