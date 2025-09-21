# ActCLI: Gemini Code Assistant Context

This document provides context for the Gemini code assistant to understand the ActCLI project.

## Project Overview

ActCLI is a terminal-native toolkit for actuarial workflows with a multi-model "roundtable" chat featuring a VSCode-style interface. It is a Python project built with Typer for the CLI and prompt_toolkit for the TUI.

The core functionality is the multi-model chat, which allows users to send a prompt to multiple language models concurrently and view the results in a unified interface. The chat can be run in interactive mode or with a single prompt.

The project also includes features for managing models, authenticating with API providers, and checking the environment configuration.

## Building and Running

To build and run the project, follow these steps:

1.  Create a virtual environment:
    ```bash
    python -m venv .venv && source .venv/bin/activate
    ```
2.  Install the dependencies:
    ```bash
    pip install -e .
    ```
3.  Run the health check:
    ```bash
    actcli doctor
    ```
4.  Start the interactive chat:
    ```bash
    actcli
    ```
5.  Run a one-shot chat with a prompt:
    ```bash
    actcli chat --prompt "Compare reserving strategies" --multi llama3,claude,gpt --rounds 2
    ```

## Development Conventions

*   **Code Style:** The project uses `ruff` for linting and formatting.
*   **Testing:** The project uses `pytest` for testing.
*   **Commits:** Commit messages should follow the Conventional Commits specification.
*   **Branching:** Feature branches should be created from the `main` branch.
*   **Pull Requests:** Pull requests should be created to merge feature branches into the `main` branch.
