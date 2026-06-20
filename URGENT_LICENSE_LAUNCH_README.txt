COMMAND NEXUS URGENT LICENSE LAUNCH PATCH
=========================================

What this patch fixes:
1. The activation textbox now accepts the full 40-character license key.
   - Display format: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
   - That is 40 raw characters + 9 dashes = 49 visible characters.
   - The old UI cap of 44 visible characters caused only 9 groups of 4 to fit.

2. License validation now accepts keys with or without dashes/spaces.

3. The main standalone license generators now use the same secret as the app:
   AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026

4. The generator now outputs dashed keys for easy paste, while keeping raw_key in JSON.

5. The activation dialog passes the displayed key through to the manager, so future field codes
   like HERMES-7-001 are not destroyed by dash stripping.

Immediate workflow:
1. Copy this patched app_source over B:\Documents\GitHub\Command Nexus or use APPLY_PATCH_AND_BUILD.ps1.
2. Run one of these from Command_Nexus_Keys:
   - Generate_15_Day_Trial_Key.bat
   - Generate_Basic_30_Day_2_AI_Key.bat
   - Generate_4_AI_30_Day_Key.bat
   - Generate_Unlimited_30_Day_Key.bat
3. Paste the generated dashed key into Command Nexus.
4. Confirm it shows active and Create AI is unlocked.
5. Build a new EXE if needed.

Files changed most importantly:
- src/core/license_dialog.py
- src/core/license_manager.py
- license_key_generator.py
- Command_Nexus_Keys/nexus_crypto.py
- Command_Nexus_Keys/generate_trial_key.py

Website note:
No website files were included in the uploaded handoff zip, so I included drop-in website snippets
in website_files/. Add the download button/snippet to your existing AveryLogicWorks.com page.
