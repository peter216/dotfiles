# This script calculates the size of each subfolder in a specified directory
# and the number of files in each subfolder.
# It then displays the results in a grid view.
# The script is designed to be run in a PowerShell environment.

$targetfolder='C:\Users\AppData\Local'
$dataColl = @()
gci -force $targetfolder -ErrorAction SilentlyContinue | ? { $_ -is [io.directoryinfo] } | % {
    $len = 0
    gci -recurse -force $_.fullname -ErrorAction SilentlyContinue | % { $len += $_.length }
    $filesCount = (gci -recurse -force $_.fullname -File -ErrorAction SilentlyContinue | Measure-Object).Count
  $dataObject = New-Object PSObject -Property @{
        Folder = $_.fullname
        SizeGb = ('{0:N3}' -f ($len / 1Gb)) -as [single]
        filesCount=$filesCount
    }
   $dataColl += $dataObject
   }
$dataColl | Out-GridView -Title "Subfolder sizes and number of files"
