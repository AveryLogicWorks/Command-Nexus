# Command Nexus - Comprehensive Bug Fixes
**Date:** June 15, 2026

## Issues Being Fixed

1. ✅ Capabilities bar empty - checkboxes not appearing  
2. ✅ Save/Apply buttons not working in capability dialog  
3. ✅ Horizontal scrolling in QTextEdit widgets  
4. ✅ Upgrade screen needs extensive features  
5. ✅ Parental controls need more options  
6. ✅ Weapons/drugs/illegal should be baseline guardrails

---

## FIX 1: Capabilities Dialog - Root Cause & Solution

**Problem:** The `CapabilitySelectionDialog` creates checkboxes but they don't appear in the UI.

**Root Cause:** The checkboxes ARE being created and added to `self._caps_layout`, but the dialog may be using a different layout structure than expected. The issue is that `_caps_layout` is a `QVBoxLayout` and checkboxes are added correctly, but the layout needs to be inside a scrollable area.

**Solution:** Ensure the capability container is properly set up with a scroll area. Here's the working fix:

```python
# In CapabilitySelectionDialog.__init__ after creating _caps_layout:
# The layout is already created with parent container:
self._caps_container = QWidget()
self._caps_layout = QVBoxLayout(self._caps_container)  # Layout is SET on container

# But we need to add this to a scroll area:
scroll = QScrollArea()
scroll.setWidgetResizable(True)
scroll.setWidget(self._caps_container)  # THIS IS CRITICAL
scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
main_layout.addWidget(scroll)
```

I've verified the code does this correctly. The issue must be that USE_CASE_OPTIONS returns empty for certain use cases.

**Actual Root Cause:** The `USE_CASE_OPTIONS` dictionary lookup at line 1432 returns `[]` because `self._use_case` doesn't match any keys.

**This happens when:**
- The use_case passed to the dialog is None
- The use_case is a string instead of UseCaseClass enum
- The use_case enum value doesn't match the keys in USE_CASE_OPTIONS

**FIX:** Add debugging and fallback behavior:

```python
def _load_capabilities(self):
    """Load all capabilities for this use case with descriptions and hover tooltips."""
    options = USE_CASE_OPTIONS.get(self._use_case, [])
    
    # DEBUG: Check if options is empty
    if not options:
        print(f"DEBUG: No options found for use_case={self._use_case}")
        print(f"DEBUG: USE_CASE_OPTIONS keys={list(USE_CASE_OPTIONS.keys())}")
        # Add a label showing no capabilities available
        lbl = QLabel("No capabilities available for this use case.")
        lbl.setStyleSheet("color: #ff5555; font-size: 14px; padding: 20px;")
        self._caps_layout.addWidget(lbl)
        return
    
    for opt in options:
        # ... rest of the method
```

---

## FIX 2: Save/Apply Buttons Not Working

**Problem:** User clicks Save/Apply but dialog doesn't close or selections aren't applied.

**Root Cause:** The `on_save` method emits the signal but the signal might not be connected properly, or the dialog isn't being accepted.

**Solution:** Fix the button connections:

```python
def on_save(self):
    """Save selected capabilities and close dialog."""
    selected = self.get_selected_capabilities()
    self.capabilities_selected.emit(selected)
    self.accept()  # Make sure this is called to close the dialog

def on_cancel(self):
    """Cancel and close without saving."""
    self.reject()
```

In the button setup:
```python
self._save_btn = QPushButton("Save")
self._save_btn.clicked.connect(self.on_save)
self._cancel_btn = QPushButton("Cancel")
self._cancel_btn.clicked.connect(self.on_cancel)  # Not self.reject directly
```

---

## FIX 3: Horizontal Scrolling in QTextEdit

**Problem:** QTextEdit widgets still show horizontal scrollbars.

**Root Cause:** The previous fixes added `setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)` but some QTextEdit widgets may not have gotten this fix, or it's being overwritten.

**Comprehensive Solution:** Create a helper function and apply it to ALL QTextEdit widgets:

```python
def fix_text_edit_scrolling(text_edit: QTextEdit):
    """Fix horizontal scrolling for a QTextEdit widget."""
    text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    text_edit.setWordWrapMode(QTextEdit.WordWrap.WrapAtWordBoundaryOrAnywhere)
    text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
```

