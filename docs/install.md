# Installation

Bloqade Shuttle is available on pypi registry. Shuttle supports Python 3.10 or later. We recommend using Python 3.10+ for the best experience.

We strongly recommend developing project using [`uv`](https://docs.astral.sh/uv/),
which is the official development environment for Kirin and Bloqade Shuttle. You can install `uv` using the following command:

=== "Linux and macOS"

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```


=== "Windows"

    ```cmd
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## Install package:
```bash
uv add bloqade-shuttle
```

## Development

We use `uv` to manage the development environment, after you install `uv`, you can install the development dependencies using the following command:

```bash
uv sync
```

Our code review requires that you pass the tests and the linting checks. We recommend
you to install `pre-commit` to run the checks before you commit your changes, the command line
tool `pre-commit` has been installed as part of the development dependencies. You can setup
`pre-commit` using the following command:

```bash
pre-commit install
```
