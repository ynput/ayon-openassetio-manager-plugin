$script_dir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$root = (Get-Item $script_dir).parent.FullName

if (-not (Test-Path 'env:POETRY_HOME')) {
    $env:POETRY_HOME = "$root\.poetry"
}

function Install-Poetry() {
    Write-Host ">>> Installing Poetry ... "
    $python = "python"
    if (Get-Command "pyenv" -ErrorAction SilentlyContinue) {
        if (-not (Test-Path -PathType Leaf -Path "$($openpype_root)\.python-version")) {
            $result = & pyenv global
            if ($result -eq "no global version configured") {
                Write-Host "!!! Using pyenv but having no local or global version of Python set."
                Exit-WithCode 1
            }
        }
        $python = & pyenv which python

    }

    $env:POETRY_HOME="$root\.poetry"
    (Invoke-WebRequest -Uri https://install.python-poetry.org/ -UseBasicParsing).Content | & $($python) -
}

if (-not (Test-Path -PathType Container -Path "$($env:POETRY_HOME)\bin")) {
    Write-Host "Poetry not found, installing locally ..."
    Install-Poetry
}

& "$env:POETRY_HOME\bin\poetry" install --no-root --ansi