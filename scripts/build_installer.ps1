param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$appExe = Join-Path $projectRoot "build\app\SurveyingDataManager.exe"
$setupScript = Join-Path $projectRoot "installer\setup.iss"

if (-not (Test-Path -LiteralPath $appExe)) {
    throw "未找到应用文件。请先运行 scripts\build.ps1 生成应用文件。"
}

$isccCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        $iscc = $command.Source
    }
}
if (-not $iscc) {
    throw "未找到 Inno Setup 编译器。请安装 Inno Setup 6 后重试。"
}

& $iscc $setupScript
if ($LASTEXITCODE -ne 0) {
    throw "安装包编译失败。"
}

$setupExe = Join-Path $projectRoot "dist\SurveyingDataManager-Setup-1.1.0.exe"
if (-not (Test-Path -LiteralPath $setupExe)) {
    throw "未找到安装包：$setupExe"
}
Write-Host "安装包完成：$setupExe"
