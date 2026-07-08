<#
.SYNOPSIS
  Helper script create virtual environment using uv.

.DESCRIPTION
  This script will create venv using uv
  and install all necessary packages from `uv.lock` or `pyproject.toml`
  needed by AYON OpenAssetIO Manager Plugin.

.EXAMPLE

PS> .\manage.ps1

#>

$script_dir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$repo_root = (Get-Item $script_dir).parent.FullName

Write-Host "Script directory: $script_dir"
Write-Host "Repo: $repo_root"


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

function Install-Uv() {
    Write-Color -Text ">>> ", "Installing uv ... " -Color Green, Gray
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
}


function Show-Usage() {
    $usage = @'
    AYON OpenAsset Manager Plugin build tool

    Usage: ./manage.ps1 [command]

    Available commands:
            create-env                    Use uv to update venv from lock file
            generate-traits               Generate Python Traits from traits.yml
            run-tests                     Run tests

'@

    Get-AsciiArt
    Write-Host $usage -ForegroundColor Gray
}

function New-UvEnv {
    Set-Cwd
    Write-Color -Text ">>> ", "Test if UV is installed ... " -Color Green, Gray -NoNewline
    if (Get-Command "uv" -ErrorAction SilentlyContinue)
    {
        Write-Color -Text "OK" -Color Green
    } else {
        if (Test-Path -PathType Leaf -Path "$($USERPROFILE)/.cargo/bin/uv") {
            $env:PATH += ";$($env:USERPROFILE)/.cargo/bin"
            Write-Color -Text "OK" -Color Green
        } else {
            Write-Color -Text "NOT FOUND" -Color Yellow
            Install-Uv
            Write-Color -Text "INSTALLED" -Color Cyan
        }
    }
    $startTime = [int][double]::Parse((Get-Date -UFormat %s))

    # note that uv venv can use .python-version marker file to determine what python version to use
    # so you can safely use pyenv to manage python versions
    Write-Color -Text ">>> ", "Creating and activating venv ... " -Color Green, Gray
    & uv venv --allow-existing .venv
    & uv sync --all-extras
    if ($LASTEXITCODE -ne 0)
    {
        Write-Color -Text "!!! ", "Creation of virtual environment failed." -Color Red, Yellow
        Restore-Cwd
        Exit-WithCode $LASTEXITCODE
    }

    Install-PrecommitHook
    $endTime = [int][double]::Parse((Get-Date -UFormat %s))
    Restore-Cwd
    try
    {
        New-BurntToastNotification -AppLogo "$app_logo" -Text "AYON", "Virtual environment created.", "All done in $( $endTime - $startTime ) secs."
    } catch {}
    Write-Color -Text ">>> ", "Virtual environment created." -Color Green, White

    }

function New-TemporaryDirectory {
    $parent = [System.IO.Path]::GetTempPath()
    [string] $name = [System.Guid]::NewGuid()
    New-Item -ItemType Directory -Path (Join-Path $parent $name)
}

function Initialize-Traits {
    # make sure openassetio-traitgen is installed in the venv
    & uv sync --all-extras --group traitgen
    $temp_traits = New-TemporaryDirectory
    Write-Color ">>> ", "Generating traits ..." -Color Green, Gray
    Write-Color ">>> ", "Temporary directory: ", $temp_traits -Color Green, Gray, Cyan

    & uv run openassetio-traitgen -o $temp_traits -g python -v "$($repo_root)\traits.yml"
    Write-Color ">>> ", "Moving traits to repository ..." -Color Green, Gray
    $src = "$temp_traits\Ayon\traits\*"
    $dst = "$($repo_root)\plugin\ayon_openassetio_manager\ayon_traits"
    Write-Color "  - ", "Source: ", $src -Color White, Cyan -NoNewline
    Write-Color " -> ", "Destination: ", $dst -Color White, Cyan
    if(!(Test-Path $dst))
    {
        New-Item -Path $dst -ItemType Directory -Force | Out-Null
    }
    Move-Item -Path $src -Destination $dst -Force
    Write-Color -Text ">>> ", "Traits generated." -Color Green, White
}

function Invoke-Tests {
    Write-Color -Text ">>> ", "Running tests ..." -Color Green, Gray
    & uv run pytest -v
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
