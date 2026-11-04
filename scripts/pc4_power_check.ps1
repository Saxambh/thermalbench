# pc4: READ-ONLY check of the BMC's "after AC power loss" policy (Get Chassis Status, NetFn 0x00 cmd 0x01).
# Run in PowerShell as administrator: powershell -ExecutionPolicy Bypass -File C:\Users\Public\pc4_power_check.ps1
$ipmi = Get-CimInstance -Namespace root\wmi -ClassName Microsoft_IPMI
$r = Invoke-CimMethod -InputObject $ipmi -MethodName RequestResponse -Arguments @{
  Command = [byte]1; Lun = [byte]0; NetworkFunction = [byte]0; RequestData = [byte[]]@()
  RequestDataSize = [uint32]0; ResponderAddress = [byte]0x20 }
$s = $r.ResponseData
$names = @("stay OFF after power returns", "restore PREVIOUS state", "always power ON", "unknown")
Write-Host ("raw chassis status: " + (($s | ForEach-Object { '{0:x2}' -f $_ }) -join ' '))
if ($s[0] -eq 0) { $p = ($s[1] -shr 5) -band 3; Write-Host "power restore policy: $p = $($names[$p])"; Write-Host "power is on: $([bool]($s[1] -band 1))" }
else { Write-Host "Get Chassis Status failed, completion code $($s[0])" }
