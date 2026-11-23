[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FirmwarePath,
    [string]$OutputPath = ".\DBY-W09_FirmwareAnalysis",
    [switch]$NoExtractBootImages,
    [switch]$HashLargeFiles,
    [ValidateRange(1, 2048)][int]$MaxExtractMiB = 512
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ImageClass {
    param([string]$Name, [long]$SizeBytes)
    switch -Regex ($Name.ToLowerInvariant()) {
        '^(boot|dtbo|ramdisk|recovery|recovery_ramdisk|vbmeta.*|erecovery.*)\.img$' { return "BOOT_OR_METADATA_IMAGE" }
        '^super\.img$' { return "DYNAMIC_PARTITIONS_CONTAINER" }
        '^(cache|preload|userdata)\.img$' { return "LARGE_PARTITION_IMAGE" }
        default {
            if ($SizeBytes -ge 536870912) { return "LARGE_IMAGE_REVIEW_ONLY" }
            return "OTHER_PARTITION_IMAGE"
        }
    }
}

function Read-U32LE {
    param([System.IO.FileStream]$Stream, [long]$Offset)
    if ($Stream.Length -lt ($Offset + 4)) { return $null }
    [void]$Stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
    $b = New-Object byte[] 4
    if ($Stream.Read($b, 0, 4) -ne 4) { return $null }
    return [System.BitConverter]::ToUInt32($b, 0)
}

function Read-U32BE {
    param([System.IO.FileStream]$Stream, [long]$Offset)
    if ($Stream.Length -lt ($Offset + 4)) { return $null }
    [void]$Stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
    $b = New-Object byte[] 4
    if ($Stream.Read($b, 0, 4) -ne 4) { return $null }
    return [uint32](([uint64]$b[0] * 16777216) + ([uint64]$b[1] * 65536) + ([uint64]$b[2] * 256) + [uint64]$b[3])
}

function Read-AsciiField {
    param([System.IO.FileStream]$Stream, [long]$Offset, [int]$Length)
    if ($Stream.Length -le $Offset) { return "" }
    [void]$Stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
    $available = [int][Math]::Min($Length, $Stream.Length - $Offset)
    if ($available -le 0) { return "" }
    $b = New-Object byte[] $available
    $read = $Stream.Read($b, 0, $available)
    if ($read -le 0) { return "" }
    $value = [System.Text.Encoding]::ASCII.GetString($b, 0, $read)
    $nul = $value.IndexOf([char]0)
    if ($nul -ge 0) { $value = $value.Substring(0, $nul) }
    return $value.Trim()
}

function Format-MiB {
    param([long]$Bytes)
    return [Math]::Round(($Bytes / 1MB), 2)
}

function Get-FileMagic {
    param([string]$Path)
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $b = New-Object byte[] 16
        $n = $fs.Read($b, 0, $b.Length)
        if ($n -le 0) { return "EMPTY" }
        $hex = (($b[0..([Math]::Min($n, 16) - 1)] | ForEach-Object { $_.ToString("X2") }) -join " ")
        $asciiLength = [Math]::Min($n, 8)
        $ascii = [System.Text.Encoding]::ASCII.GetString($b, 0, $asciiLength)
        if ($asciiLength -ge 8 -and $ascii.Substring(0, 8) -eq "ANDROID!") { return "ANDROID_BOOT_IMAGE | $hex" }
        if ($asciiLength -ge 4 -and $ascii.Substring(0, 4) -eq "AVB0") { return "AVB_VBMETA | $hex" }
        if ($b[0] -eq 0x1F -and $b[1] -eq 0x8B) { return "GZIP | $hex" }
        if ($b[0] -eq 0x04 -and $b[1] -eq 0x22 -and $b[2] -eq 0x4D -and $b[3] -eq 0x18) { return "LZ4_FRAME | $hex" }
        if ($b[0] -eq 0x02 -and $b[1] -eq 0x21 -and $b[2] -eq 0x4C -and $b[3] -eq 0x18) { return "LZ4_LEGACY | $hex" }
        if ($b[0] -eq 0xFD -and $b[1] -eq 0x37 -and $b[2] -eq 0x7A -and $b[3] -eq 0x58) { return "XZ | $hex" }
        if ($b[0] -eq 0x28 -and $b[1] -eq 0xB5 -and $b[2] -eq 0x2F -and $b[3] -eq 0xFD) { return "ZSTD | $hex" }
        if ($b[0] -eq 0x3A -and $b[1] -eq 0xFF -and $b[2] -eq 0x26 -and $b[3] -eq 0xED) { return "ANDROID_SPARSE_IMAGE | $hex" }
        if ($b[0] -eq 0xD0 -and $b[1] -eq 0x0D -and $b[2] -eq 0xFE -and $b[3] -eq 0xED) { return "FLATTENED_DEVICE_TREE | $hex" }
        if ($asciiLength -ge 6 -and $ascii.Substring(0, 6) -eq "070701") { return "CPIO_NEWC | $hex" }
        if ($b[0] -eq 0xD7 -and $b[1] -eq 0xB7 -and $b[2] -eq 0xAB -and $b[3] -eq 0x1E) { return "ANDROID_DTBO | $hex" }
        return "UNKNOWN | $hex"
    }
    finally { $fs.Dispose() }
}

