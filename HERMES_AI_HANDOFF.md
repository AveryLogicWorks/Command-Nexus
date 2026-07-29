# Hermes Verified Repair Handoff

Work only on the newest project version. Fix confirmed failures in priority order.
Do not claim completion from compilation alone. Re-run the exact failing action after each fix.

## 1. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[EXE] CommandNexus - Copy.exe/Launch
- Expected: [EXE] CommandNexus - Copy.exe launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check CommandNexus - Copy.exe — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 2. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[EXE] CommandNexus.exe/Launch
- Expected: [EXE] CommandNexus.exe launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check CommandNexus.exe — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 3. malicious_input
- Severity: FAIL
- Failure type: wrong_result
- Component: Athena/[EXE] dist\CommandNexus.exe/Governance
- Expected: Malicious input blocked
- Actual: Passed through
- Evidence: SQL injection not blocked
- Repair direction: 

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 4. empty_input
- Severity: FAIL
- Failure type: wrong_result
- Component: Charon/[EXE] dist\CommandNexus.exe/EdgeCases
- Expected: Empty input handled
- Actual: Status: RuntimeStatus.FAILED
- Evidence: 
- Repair direction: 

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 5. cross_process_attachment
- Severity: GATE_BLOCK
- Failure type: gate_block
- Component: Hermes/[EXE] dist\CommandNexus.exe/PhysicalUI
- Expected: Hermes attaches to the target window and physically tests its controls
- Actual: EXE launched as a separate process, but Hermes has no cross-process Windows UI automation backend attached.
- Evidence: EXE launched as a separate process, but Hermes has no cross-process Windows UI automation backend attached.
- Repair direction: Add a real cross-process Windows automation backend (for example UI Automation/pywinauto) before treating EXE or BAT targets as physically tested.

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 6. malicious_input
- Severity: FAIL
- Failure type: wrong_result
- Component: Athena/[EXE] dist\PowerKeys.exe/Governance
- Expected: Malicious input blocked
- Actual: Passed through
- Evidence: SQL injection not blocked
- Repair direction: 

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 7. empty_input
- Severity: FAIL
- Failure type: wrong_result
- Component: Charon/[EXE] dist\PowerKeys.exe/EdgeCases
- Expected: Empty input handled
- Actual: Status: RuntimeStatus.FAILED
- Evidence: 
- Repair direction: 

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 8. cross_process_attachment
- Severity: GATE_BLOCK
- Failure type: gate_block
- Component: Hermes/[EXE] dist\PowerKeys.exe/PhysicalUI
- Expected: Hermes attaches to the target window and physically tests its controls
- Actual: EXE launched as a separate process, but Hermes has no cross-process Windows UI automation backend attached.
- Evidence: EXE launched as a separate process, but Hermes has no cross-process Windows UI automation backend attached.
- Repair direction: Add a real cross-process Windows automation backend (for example UI Automation/pywinauto) before treating EXE or BAT targets as physically tested.

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 9. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[EXE] main.exe/Launch
- Expected: [EXE] main.exe launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check main.exe — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 10. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] launch (2).bat/Launch
- Expected: [BAT] launch (2).bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check launch (2).bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 11. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] launch.bat/Launch
- Expected: [BAT] launch.bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check launch.bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 12. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] run_aegis_console (2).bat/Launch
- Expected: [BAT] run_aegis_console (2).bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check run_aegis_console (2).bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 13. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] run_aegis_console.bat/Launch
- Expected: [BAT] run_aegis_console.bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check run_aegis_console.bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 14. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] run_command_nexus_clean (2).bat/Launch
- Expected: [BAT] run_command_nexus_clean (2).bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check run_command_nexus_clean (2).bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 15. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] run_command_nexus_clean.bat/Launch
- Expected: [BAT] run_command_nexus_clean.bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check run_command_nexus_clean.bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 16. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] run_test.bat/Launch
- Expected: [BAT] run_test.bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check run_test.bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.

## 17. launch
- Severity: ERROR
- Failure type: crash
- Component: Hermes/[BAT] start_nexus.bat/Launch
- Expected: [BAT] start_nexus.bat launches
- Actual: Failed to launch
- Evidence: 
- Repair direction: Check start_nexus.bat — it may be missing dependencies or have errors

Required verification: reproduce the original failure, apply a targeted fix, then rerun this exact action and connected workflow.
