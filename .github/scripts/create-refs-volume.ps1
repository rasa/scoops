# Copied from: rasa/dotfiles/.github/scripts/create-refs-volume.ps1
# EDIT THE ABOVE FILE, NOT THIS COPY, OR YOUR CHANGES WILL BE LOST!

$vhdfile = "$env:TEMP\r_refs_2gb.vhdx"
New-VHD -Path $vhdfile -Dynamic -SizeBytes 2GB
Mount-VHD -Path $vhdfile
$disk = Get-Disk | Where-Object PartitionStyle -Eq 'RAW'
Initialize-Disk -InputObject $disk -PartitionStyle GPT -PassThru |
  New-Partition -UseMaximumSize -DriveLetter 'R' |
  Format-Volume -FileSystem ReFS -NewFileSystemLabel "RREFS.2GB" -Confirm:$false
