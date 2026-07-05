param (
    [ValidatePattern("^[A-Za-z]$")]
    [char]$DriveLetter = 'Z',

    [ValidatePattern("^\d+(MB|GB|TB)$")]
    [string]$Size = "2GB",

    [ValidateSet("exFAT", "FAT", "FAT32", "NTFS", "ReFS")]
    [string]$FileSystem = 'NTFS'
)

$randHex = '{0:x8}' -f (Get-Random -Minimum 0 -Maximum 4294967295)
$vhdfile = "$env:TEMP\~tmp_${DriveLetter}_${FileSystem}_${Size}_${randHex}.vhdx"
New-VHD -Path $vhdfile -Dynamic -SizeBytes $Size | Out-Null
Mount-VHD -Path $vhdfile | Out-Null
Start-Sleep -Seconds 1
$disk = Get-Disk | Where-Object { $_.PartitionStyle -eq 'RAW' } # -and $_.Location -like "*$vhdfile*" }
if (-not $disk) {
    Write-Error "Unable to locate newly mounted RAW disk for $vhdfile"
    exit 1
}
$partitionStyle = if ($FileSystem -in @("exFAT", "NTFS", "ReFS")) { "GPT" } else { "MBR" }
$partition = Initialize-Disk -InputObject $disk -PartitionStyle $partitionStyle -PassThru |
    New-Partition -UseMaximumSize -DriveLetter $DriveLetter
Format-Volume -Partition $partition -FileSystem $FileSystem -NewFileSystemLabel "${DriveLetter}${FileSystem}${Size}" -Confirm:$false -Force
