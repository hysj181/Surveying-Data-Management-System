param(
    [string]$IndexUrl = "",
    [switch]$SkipInstall,
    [switch]$Portable
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectVenvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Invoke-BootstrapPython {
    param([string[]]$Arguments)

    if (Test-Path -LiteralPath $projectVenvPython) {
        & $projectVenvPython @Arguments
        return
    }

    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & $pyLauncher.Source -3 @Arguments
        return
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source @Arguments
        return
    }

    throw "未找到 Python，请先安装 Python 3.10 或更高版本。"
}

$pythonTag = Invoke-BootstrapPython @("-c", "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
if (-not $pythonTag) {
    throw "无法确定 Python 版本。"
}
$pythonTag = $pythonTag.Trim()

$isAsciiPath = $projectRoot -notmatch "[^\x00-\x7F]"
$buildRoot = $projectRoot

if (-not $isAsciiPath) {
    $buildRoot = Join-Path $env:PUBLIC "SurveyingDataManagerBuild$pythonTag"
    $asciiPython = Join-Path $env:PUBLIC "SurveyingDataManagerPython$pythonTag"
    New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null

    if (-not (Test-Path -LiteralPath (Join-Path $asciiPython "python.exe"))) {
        $sourcePython = Invoke-BootstrapPython @("-c", "import sys; print(sys.base_prefix)")
        if (-not $sourcePython) {
            throw "无法确定 Python 安装目录。"
        }
        Copy-Item -LiteralPath $sourcePython.Trim() -Destination $asciiPython -Recurse
    }

    if (-not (Test-Path -LiteralPath (Join-Path $buildRoot ".venv\Scripts\python.exe"))) {
        & (Join-Path $asciiPython "python.exe") -m venv (Join-Path $buildRoot ".venv")
    }

    Remove-Item -LiteralPath (Join-Path $buildRoot "src") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $buildRoot "assets") -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item -LiteralPath (Join-Path $projectRoot "src") -Destination (Join-Path $buildRoot "src") -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot "assets") -Destination (Join-Path $buildRoot "assets") -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot "pysidedeploy.spec") -Destination $buildRoot -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "requirements.txt") -Destination $buildRoot -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot "requirements-build.txt") -Destination $buildRoot -Force
    New-Item -ItemType Directory -Force -Path (Join-Path $buildRoot "temp") | Out-Null
    $env:TEMP = Join-Path $buildRoot "temp"
    $env:TMP = $env:TEMP
}

$venvPython = Join-Path $buildRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-BootstrapPython @("-m", "venv", (Join-Path $buildRoot ".venv"))
}

& $venvPython -c "import sys; assert sys.version_info >= (3, 10), '需要 Python 3.10 或更高版本'"
if ($LASTEXITCODE -ne 0) { throw "Python 版本不满足要求。" }

if (-not $SkipInstall) {
    $pipArgs = @(
        "-m", "pip", "install",
        "-r", (Join-Path $buildRoot "requirements-build.txt")
    )
    if ($IndexUrl) {
        $pipArgs += @("-i", $IndexUrl, "--trusted-host", ([uri]$IndexUrl).Host)
    }
    & $venvPython @pipArgs
    if ($LASTEXITCODE -ne 0) { throw "依赖安装失败。" }
}

New-Item -ItemType Directory -Force -Path (Join-Path $buildRoot "dist") | Out-Null
Push-Location $buildRoot
try {
    & (Join-Path $buildRoot ".venv\Scripts\pyside6-deploy.exe") `
        -c (Join-Path $buildRoot "pysidedeploy.spec") `
        --mode onefile --no-install --no-warn
    if ($LASTEXITCODE -ne 0) { throw "打包失败。" }
}
finally {
    Pop-Location
}

$builtExe = Join-Path $buildRoot "dist\SurveyingDataManager.exe"
if (-not (Test-Path -LiteralPath $builtExe)) {
    throw "未找到打包产物：$builtExe"
}

$running = Get-Process -Name "SurveyingDataManager" -ErrorAction SilentlyContinue
if ($running) {
    throw "检测到 SurveyingDataManager 正在运行，请先关闭程序后再复制打包产物。"
}

$outputDir = Join-Path $projectRoot "dist"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$finalExe = Join-Path $outputDir "SurveyingDataManager.exe"
Copy-Item -LiteralPath $builtExe -Destination $finalExe -Force
Write-Host "单文件完成：$finalExe"

if ($Portable) {
    Push-Location $buildRoot
    try {
        & (Join-Path $buildRoot ".venv\Scripts\pyside6-deploy.exe") `
            -c (Join-Path $buildRoot "pysidedeploy.spec") `
            --mode standalone --no-install --no-warn
        if ($LASTEXITCODE -ne 0) { throw "便携版打包失败。" }
    }
    finally {
        Pop-Location
    }

    $portableSource = Join-Path $buildRoot "dist\SurveyingDataManager.dist"
    if (-not (Test-Path -LiteralPath $portableSource)) {
        throw "未找到便携版目录：$portableSource"
    }

    $portableDir = Join-Path $outputDir "SurveyingDataManager-Portable"
    Remove-Item -LiteralPath $portableDir -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item -LiteralPath $portableSource -Destination $portableDir -Recurse
    Rename-Item -LiteralPath (Join-Path $portableDir "main.exe") -NewName "SurveyingDataManager.exe"
    Copy-Item -LiteralPath (Join-Path $projectRoot "scripts\portable-readme.txt") -Destination $portableDir -Force

    $zipPath = Join-Path $outputDir "SurveyingDataManager-Portable.zip"
    Remove-Item -LiteralPath $zipPath -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path (Join-Path $portableDir "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "便携版完成：$zipPath"
}
