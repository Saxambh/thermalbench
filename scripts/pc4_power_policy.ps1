# pc4 (ASUS Pro WS WRX80E-SAGE SE WIFI II, onboard BMC): set "after AC power loss" through the
# BMC from Windows, no BIOS visit. Run in PowerShell AS ADMINISTRATOR on pc4:
#   powershell -ExecutionPolicy Bypass -File \wsl$\Ubuntu-24.04\home\saxam\thermbench\scripts\pc4_power_policy.ps1
# Uses the standard IPMI chassis commands via Windows' built-in IPMI driver (Microsoft_IPMI):
#   Get Chassis Status (NetFn 0x00, cmd 0x01): byte 1 bits 6:5 = restore policy
#   Set Power Restore Policy (NetFn 0x00, cmd 0x06): 0 stay off, 1 previous state, 2 always on
# Also prints the BMC's own network address (LAN parameters, NetFn 0x0C cmd 0x02).
$ErrorActionPreference = "Stop"
$ipmi = Get-CimInstance -Namespace root\wmi -ClassName Microsoft_IPMI
function Req([byte]$netfn, [byte]$cmd, [byte[]]$data) {
  $r = Invoke-CimMethod -InputObject $ipmi -MethodName RequestResponse -Arguments @{
    Command = $cmd; Lun = [byte]0; NetworkFunction = $netfn; RequestData = $data
    RequestDataSize = [uint32]$data.Length; ResponderAddress = [byte]0x20 }
  return ,$r.ResponseData
}
$names = @{0 = "stay OFF after power returns"; 1 = "restore PREVIOUS state"; 2 = "always power ON"; 3 = "unknown"}
function Policy { $s = Req 0x00 0x01 @(); if ($s[0] -ne 0) { Write-Host "Get Chassis Status failed, code $($s[0])"; return -1 }
  $p = ($s[1] -shr 5) -band 3; Write-Host "current policy: $p = $($names[[int]$p])"; return $p }   # Write-Host: shown even when the result is assigned
$id = Req 0x06 0x01 @()
"BMC: device id $($id[1]), firmware $($id[3] -band 0x7f).$('{0:x2}' -f $id[4]), IPMI v$($id[5] -band 0xf).$($id[5] -shr 4)"
$before = Policy
$set = Req 0x00 0x06 @([byte]1)
if ($set[0] -eq 0) { "set policy 1 (restore previous state): OK" } else { "set policy FAILED, completion code $($set[0])" }
$after = Policy
foreach ($ch in 1..8) {
  try { $ip = Req 0x0C 0x02 @([byte]$ch, [byte]3, [byte]0, [byte]0); $src = Req 0x0C 0x02 @([byte]$ch, [byte]4, [byte]0, [byte]0)
    if ($ip[0] -eq 0) { "BMC LAN channel ${ch}: IP $($ip[2]).$($ip[3]).$($ip[4]).$($ip[5]) (source $($src[2]): 1 static, 2 DHCP)" } } catch {}
}
