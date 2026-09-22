# PowerShell script to register daily automated snapshot task in Windows Task Scheduler
# Executes every day at 08:30 AM Beijing time.
# If the machine is off at 08:30, it runs immediately upon next boot.

$TaskName = "AmazonOpsDashboard_DailySnapshot"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$PythonExe = (Get-Command python).Source
$RunnerScript = Join-Path $ScriptDir "run_daily_snapshot.py"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing Windows Task Scheduler: $TaskName" -ForegroundColor Cyan
Write-Host " Python: $PythonExe" -ForegroundColor Gray
Write-Host " Script: $RunnerScript" -ForegroundColor Gray
Write-Host " Schedule: Daily at 08:30 AM" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

# Action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$RunnerScript`"" -WorkingDirectory $ProjectDir

# Trigger: Daily at 08:30
$Trigger = New-ScheduledTaskTrigger -Daily -At 08:30AM

# Settings: run as soon as possible if missed schedule
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily Amazon Ops Data Snapshot (08:30 AM)"
    Write-Host "[SUCCESS] Task '$TaskName' successfully registered in Windows Task Scheduler!" -ForegroundColor Green
    Write-Host "You can inspect it by running: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to register task: $_" -ForegroundColor Red
    Write-Host "Try running PowerShell as Administrator if permission is denied." -ForegroundColor Yellow
}