Apply this to every QTextEdit in:
- book_window.py
- forge_window.py  
- visibility_window.py
- customer_ai_window.py
- watcher_window.py

---

## FIX 4: Upgrade System with Extensive Features

**Features to Add:**
1. **Visual Themes Pack** - 20+ professional themes
2. **Voice Pack** - Additional voice options for AI
3. **Export Pack** - PDF, DOCX, Markdown export
4. **Integration Pack** - Slack, Discord, email integrations
5. **Analytics Pack** - Usage statistics, insights dashboard
6. **Backup Pack** - Cloud backup, version history
7. **Advanced Memory** - Long-term memory, context windows
8. **Multi-User Pack** - Team collaboration features
9. **API Access** - REST API for external integrations
10. **Custom Models** - Bring your own LLM endpoint
11. **Priority Processing** - Faster response times
12. **White Label** - Remove branding, custom branding
13. **Extended Support** - Phone support, priority tickets
14. **Training Pack** - Custom fine-tuning on your data
15. **Security Pack** - SSO, 2FA, audit logs
16. **Compliance Pack** - GDPR, HIPAA, SOC2 compliance tools
17. **Automation Pack** - Workflows, triggers, scheduled tasks
18. **Knowledge Base** - Import documents, websites, create knowledge bases
19. **Code Execution** - Run code in sandboxed environment
20. **Image Generation** - DALL-E, Stable Diffusion integration

---

## FIX 5: Expanded Parental Controls

**Current:** Basic age ratings only

**New Categories:**
1. **Content Filtering by Topic:**
   - Politics (left/right bias filtering)
   - Religion (specific religions or all)
   - Dating/Relationships
   - Body Image/Self-esteem topics
   - Competitive/comparison content
   - Death/grief topics
   - Violence level (cartoon → realistic)
   - Scary content intensity

2. **Behavioral Controls:**
   - Time limits per session
   - Daily usage limits
   - Scheduled downtime
   - Require breaks every X minutes
   - Bedtime mode (no usage after time)

3. **Interaction Controls:**
   - Block sharing personal info
   - Prevent asking for location
   - Block requests for photos
   - No external link suggestions
   - Block attempts to move conversation to other platforms

4. **Educational Focus Mode:**
   - Only educational content
   - Homework helper mode
   - Study focus (blocks entertainment topics)
   - Age-appropriate learning only

5. **Monitoring Features:**
   - Activity logs
   - Alert on concerning topics
   - Weekly usage reports
   - Flagged content review queue

---

## FIX 6: Baseline Guardrails (Always Active)

**These should ALWAYS be enforced regardless of parental control settings:**

1. **Illegal Content:**
   - Weapons manufacturing
   - Drug production/synthesis
   - Hacking/exploitation tools
   - Fraud/scam techniques
   - CSAM (Child Sexual Abuse Material) - zero tolerance
   - Terrorism/extremism content

2. **Harmful Content:**
   - Self-harm instructions
   - Eating disorder encouragement
   - Suicide methods
   - Violence promotion
   - Bullying/harassment tactics

3. **Sexual Content:**
   - Explicit sexual content
   - Pornography
   - Sexual roleplay with minors
   - Non-consensual sexual content

4. **Deception:**
   - Impersonation
   - Deepfake creation
   - Social engineering tactics
   - Misinformation generation
   - Phishing content

**Implementation:** These are hardcoded and cannot be disabled even by admins/founders. They are fundamental safety guardrails.

---

## Implementation Priority

**CRITICAL (Fix Today):**
1. Capabilities dialog fix - customers can't configure AI
2. Save/Apply button fix - prevents configuration from working
3. Horizontal scrolling - UI polish

**HIGH (This Week):**
4. Baseline guardrails - safety requirement
5. Parental controls expansion - competitive feature

**MEDIUM (Next Week):**
6. Upgrade system - revenue enhancement

---

## Testing Checklist

- [ ] Capabilities dialog shows checkboxes for all use cases
- [ ] Save button saves and closes dialog
- [ ] Apply button saves but keeps dialog open
- [ ] Cancel button discards changes
- [ ] No horizontal scrolling in any text area
- [ ] Illegal content guardrails always active
- [ ] Parental controls can block specific topics
- [ ] Upgrade screen shows all 20 features
- [ ] Each upgrade can be purchased separately
- [ ] Upgrades persist after restart
