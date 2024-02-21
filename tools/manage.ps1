<#
.SYNOPSIS
  Helper script create virtual environment using Poetry.

.DESCRIPTION
  This script will detect Python installation, create venv with Poetry
  and install all necessary packages from `poetry.lock` or `pyproject.toml`
  needed by AYON OpenAssetIO Manager Plugin.

.EXAMPLE

PS> .\manage.ps1

.EXAMPLE

Print verbose information from Poetry:
PS> .\manage.ps1 create-env --verbose

#>

$script_dir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$repo_root = (Get-Item $script_dir).parent.FullName

Write-Host "Script directory: $script_dir"
Write-Host "Repo: $repo_root"

if (-not (Test-Path 'env:POETRY_HOME')) {
    $env:POETRY_HOME = "$root\.poetry"
}

& git submodule update --init --recursive
# Install PSWriteColor to support colorized output to terminal
$env:PSModulePath = $env:PSModulePath + ";$($repo_root)\tools\modules\powershell"

$FunctionName=$ARGS[0]
$arguments=@()
if ($ARGS.Length -gt 1) {
    $arguments = $ARGS[1..($ARGS.Length - 1)]
}

$art = @"

                    ▄██▄
         ▄███▄ ▀██▄ ▀██▀ ▄██▀ ▄██▀▀▀██▄    ▀███▄      █▄
        ▄▄ ▀██▄  ▀██▄  ▄██▀ ██▀      ▀██▄  ▄  ▀██▄    ███
       ▄██▀  ██▄   ▀ ▄▄ ▀  ██         ▄██  ███  ▀██▄  ███
      ▄██▀    ▀██▄   ██    ▀██▄      ▄██▀  ███    ▀██ ▀█▀
     ▄██▀      ▀██▄  ▀█      ▀██▄▄▄▄██▀    █▀      ▀██▄

     ·  · - =[ by YNPUT ]:[ http://ayon.ynput.io ]= - ·  ·

"@

function Get-AsciiArt() {
    Write-Host $art -ForegroundColor DarkGreen
}

function Exit-WithCode($exitcode) {
   # Only exit this host process if it's a child of another PowerShell parent process...
   $parentPID = (Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$PID" | Select-Object -Property ParentProcessId).ParentProcessId
   $parentProcName = (Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$parentPID" | Select-Object -Property Name).Name
   if ('powershell.exe' -eq $parentProcName) { $host.SetShouldExit($exitcode) }

   exit $exitcode
}

function Install-Poetry() {
    Write-Color -Text ">>> ", "Installing Poetry ... " -Color Green, Gray
    $python = "python"
    if (Get-Command "pyenv" -ErrorAction SilentlyContinue) {
        if (-not (Test-Path -PathType Leaf -Path "$($repo_root)\.python-version")) {
            $result = & pyenv global
            if ($result -eq "no global version configured") {
                Write-Color -Text "!!! ", "Using pyenv but having no local or global version of Python set." -Color Red, Yellow
                Exit-WithCode 1
            }
        }
        $python = & pyenv which python

    }

    $env:POETRY_HOME="$repo_root\.poetry"
    (Invoke-WebRequest -Uri https://install.python-poetry.org/ -UseBasicParsing).Content | & $($python) -
}

function Show-Usage() {
    $usage = @'
    AYON OpenAsset Manager Plugin build tool

    Usage: ./manage.ps1 [command]

    Available commands:
            create-env                    Install Poetry and update venv by lock file
            generate-traits               Generate Python Traits from traits.yml
            run-tests                     Run tests

'@

    Get-AsciiArt
    Write-Host $usage -ForegroundColor Gray
}

function Initialize-Environment {
    Write-Color -Text ">>> ", "Reading Poetry ... " -Color Green, Gray -NoNewline
    if (-not (Test-Path -PathType Container -Path "$($env:POETRY_HOME)\bin")) {
        Write-Color -Text "NOT FOUND" -Color Yellow
        Install-Poetry
        Write-Color -Text "INSTALLED" -Color Cyan
    } else {
        Write-Color -Text "OK" -Color Green
    }

    if (-not (Test-Path -PathType Leaf -Path "$($repo_root)\poetry.lock")) {
        Write-Color -Text ">>> ", "Installing virtual environment and creating lock." -Color Green, Gray
    } else {
        Write-Color -Text ">>> ", "Installing virtual environment from lock." -Color Green, Gray
    }
    $startTime = [int][double]::Parse((Get-Date -UFormat %s))
    & "$env:POETRY_HOME\bin\poetry" config virtualenvs.in-project true --local
    & "$env:POETRY_HOME\bin\poetry" config virtualenvs.create true --local
    & "$env:POETRY_HOME\bin\poetry" install --no-root $poetry_verbosity --ansi
    if ($LASTEXITCODE -ne 0) {
        Write-Color -Text "!!! ", "Poetry command failed." -Color Red, Yellow
        Exit-WithCode 1
    }

    $endTime = [int][double]::Parse((Get-Date -UFormat %s))
    $duration = $endTime - $startTime
    Write-Color -Text ">>> ", "Virtual environment created in ", $duration, " secs." -Color Green, White, Cyan, White
}

function New-TemporaryDirectory {
    $parent = [System.IO.Path]::GetTempPath()
    [string] $name = [System.Guid]::NewGuid()
    New-Item -ItemType Directory -Path (Join-Path $parent $name)
}

function Initialize-Traits {
    $temp_traits = New-TemporaryDirectory
    Write-Color ">>> ", "Generating traits ..." -Color Green, Gray
    Write-Color ">>> ", "Temporary directory: ", $temp_traits -Color Green, Gray, Cyan

    & "$env:POETRY_HOME\bin\poetry.exe" run openassetio-traitgen -o $temp_traits -g python -v "$($repo_root)\traits.yml"
    Write-Color ">>> ", "Moving traits to repository ..." -Color Green, Gray
    Move-Item -Path $temp_traits\Ayon\traits\* -Destination "$($repo_root)\AyonOpenAssetIOManager\ayon_traits" -Force
    Write-Color -Text ">>> ", "Traits generated." -Color Green, White
}

function Invoke-Tests {
    Write-Color -Text ">>> ", "Running tests ..." -Color Green, Gray
    & "$env:POETRY_HOME\bin\poetry.exe" run pytest -v
    if ($LASTEXITCODE -ne 0) {
        Write-Color -Text "!!! ", "Tests failed." -Color Red, Yellow
        Exit-WithCode 1
    }
    Write-Color -Text ">>> ", "Tests passed." -Color Green, White
}

function Main {
    if ($null -eq $FunctionName) {
        Show-Usage
        return
    }
    $FunctionName = $FunctionName.ToLower() -replace "\W"
    if ($FunctionName -eq "createenv") {
        Initialize-Environment
    } elseif ($FunctionName -eq "generatetraits") {
        Initialize-Traits
    } elseif ($FunctionName -eq "runtests") {
        Invoke-Tests
    } else {
        Write-Host "Unknown command ""$FunctionName"""
        Show-Usage
    }
}

Main
