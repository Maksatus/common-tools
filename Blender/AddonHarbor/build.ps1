<#
  Собирает zip расширения для установки в Blender.
  Версия берётся из blender_manifest.toml — отдельно её указывать не нужно.

  На выходе: dist\AddonHarbor-v<версия>.zip, внутри — файлы аддона в корне
  архива (именно так Blender ждёт расширение).

  Запуск:  powershell -ExecutionPolicy Bypass -File build.ps1
#>
[CmdletBinding()]
param(
    [string]$OutDir
)

$ErrorActionPreference = 'Stop'

$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $OutDir) { $OutDir = Join-Path $root 'dist' }

$manifestPath = Join-Path $root 'blender_manifest.toml'
foreach ($p in @($manifestPath, (Join-Path $root '__init__.py'))) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Не найден файл: $p" }
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8
$match = [regex]::Match($manifest, '(?m)^\s*version\s*=\s*"([^"]+)"')
if (-not $match.Success) { throw 'В blender_manifest.toml не нашлась строка version = "..."' }
$version = $match.Groups[1].Value

# то, что не должно попасть в архив
$exclude = @('dist', 'build.ps1', '__pycache__', '.mypy_cache')

$staging = Join-Path ([IO.Path]::GetTempPath()) ("addonharbor-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null
try {
    Get-ChildItem -LiteralPath $root | Where-Object {
        $exclude -notcontains $_.Name -and $_.Extension -ne '.pyc'
    } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $staging -Recurse
    }

    if (-not (Test-Path -LiteralPath $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir | Out-Null
    }
    $outPath = Join-Path $OutDir "AddonHarbor-v$version.zip"
    if (Test-Path -LiteralPath $outPath) { Remove-Item -LiteralPath $outPath -Force }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    # includeBaseDirectory = $false: файлы ложатся в корень архива, без лишней папки
    [IO.Compression.ZipFile]::CreateFromDirectory(
        $staging, $outPath, [IO.Compression.CompressionLevel]::Optimal, $false)
} finally {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
}

$entries = [IO.Compression.ZipFile]::OpenRead($outPath)
try {
    $names = $entries.Entries | ForEach-Object { $_.FullName }
} finally {
    $entries.Dispose()
}
if ($names -notcontains 'blender_manifest.toml') {
    throw "blender_manifest.toml не лежит в корне архива — Blender такой zip не примет"
}

$sizeKb = [Math]::Round((Get-Item -LiteralPath $outPath).Length / 1KB, 1)
Write-Host "Готово: $outPath ($sizeKb КБ)"
Write-Host ("В архиве: " + ($names -join ', '))
