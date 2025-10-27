# Agent Demo

This repository contains a minimal example of an [AG2](https://github.com/ag2ai/ag2) agent that can execute Python or shell code and convert files to Markdown using [MarkItDown](https://github.com/microsoft/markitdown). The demo is containerised with Docker so you can run it without installing the dependencies locally.

## Features

- **AG2 agent** configured via `config/runtime.yaml`.
- **Local command execution** powered by AG2's `LocalCommandLineCodeExecutor`, enabling both Python and Bash snippets.
- **MarkItDown tool** to convert arbitrary files or binary data to Markdown.
- **Docker image** ready to run the agent with your Hugging Face token.

## Prerequisites

- Docker and Docker Compose
- A Hugging Face Inference token stored in the `HF_TOKEN` environment variable (grants access to [router.huggingface.co](https://huggingface.co/inference-api))

## Running the agent

Build the image and start the container with a one-off prompt:

```bash
docker compose run --rm \
  -e HF_TOKEN="$HF_TOKEN" \
  agent "Summarise the attachment and write Python that counts the words."
```

To include a document, mount it into the container and pass the path via `--attachment`:

```bash
docker compose run --rm \
  -e HF_TOKEN="$HF_TOKEN" \
  -v "$PWD/samples:/workspace/data" \
  agent "Summarise the attachment" --attachment /workspace/data/report.docx
```

The agent responds in the terminal using the selected LLM. When the agent needs to work with attachments, it will call `markitdown_convert` to convert them into Markdown before reasoning about their contents.

## Development

Install dependencies locally (requires network access to PyPI):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You can then invoke the agent directly (make sure `HF_TOKEN` is exported so the runtime can authenticate with Hugging Face):

```bash
python -m agent_demo.main "List three features of AG2"
```

Use the `--attachment` option to convert files through MarkItDown. The file will be supplied to the agent as base64 data, and it should call `markitdown_convert` with the `data` argument to obtain the Markdown contents:

```bash
python -m agent_demo.main "Review the attached resume" --attachment ./samples/resume.pdf
```

## Configuration

Runtime settings for AG2 are stored in `config/runtime.yaml`. Update the model name or add provider-specific options as needed. Environment variables referenced in the file (like `HF_TOKEN`) are expanded automatically when the container starts.

## Testing inside Docker

To run the containerised agent interactively:

```bash
docker compose build
docker compose run --rm agent "Write Python code to compute fibonacci numbers"
```

You can stop the container at any time with `Ctrl+C`.
