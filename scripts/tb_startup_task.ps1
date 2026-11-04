# Windows part of the power-cut recovery (run once per machine in PowerShell AS ADMINISTRATOR).
# Registers a task that starts the ThermBench Ubuntu at Windows startup, without anyone logging
# in, and keeps it running (so systemd starts tailscaled, ssh and tb-resume.service).
# Set $d to the distro that runs the simulations (wsl -l -v): laptop Ubuntu, pc4 Ubuntu-24.04.
# Windows asks for this PC's Windows password; it is stored by Windows only.
# Remove: Unregister-ScheduledTask -TaskName "ThermBench keep Ubuntu running"
$d = "Ubuntu-24.04"
$a = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\wsl.exe" -Argument "-d $d --exec /bin/sleep infinity"
$t = New-ScheduledTaskTrigger -AtStartup
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$c = Get-Credential -UserName "$env:USERDOMAIN\$env:USERNAME" -Message "Windows password of this PC (kept by Windows for the startup task)"
Register-ScheduledTask -TaskName "ThermBench keep Ubuntu running" -Action $a -Trigger $t -Settings $s -User $c.UserName -Password $c.GetNetworkCredential().Password -RunLevel Highest
Start-ScheduledTask -TaskName "ThermBench keep Ubuntu running"
Start-Sleep 5
Get-ScheduledTask -TaskName "ThermBench keep Ubuntu running" | Select-Object TaskName, State
wsl -l -v
