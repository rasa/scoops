# Copied from: rasa/dotfiles/.github/scripts/create-ramdisk.ps1
# EDIT THE ABOVE FILE, NOT THIS COPY, OR YOUR CHANGES WILL BE LOST!

$vhdfile = "$env:TEMP\ntfs_n_1gb.vhdx"
New-VHD -Path $vhdfile -Dynamic -SizeBytes 1GB
Mount-VHD -Path $vhdfile
$disk = Get-Disk | Where-Object PartitionStyle -Eq 'RAW'
Initialize-Disk -InputObject $disk -PartitionStyle GPT -PassThru |
  New-Partition -UseMaximumSize -DriveLetter 'N' |
  Format-Volume -FileSystem EXFAT -NewFileSystemLabel "NTFS_N.1GB" -Confirm:$false
