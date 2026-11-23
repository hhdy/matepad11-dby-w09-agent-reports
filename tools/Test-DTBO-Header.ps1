[CmdletBinding()]
param(
    [string]$AnalyzerPath = (Join-Path $PSScriptRoot "Analyze-DBY-W09-Firmware.ps1")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Set-U32BE {
    param([byte[]]$Buffer, [int]$Offset, [uint64]$Value)
    $Buffer[$Offset + 0] = [byte](($Value -shr 24) -band 255)
    $Buffer[$Offset + 1] = [byte](($Value -shr 16) -band 255)
    $Buffer[$Offset + 2] = [byte](($Value -shr 8) -band 255)
    $Buffer[$Offset + 3] = [byte]($Value -band 255)
}

if (-not (Test-Path -LiteralPath $AnalyzerPath -PathType Leaf)) {
    throw "Analyzer script not found: $AnalyzerPath"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("DBY-W09-DTBO-Test-" + [Guid]::NewGuid().ToString("N"))
$inputDir = Join-Path $tempRoot "input"
$outputDir = Join-Path $tempRoot "output"

try {
    New-Item -ItemType Directory -Path $inputDir -Force | Out-Null

    # Create a synthetic, 68-byte DT table with one 32-byte entry and a 4-byte payload.
    # This exercises the high-bit DTBO magic (D7B7AB1E) that exposed the PS 5.1 bug.
    $bytes = New-Object byte[] 68
    Set-U32BE -Buffer $bytes -Offset 0 -Value ([Convert]::ToUInt32("D7B7AB1E", 16))
    Set-U32BE -Buffer $bytes -Offset 4 -Value 68
    Set-U32BE -Buffer $bytes -Offset 8 -Value 32
    Set-U32BE -Buffer $bytes -Offset 12 -Value 32
    Set-U32BE -Buffer $bytes -Offset 16 -Value 1
    Set-U32BE -Buffer $bytes -Offset 20 -Value 32
    Set-U32BE -Buffer $bytes -Offset 24 -Value 4096
    Set-U32BE -Buffer $bytes -Offset 28 -Value 0

    Set-U32BE -Buffer $bytes -Offset 32 -Value 4
    Set-U32BE -Buffer $bytes -Offset 36 -Value 64
    Set-U32BE -Buffer $bytes -Offset 40 -Value 1
    Set-U32BE -Buffer $bytes -Offset 44 -Value 1

    [System.IO.File]::WriteAllBytes((Join-Path $inputDir "dtbo.img"), $bytes)

    & $AnalyzerPath -FirmwarePath $inputDir -OutputPath $outputDir -MaxExtractMiB 8

    $reportPath = Join-Path $outputDir "firmware_analysis.txt"
    if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
        throw "Analyzer did not create firmware_analysis.txt"
    }
    $report = [System.IO.File]::ReadAllText($reportPath)

    $required = @(
        "DTBO_MAGIC_HEX: D7B7AB1E",
        "DTBO_TOTAL_SIZE_BYTES: 68",
        "DTBO_HEADER_SIZE_BYTES: 32",
        "DTBO_ENTRY_SIZE_BYTES: 32",
        "DTBO_ENTRY_COUNT: 1",
        "DTBO_ENTRIES_OFFSET: 32",
        "DTBO_PAGE_SIZE_BYTES: 4096",
        "DTBO_HEADER_VALIDATION: VALID",
        "DTBO_ENTRY_0: SIZE_BYTES=4 OFFSET=64 ID=0x00000001 REV=0x00000001"
    )

    foreach ($expected in $required) {
        if ($report.IndexOf($expected, [System.StringComparison]::Ordinal) -lt 0) {
            throw "DTBO regression test failed; report did not contain: $expected"
        }
    }

    Write-Host "PASS: Windows PowerShell DTBO high-bit magic and one-entry header test." -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
