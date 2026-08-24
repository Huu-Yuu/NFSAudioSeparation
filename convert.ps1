param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$SourceName,
    [ValidateRange(0.001, 86400)]
    [double]$Duration = 180,
    [ValidateSet("mp3", "ogg")]
    [string]$Format = "ogg",
    [ValidateRange(8000, 192000)]
    [int]$SampleRate = 44100
)

$ProjectRoot = $PSScriptRoot
$Ffmpeg = "D:\Program Files\ffmpeg-9.0.1-full_build-shared\bin\ffmpeg.exe"
$LibGme = "D:\Program Files\vcpkg-master\installed\x64-windows\bin\gme.dll"

if ([IO.Path]::IsPathRooted($SourceName) -or $SourceName -match '[\\/]' -or $SourceName -match '(^|[.])\.([.]|$)') {
    Write-Error "源文件名必须是 input 目录下的文件名：$SourceName"
    exit 2
}

$InputFile = Join-Path (Join-Path $ProjectRoot "input") $SourceName
$OutputDir = Join-Path $ProjectRoot "output"

foreach ($Dependency in @(
    @{ Path = $InputFile; Description = "源 NSF 文件" },
    @{ Path = $Ffmpeg; Description = "FFmpeg" },
    @{ Path = $LibGme; Description = "libgme" }
)) {
    if (-not (Test-Path -LiteralPath $Dependency.Path -PathType Leaf)) {
        Write-Error "$($Dependency.Description)不存在：$($Dependency.Path)"
        exit 2
    }
}

Push-Location $ProjectRoot
try {
    & python -m nsf_exporter $InputFile $OutputDir `
        --duration $Duration `
        --format $Format `
        --sample-rate $SampleRate `
        --ffmpeg $Ffmpeg `
        --libgme $LibGme
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
