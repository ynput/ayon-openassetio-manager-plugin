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

To get the correct formatted paths, you need to have AYON site id - unique identifier of your local site that can be determined from hostname
and platform. Server can determine your site id from that and use it for all subsequent requests. Site id is stored on server once
you first run AYON launcher and connect it to the server. In other words, you need to run AYON launcher at least once to get correct results.
This needs to be handled later on more gracefully.

### Tech Preview: Setup for Nuke 15

Nuke 15 comes with OpenAssetIO support out of the box in a state of tech-preview. To use it, you need to
set `OPENASSETIO_PLUGIN_PATH` environment variable to the location of this repository. You also need to add at least
`requests` module to your Python environment - you can do that by running `./tools/manage.ps1 create-env` on Windows
and then `$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)/.venv/Lib/site-packages"` in PowerShell. Set your `AYON_SERVER_URL` and `AYON_API_KEY`
and `OPENASSETIO_DEFAULT_CONFIG` like `$env:OPENASSETIO_DEFAULT_CONFIG="$env:OPENASSETIO_DEFAULT_CONFIG;$(pwd)/pyproject.toml`.
Then you can run Nuke and use OpenAssetIO:

```powershell
$env:OPENASSETIO_PLUGIN_PATH=$(pwd)
$env:OPENASSETIO_DEFAULT_CONFIG="$(pwd)/pyproject.toml"
$env:AYON_SERVER_URL="https://your.ayon.instance"
$env:AYON_API_KEY="your-api-key"
$env:PYTHONPATH="$($env:PYTHONPATH);$(pwd)/.venv/Lib/site-packages"
& 'C:\Program Files\Nuke15.0v1\Nuke15.0.exe'
```

More information about OpenAssetIO in Nuke can be found in [Nuke documentation](https://learn.foundry.com/nuke/developers/150/pythondevguide/openassetio.html).

## Development

To run tests, you need to configure your AYON server in `tests/conftest.py` file. Set `AYON_SERVER_URL` and `AYON_API_KEY` at the top of the file.

### TODO:

- [ ] Handle site id determination more gracefully
- [ ] Better error handling
- [ ] Better logging
- [ ] More tests
- [ ] Implement missing methods
