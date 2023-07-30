$script_dir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$root = (Get-Item $script_dir).parent.FullName

if (-not (Test-Path 'env:POETRY_HOME')) {
    $env:POETRY_HOME = "$root\.poetry"
}


function New-TemporaryDirectory {
    $parent = [System.IO.Path]::GetTempPath()
    [string] $name = [System.Guid]::NewGuid()
    New-Item -ItemType Directory -Path (Join-Path $parent $name)
}

$temp_traits = New-TemporaryDirectory
Write-Host ">>> Generating traits ..."
Write-Host ">>> Temporary directory: $temp_traits"

& "$env:POETRY_HOME\bin\poetry.exe" run openassetio-traitgen -o $temp_traits -g python -v .\traits.yml
Move-Item -Path $temp_traits\Ayon\traits\* -Destination ".\AyonOpenAssetIOManager\ayon_traits" -Force
