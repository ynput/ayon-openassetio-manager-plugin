# AYON OpenAssetIO Manager Plugin

This is implementing manager interface for
[OpenAssetIO](https://github.com/OpenAssetIO/OpenAssetIO). With it, any
OpenAssetIO enabled host (DCC) can be used to load data from
[AYON](https://ayon.ynput.io/). This is a work in progress and it depends on
OpenAssetIO Traits to be supported by the host.

## Installation

There are few options for installation, depending on the intended use and
existing Python environment.

## pip

Assuming you are within the Python environment of your target host application,
then

```shell
pip install .[ui]
```

will install the plugin and its dependencies. The `[ui]` part is optional, it
will install additional dependencies to support UI delegation.

Often, you may not wish or be able to install the plugin directly into the host
application environment. An alternative is to install to a target directory

```shell
pip install .[ui] --target /path/to/target/directory
```

then ensure you add the target directory to the `PYTHONPATH` environment
variable when starting the host application. As long as the host application
loads the OpenAssetIO Python plugin system and supports Python importlib
entrypoint plugins, then the AYON plugin will be automatically discovered.

## PowerShell

To manage your installation, use `./tools/manage.ps1` on Windows. It accepts
commands as arguments, run it without arguments to see the list of available
commands.

* `create-env` - creates virtual environment for development using [Poetry](https://python-poetry.org/)
* `generate-traits` - generates Python traits using openassetio-tratsgen from
  `traits.yml` file and puts them into `ayon_traits` module.
* `run-tests` - runs test

## Building

You can build the plugin as Python wheel using Poetry. Run `poetry build` to
build the wheel. It will be located in `dist` directory.

## Usage

To use this plugin, ensure the host Python environment contains all dependencies
(see `pyproject.toml`) and that the plugin package is on `PYTHONPATH`. This may
be a bespoke setup to support a particular host application (e.g. configured
by Rez) or configured generically according to the Installation section above.

If the host application does not support Python importlib entrypoint plugins,
then make sure you point the `OPENASSETIO_PLUGIN_PATH` environment variable to
the directory where this plugin is located, and `OPENASSETIO_UI_PLUGIN_PATH` to
the `ui` subdirectory (if also wishing to use the UI delegate plugin).

To tell manager how to connect to AYON, set environment variable
`AYON_SERVER_URL` to the server address; `AYON_API_KEY` to the API key; and
`AYON_BUNDLE_NAME` to the active AYON package bundle. If using an application
launched via the AYON launcher, these environment variables will be set
automatically. Alternatively, these can be configured in the OpenAssetIO config
file.

The config file must (usually) be specified by the `OPENASSETIO_DEFAULT_CONFIG`
environment variable to tell the host application which OpenAssetIO plugin(s)
it should use. The environment variable should point to a TOML file with the 
following content:

```toml
[manager]
# This must match exactly the identifier of the plugin.
identifier = "io.ynput.ayon.openassetio.manager"

[settings]
# Required settings for the AYON manager plugin. 
# Each may be set as an environment variable instead.
# AYON server URL.
AYON_SERVER_URL = "https://openassetio.ayon.example"
# AYON API key for authentication.
AYON_API_KEY = "YOURAPIKEYGOESHERE"
# AYON bundle name. Required to locate ayon_core in local cache.
AYON_BUNDLE_NAME = "2025.06.0-2025-06-20-01"
```

Additionally, the plugin requires the `ayon_core` Python package to be
available, which means that the AYON launcher should be installed and run at
least once to download and cache `ayon_core` locally.

To get the correct formatted paths, you need to have AYON site id - unique
identifier of your local site that can be determined from hostname and platform.
Server can determine your site id from that and use it for all subsequent
requests. Site id is stored on server once you first run AYON launcher and
connect it to the server.

In other words, you need to run AYON launcher at least once to get
correct results. This needs to be handled later on more gracefully.

### Tech Preview: Setup for Nuke 15+

Nuke 15+ comes with OpenAssetIO support out of the box (in a state of
tech-preview for Nuke 15). To use it, you need the appropriate dependencies in
the Nuke Python environment - you can do that by running 
`./tools/manage.ps1 create-env` on Windows and then
`$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)/.venv/Lib/site-packages"` in
PowerShell. Set your `AYON_SERVER_URL` and `AYON_API_KEY` and
`OPENASSETIO_DEFAULT_CONFIG` like
`$env:OPENASSETIO_DEFAULT_CONFIG="$env:OPENASSETIO_DEFAULT_CONFIG;$(pwd)/pyproject.toml`.
Then you can run Nuke and use OpenAssetIO:

```powershell
$env:OPENASSETIO_DEFAULT_CONFIG="$(pwd)/pyproject.toml"
$env:AYON_SERVER_URL="https://your.ayon.instance"
$env:AYON_API_KEY="your-api-key"
$env:PYTHONPATH="$($env:PYTHONPATH);$(pwd)/.venv/Lib/site-packages"
& 'C:\Program Files\Nuke15.0v1\Nuke15.0.exe'
```

More information about OpenAssetIO in Nuke can be found in [Nuke documentation](https://learn.foundry.com/nuke/developers/150/pythondevguide/openassetio.html).

## Development

To run tests, you need to configure your AYON server in `tests/conftest.py`
file. Set `AYON_SERVER_URL` and `AYON_API_KEY` at the top of the file.
Alternatively, set them as environment variables.

### TODO:

- [ ] Handle site id determination more gracefully
- [ ] Better error handling
- [ ] Better logging
- [ ] More tests
- [ ] Implement missing methods
