# Copied from: rasa/dotfiles/.github/scripts/create-ramdisk.ps1
# EDIT THE ABOVE FILE, NOT THIS COPY, OR YOUR CHANGES WILL BE LOST!

$vhdfile = "$env:TEMP\fat32_p_1gb.vhdx"
New-VHD -Path $vhdfile -Dynamic -SizeBytes 1GB
Mount-VHD -Path $vhdfile
$disk = Get-Disk | Where-Object PartitionStyle -Eq 'RAW'
Initialize-Disk -InputObject $disk -PartitionStyle GPT -PassThru |
  New-Partition -UseMaximumSize -DriveLetter 'P' |
  Format-Volume -FileSystem FAT32 -NewFileSystemLabel "FAT32_R.1GB" -Confirm:$false
