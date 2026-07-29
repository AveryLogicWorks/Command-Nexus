# Resume verification from the first incomplete case.
# Phase 1: identify which test_startup.py script-mode step stalls (30s timeout each).
# Phase 2: end-to-end runtime probe (90s timeout).
# Every line is appended to $ProgressFile as it happens (visible progress).

$ErrorActionPreference = 'Continue'
$ProgressFile = "$env:USERPROFILE\cn_progress.txt"
$Root = 'B:\Documents\GitHub\CommandNexusLattice_RepairCopy_20260729'
Set-Location $Root
$env:PYTHONIOENCODING = 'utf-8'
$env:QT_QPA_PLATFORM = 'offscreen'

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    $line | Out-File $ProgressFile -Append -Encoding utf8
}

function Run-WithTimeout($file, $cmdArgs, $timeoutSec, $tag) {
    $outF = "$env:USERPROFILE\cn_step_out.txt"
    $errF = "$env:USERPROFILE\cn_step_err.txt"
    if (Test-Path $outF) { Remove-Item $outF -Force }
    if (Test-Path $errF) { Remove-Item $errF -Force }
    Log "START $tag (timeout ${timeoutSec}s)"
    $p = Start-Process -FilePath $file -ArgumentList $cmdArgs `
        -WorkingDirectory $Root -NoNewWindow -PassThru `
        -RedirectStandardOutput $outF -RedirectStandardError $errF
    $finished = $p.WaitForExit($timeoutSec * 1000)
    if ($finished) {
        Log "EXIT  $tag code=$($p.ExitCode)"
    } else {
        Log "TIMEOUT $tag after ${timeoutSec}s -> killing PID $($p.Id)"
        try { $p.Kill() } catch {}
        try { $p.WaitForExit(5000) } catch {}
    }
    if (Test-Path $outF) {
        Get-Content $outF -ErrorAction SilentlyContinue | Select-Object -Last 12 | ForEach-Object { Log "  out| $_" }
    }
    if (Test-Path $errF) {
        Get-Content $errF -ErrorAction SilentlyContinue | Select-Object -Last 6 | ForEach-Object { Log "  err| $_" }
    }
}

"=== RESUME RUN $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Out-File $ProgressFile -Encoding utf8
Log "Phase 1: startup steps (script mode), 30s timeout each"

$steps = @('test_imports','test_governance','test_settings','test_license','test_tripwire','test_watcher','test_character_sheet')
foreach ($s in $steps) {
    Run-WithTimeout 'py' @('-3.12','scripts\_probe_startup_step.py',$s) 30 $s
}

Log "Phase 2: end-to-end runtime probe, 90s timeout"
Run-WithTimeout 'py' @('-3.12','scripts\_probe_e2e_runtime.py') 90 'e2e_runtime'

Log "RESUME RUN COMPLETE"
