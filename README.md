# AYON OpenAssetIO Manager Plugin

This is implementing manager interface for [OpenAssetIO](https://github.com/OpenAssetIO/OpenAssetIO). With it,
any OpenAssetIO enabled host (DCC) can be used to load data from [AYON](https://ayon.ynput.io/). This is a work in progress and it depends on
OpenAssetIO Traits to be supported by the host.

## Installation

To manage your installation, use `./tools/manage.ps1` on Windows and `./tools/manage.sh` on Linux and macOS. It accepts
commands as arguments, run it without arguments to see the list of available commands.

* `create-env` - creates virtual environment for development using [Poetry](https://python-poetry.org/)
* `generate-traits` - generates Python traits using openassetio-tratsgen from `traits.yml` file and puts them into `ayon_traits` module.
* `run-tests` - runs test

## Usage

To use this plugin, make sure you point `OPENASSETIO_PLUGIN_PATH` environment variable to the directory where this plugin is located.
Also make sure plugin Python environment is available inside the host. So far it needs only `requests` package and `openassetio` itself.
To tell manager how to connect to AYON, set `AYON_SERVER_URL` environment variable to the server address and `AYON_API_KEY` to the API key.

## Development

To run tests, you need to configure your AYON server in `tests/conftest.py` file. Set `AYON_SERVER_URL` and `AYON_API_KEY` at the top of the file.
