<#
  Собирает самодостаточный установщик: берёт install-fork-commands.bat и
  вшивает в него custom-commands.json (base64) между маркерами PAYLOAD.
  Результат: dist\ToolsReset-Installer.bat — один файл, который можно
  просто скачать и запустить, без custom-commands.json рядом.

  Запуск:  powershell -ExecutionPolicy Bypass -File build.ps1
#>
[CmdletBinding()]
param(
    [string]$OutDir
)

$ErrorActionPreference = 'Stop'

$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $OutDir) { $OutDir = Join-Path $root 'dist' }

$batPath  = Join-Path $root 'install-fork-commands.bat'
$jsonPath = Join-Path $root 'custom-commands.json'

foreach ($p in @($batPath, $jsonPath)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Не найден файл: $p" }
}

# json проверяем на валидность, чтобы не вшить в релиз битый конфиг
$jsonBytes = [IO.File]::ReadAllBytes($jsonPath)
try {
    [void]([Text.Encoding]::UTF8.GetString($jsonBytes) | ConvertFrom-Json)
} catch {
    throw "custom-commands.json не парсится как JSON: $($_.Exception.Message)"
}

$b64 = [Convert]::ToBase64String($jsonBytes)

# base64 режем на куски: строка `set` в cmd не должна упираться в лимит 8191 символ
$chunkSize = 400
$payload = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $b64.Length; $i += $chunkSize) {
    $len = [Math]::Min($chunkSize, $b64.Length - $i)
    $payload.Add('set "P=%P%' + $b64.Substring($i, $len) + '"')
}

$beginMarker = 'rem === PAYLOAD BEGIN'
$endMarker   = 'rem === PAYLOAD END'

$lines  = [IO.File]::ReadAllLines($batPath, [Text.UTF8Encoding]::new($false))
$begin  = ($lines | Select-String -SimpleMatch $beginMarker | Select-Object -First 1).LineNumber
$end    = ($lines | Select-String -SimpleMatch $endMarker   | Select-Object -First 1).LineNumber
if (-not $begin -or -not $end) { throw "В $batPath не найдены маркеры PAYLOAD BEGIN/END" }
if ($end -le $begin) { throw "Маркеры PAYLOAD идут в неверном порядке" }

# LineNumber начинается с 1: строки до BEGIN включительно + payload + строки от END
$out = New-Object System.Collections.Generic.List[string]
$out.AddRange([string[]]$lines[0..($begin - 1)])
$out.AddRange([string[]]$payload)
$out.AddRange([string[]]$lines[($end - 1)..($lines.Length - 1)])

if (-not (Test-Path -LiteralPath $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}
$outPath = Join-Path $OutDir 'ToolsReset-Installer.bat'

# cmd ждёт CRLF, UTF-8 без BOM (в батнике chcp 65001)
$text = ($out -join "`r`n") + "`r`n"
[IO.File]::WriteAllBytes($outPath, [Text.UTF8Encoding]::new($false).GetBytes($text))

$sizeKb = [Math]::Round((Get-Item -LiteralPath $outPath).Length / 1KB, 1)
Write-Host "Готово: $outPath ($sizeKb КБ, payload $($payload.Count) стр.)"