function Get-BootImageReport {
    param([string]$Path)
    $lines = New-Object System.Collections.Generic.List[string]
    $item = Get-Item -LiteralPath $Path
    $lines.Add("FILE: " + $item.Name)
    $lines.Add("SIZE_BYTES: " + $item.Length)
    $lines.Add("MAGIC: " + (Get-FileMagic -Path $Path))
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $head = New-Object byte[] 8
        if ($fs.Read($head, 0, 8) -eq 8 -and [System.Text.Encoding]::ASCII.GetString($head) -eq "ANDROID!") {
            $version = Read-U32LE -Stream $fs -Offset 40
            $lines.Add("ANDROID_BOOT_HEADER_VERSION: " + $version)
            if ($version -le 2) {
                $lines.Add("KERNEL_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 8))
                $lines.Add("RAMDISK_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 16))
                $lines.Add("SECOND_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 24))
                $lines.Add("PAGE_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 36))
                $lines.Add("OS_VERSION_PACKED: " + (Read-U32LE -Stream $fs -Offset 44))
                $lines.Add("CMDLINE: " + (Read-AsciiField -Stream $fs -Offset 64 -Length 512))
                $extra = Read-AsciiField -Stream $fs -Offset 608 -Length 1024
                if ($extra) { $lines.Add("EXTRA_CMDLINE: " + $extra) }
                if ($version -ge 1) {
                    $lines.Add("RECOVERY_DTBO_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 1632))
                    $lines.Add("HEADER_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 1644))
                }
                if ($version -ge 2) {
                    $lines.Add("DTB_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 1648))
                    $lines.Add("DTB_ADDRESS: " + (Read-U32LE -Stream $fs -Offset 1652))
                }
            }
            else {
                $lines.Add("KERNEL_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 8))
                $lines.Add("RAMDISK_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 12))
                $lines.Add("OS_VERSION_PACKED: " + (Read-U32LE -Stream $fs -Offset 16))
                $lines.Add("HEADER_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 20))
                $lines.Add("PAGE_SIZE_BYTES: 4096 (fixed for header v3+)")
                $lines.Add("CMDLINE: " + (Read-AsciiField -Stream $fs -Offset 44 -Length 1536))
                if ($version -ge 4) { $lines.Add("BOOT_SIGNATURE_SIZE_BYTES: " + (Read-U32LE -Stream $fs -Offset 1580)) }
            }
        }
        elseif ($item.Name -match '^dtbo\.img$') {
            $magic = Read-U32BE -Stream $fs -Offset 0
            if ($magic -eq 0xD7B7AB1E) {
                $lines.Add("DTBO_TOTAL_SIZE_BYTES: " + (Read-U32BE -Stream $fs -Offset 4))
                $lines.Add("DTBO_HEADER_SIZE_BYTES: " + (Read-U32BE -Stream $fs -Offset 8))
                $lines.Add("DTBO_ENTRY_SIZE_BYTES: " + (Read-U32BE -Stream $fs -Offset 12))
                $lines.Add("DTBO_ENTRY_COUNT: " + (Read-U32BE -Stream $fs -Offset 16))
                $lines.Add("DTBO_ENTRIES_OFFSET: " + (Read-U32BE -Stream $fs -Offset 20))
                $lines.Add("DTBO_PAGE_SIZE_BYTES: " + (Read-U32BE -Stream $fs -Offset 24))
                $lines.Add("DTBO_VERSION: " + (Read-U32BE -Stream $fs -Offset 28))
            }
        }
        elseif ($item.Name -match 'ramdisk.*\.img$') {
            $lines.Add("RAMDISK_COMPRESSION_OR_FORMAT: " + (Get-FileMagic -Path $Path))
        }
    }
    finally { $fs.Dispose() }
    return $lines
}

$inputItem = Get-Item -LiteralPath $FirmwarePath
$inputFull = $inputItem.FullName
$outputFull = [System.IO.Path]::GetFullPath($OutputPath)
if ($inputItem.PSIsContainer) {
    $inputRoot = $inputFull.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    if ($outputFull.StartsWith($inputRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "OutputPath must be outside the source firmware directory. Source files are never modified."
    }
}
New-Item -ItemType Directory -Path $outputFull -Force | Out-Null
$payloadDir = Join-Path $outputFull "payloads"
if (-not $NoExtractBootImages) { New-Item -ItemType Directory -Path $payloadDir -Force | Out-Null }

$inventory = New-Object System.Collections.Generic.List[object]
$sourceFiles = New-Object System.Collections.Generic.List[object]
$sourceMode = ""
$archive = $null

if (-not $inputItem.PSIsContainer -and $inputItem.Extension -match '^\.(zip)$') {
    $sourceMode = "ZIP_ARCHIVE_READ_ONLY"
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($inputFull)
    foreach ($entry in $archive.Entries) {
        if ([string]::IsNullOrWhiteSpace($entry.Name) -or $entry.FullName -notmatch '\.img$') { continue }
        $name = [System.IO.Path]::GetFileName($entry.FullName)
        $size = [long]$entry.Length
        $inventory.Add([pscustomobject]@{
            RelativePath = $entry.FullName
            FileName = $name
            SizeBytes = $size
            SizeMiB = Format-MiB -Bytes $size
            Classification = Get-ImageClass -Name $name -SizeBytes $size
            Source = "ZIP"
        })
        $sourceFiles.Add([pscustomobject]@{ Name = $name; RelativePath = $entry.FullName; Length = $size; Entry = $entry })
    }
}
elseif ($inputItem.PSIsContainer) {
    $sourceMode = "EXTRACTED_DIRECTORY_READ_ONLY"
    $imagesDir = Join-Path $inputFull "images"
    if (-not (Test-Path -LiteralPath $imagesDir -PathType Container)) { $imagesDir = $inputFull }
    Get-ChildItem -LiteralPath $imagesDir -File -Recurse -Filter "*.img" | ForEach-Object {
        $relative = $_.FullName.Substring($imagesDir.TrimEnd('\').Length).TrimStart('\')
        $inventory.Add([pscustomobject]@{
            RelativePath = $relative
            FileName = $_.Name
            SizeBytes = [long]$_.Length
            SizeMiB = Format-MiB -Bytes ([long]$_.Length)
            Classification = Get-ImageClass -Name $_.Name -SizeBytes ([long]$_.Length)
            Source = "DIRECTORY"
        })
        $sourceFiles.Add([pscustomobject]@{ Name = $_.Name; RelativePath = $relative; Length = [long]$_.Length; FullName = $_.FullName })
    }
}
else {
    throw "FirmwarePath must be an extracted directory or a .zip package. No other file types are processed."
}

try {
    if (-not $NoExtractBootImages) {
        $selected = @($sourceFiles | Where-Object {
            $_.Name -match '^(boot|dtbo|ramdisk|recovery|recovery_ramdisk|erecovery|erecovery_ramdisk|vbmeta.*)\.img$'
        })
        $usedNames = @{}
        foreach ($source in $selected) {
            if ($source.Length -gt ($MaxExtractMiB * 1MB)) {
                $skippedLarge.Add($source.RelativePath + " (" + $source.Length + " bytes; exceeds MaxExtractMiB=" + $MaxExtractMiB + ")")
                continue
            }
            $base = [System.IO.Path]::GetFileName($source.Name)
            $destName = $base
            $counter = 1
            while ($usedNames.ContainsKey($destName)) {
                $counter++
                $destName = ([System.IO.Path]::GetFileNameWithoutExtension($base) + "_" + $counter + ".img")
            }
            $usedNames[$destName] = $true
            $destination = Join-Path $payloadDir $destName
            if ($sourceMode -eq "ZIP_ARCHIVE_READ_ONLY") {
                $inStream = $source.Entry.Open()
                $outStream = [System.IO.File]::Open($destination, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
                try { $inStream.CopyTo($outStream) }
                finally { $outStream.Dispose(); $inStream.Dispose() }
            }
            else {
                Copy-Item -LiteralPath $source.FullName -Destination $destination
            }
        }
    }

    $inventoryPath = Join-Path $outputFull "partition_inventory.csv"
    $inventory | Sort-Object RelativePath | Export-Csv -LiteralPath $inventoryPath -NoTypeInformation -Encoding UTF8
    $analysis = New-Object System.Collections.Generic.List[string]
    $analysis.Add("MatePad 11 DBY-W09 - Local Firmware Read-Only Analysis")
    $analysis.Add("Generated: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz"))
    $analysis.Add("Source mode: " + $sourceMode)
    $analysis.Add("Source name: " + $inputItem.Name)
    $analysis.Add("Image inventory rows: " + $inventory.Count)
    $analysis.Add("No device connection, ADB, fastboot, flashing, partition writes, or firmware-provided scripts were used.")
    $analysis.Add("")
    $analysis.Add("=== IMAGE INVENTORY SUMMARY ===")
    $inventory | Group-Object Classification | Sort-Object Name | ForEach-Object { $analysis.Add(($_.Name + ": " + $_.Count)) }
    $analysis.Add("")
    $analysis.Add("=== BOOT / DTBO / RAMDISK HEADER ANALYSIS ===")
    $analysis.Add("Maximum selected-image extraction size: " + $MaxExtractMiB + " MiB per file")
    $hashRows = New-Object System.Collections.Generic.List[object]
    $skippedLarge = New-Object System.Collections.Generic.List[string]
    if (-not $NoExtractBootImages -and (Test-Path -LiteralPath $payloadDir)) {
        Get-ChildItem -LiteralPath $payloadDir -File | Sort-Object Name | ForEach-Object {
            $analysis.Add("")
            $analysis.AddRange([string[]](Get-BootImageReport -Path $_.FullName))
            $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            $hashRows.Add([pscustomobject]@{ FileName = $_.Name; SizeBytes = [long]$_.Length; SHA256 = $hash; Source = "Extracted locally for inspection" })
        }
    }
    if ($skippedLarge.Count -gt 0) {
        $analysis.Add("")
        $analysis.Add("=== SKIPPED BOOT-RELATED FILES ABOVE EXTRACTION LIMIT ===")
        foreach ($skipped in $skippedLarge) { $analysis.Add($skipped) }
    }
    if ($HashLargeFiles -and $sourceMode -eq "EXTRACTED_DIRECTORY_READ_ONLY") {
        $analysis.Add("")
        $analysis.Add("=== OPTIONAL LARGE IMAGE HASHES ===")
        foreach ($source in ($sourceFiles | Where-Object { $_.Length -ge 536870912 })) {
            $analysis.Add("HASHING LARGE FILE: " + $source.RelativePath + " (" + $source.Length + " bytes)")
            $hashRows.Add([pscustomobject]@{ FileName = $source.RelativePath; SizeBytes = $source.Length; SHA256 = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash; Source = "Source image; read only" })
        }
    }
    elseif ($sourceMode -eq "ZIP_ARCHIVE_READ_ONLY") {
        $analysis.Add("")
        $analysis.Add("Large archive entries (including super.img) were inventoried but not extracted or fully hashed.")
    }
    $analysis.Add("")
    $analysis.Add("=== OPTIONAL TOOL AVAILABILITY (DETECTED ONLY; NOT EXECUTED) ===")
    foreach ($toolName in @("magiskboot", "unpack_bootimg", "unpack_bootimg.py", "lpunpack", "lpdump", "dtc", "lz4", "7z", "python", "python3", "wsl.exe")) {
        $found = Get-Command $toolName -ErrorAction SilentlyContinue
        if ($found) { $analysis.Add($toolName + ": AVAILABLE (" + $found.Source + ")") }
        else { $analysis.Add($toolName + ": NOT FOUND") }
    }
    $analysis.Add("")
    $analysis.Add("=== IMPORTANT REVIEW NOTES ===")
    $analysis.Add("1. Header identification is not proof that an image is compatible with GKI.")
    $analysis.Add("2. super.img, preload.img, cache.img and other large partitions are inventoried only; no large partition is extracted.")
    $analysis.Add("3. Boot-related files above MaxExtractMiB are not copied.")
    $analysis.Add("4. payloads/ contains local working copies. Do not commit proprietary firmware binaries to this public repository.")
    $analysis.Add("5. DTB payloads, vendor modules, UFS firmware and PCI IDs still require separate evidence-based analysis.")
    $analysis.Add("6. Verify hashes against the original package before any later experiment.")
    $analysis | Set-Content -LiteralPath (Join-Path $outputFull "firmware_analysis.txt") -Encoding UTF8
    $hashRows | Export-Csv -LiteralPath (Join-Path $outputFull "selected_images_sha256.csv") -NoTypeInformation -Encoding UTF8
    $summary = [pscustomobject]@{
        DeviceTarget = "Huawei MatePad 11 DBY-W09"
        SoCPlatform = "Qualcomm KONA / SM8250 (from existing device report; not re-probed)"
        SourceMode = $sourceMode
        SourceName = $inputItem.Name
        InventoryRows = $inventory.Count
        ExtractedBootRelatedImages = $hashRows.Count
        OutputFiles = @("partition_inventory.csv", "firmware_analysis.txt", "selected_images_sha256.csv", "payloads/")
        Safety = "Local read-only package inspection only; no device connection or partition writes."
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputFull "summary.json") -Encoding UTF8
    Write-Host ""
    Write-Host "Analysis complete." -ForegroundColor Green
    Write-Host ("Output directory: " + $outputFull)
    Write-Host ("Inventory rows: " + $inventory.Count)
    Write-Host ("Extracted local boot-related images: " + $hashRows.Count)
    Write-Host "Upload only text/CSV/JSON reports to the public repository. Do NOT upload payloads/."
}
finally {
    if ($archive) { $archive.Dispose() }
}
