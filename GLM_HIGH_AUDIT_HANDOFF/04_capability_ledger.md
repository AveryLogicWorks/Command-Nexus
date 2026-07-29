# Command Nexus Lattice — Capability Ledger

**Audit Date:** 2026-07-28  
**Source:** `src/core/capability_registry.py`, `src/parts/forge/capability_actions.py`, `src/core/nexus_ai_runtime.py`

---

## 1. Implementation Status Definitions

| Status | Meaning |
|--------|---------|
| **REAL** | Fully wired through runtime/tool loop; executes locally without pretending |
| **PARTIAL** | Local scaffold/fallback works; full quality output needs a model or optional API |
| **PAUSED** | Not implemented in this build; returns an honest pause message |

## 2. Canonical Runtime Intents (RUNTIME_INTENTS)

These are the 56 canonical intents that `NexusAIRuntime._classify()` can route to:

### REAL (7 intents — fully functional without external model)

| Intent | Module | Local Behavior | Notes |
|--------|--------|----------------|-------|
| Chatbot | `_run_chat()` | Local chat response with knowledge/memory/context | Works without model; richer with model |
| Document Processor | `_run_document_processor()` | Local file operations | Real file I/O via ToolExecutor |
| Notebook | `_run_notebook()` | Local note storage | Real persistence |
| Archive | `_run_archive()` | Local archive storage | Real persistence |
| Tool User | `_run_tool_user()` | Routes through CommandRouter/ToolExecutor | Real tool execution |
| Customer Support AI | `_run_customer_support()` | Customer support dialog | Real with model, scaffold without |
| Memory Recorder | `_run_memory_recorder()` | Records session/activity | Real local recording |

### PARTIAL (47 intents — scaffold works, full output needs model/API)

| Intent | Run Method | Needs | Local Fallback |
|--------|-----------|-------|----------------|
| Research | `_run_research()` | Brave Search API + model | Scaffold with search guidance |
| Coder | `_run_coder()` | Model | Local scaffold with code structure |
| Creative Writing | `_run_writer()` | Model | Local scaffold with writing template |
| Planner | `_run_planner()` | Model | Local scaffold with plan structure |
| Tutor | `_run_tutor()` | Model | Local scaffold with learning guidance |
| Business Workflow | `_run_business()` | Model | Local scaffold with workflow template |
| Data Analyst Pro | `_run_data_analyst()` | Model | Local scaffold with analysis structure |
| Code Reviewer | `_run_code_reviewer()` | Model | Local scaffold with review checklist |
| Meeting Facilitator | `_run_meeting_facilitator()` | Model | Local scaffold with agenda template |
| Security Auditor | `_run_security_auditor()` | Model | Local scaffold with audit checklist |
| Activity Watcher | `_run_activity_watcher()` | Model | Local scaffold with monitoring template |
| Financial Gainer | `_run_financial_gainer()` | Model | Local scaffold with disclaimer |
| Game Companion | `_run_game_companion()` | Model | Local scaffold with game guidance |
| Email Automation | `_run_email_automation()` | Model + email config | Local scaffold |
| API Integrator | `_run_api_integrator()` | Model + API config | Local scaffold |
| Team Orchestrator | `_run_team_orchestrator()` | Model | Local scaffold |
| Voice Interface | `_run_voice_interface()` | Model + voice config | Local scaffold |
| Visual Canvas | `_run_visual_canvas()` | Model + canvas | Local scaffold |
| Medical Researcher | `_run_medical_researcher()` | Model | Local scaffold with medical disclaimer |
| Legal Document Reviewer | `_run_legal_document_reviewer()` | Model | Local scaffold with legal disclaimer |
| Wellness Coach | `_run_wellness_coach()` | Model | Local scaffold |
| Content Strategist | `_run_content_strategist()` | Model | Local scaffold |
| Fact Checker | `_run_fact_checker()` | Model | Local scaffold |
| Task Scheduler | `_run_task_scheduler()` | Model | Local scaffold |
| Form Builder | `_run_form_builder()` | Model | Local scaffold |
| Report Generator | `_run_report_generator()` | Model | Local scaffold |
| Invoice Processor | `_run_invoice_processor()` | Model | Local scaffold |
| Spreadsheet Analyst | `_run_spreadsheet_analyst()` | Model | Local scaffold |
| Data Visualizer | `_run_data_visualizer()` | Model | Local scaffold |
| Statistical Modeler | `_run_statistical_modeler()` | Model | Local scaffold |
| Trend Forecaster | `_run_trend_forecaster()` | Model | Local scaffold |
| DevOps Assistant | `_run_devops_assistant()` | Model | Local scaffold |
| Database Manager | `_run_database_manager()` | Model | Local scaffold |
| Test Generator | `_run_test_generator()` | Model | Local scaffold |
| Documentation Generator | `_run_documentation_generator()` | Model | Local scaffold |
| Script Writer | `_run_script_writer()` | Model | Local scaffold |
| Copy Editor | `_run_copy_editor()` | Model | Local scaffold |
| Podcast Planner | `_run_podcast_planner()` | Model | Local scaffold |
| Brand Strategist | `_run_brand_strategist()` | Model | Local scaffold |
| Presentation Coach | `_run_presentation_coach()` | Model | Local scaffold |
| PR Assistant | `_run_pr_assistant()` | Model | Local scaffold |
| Internal Comms Writer | `_run_internal_comms_writer()` | Model | Local scaffold |
| Academic Citation Manager | `_run_academic_citation_manager()` | Model | Local scaffold |
| Patent Researcher | `_run_patent_researcher()` | Model | Local scaffold |
| Market Analyst | `_run_market_analyst()` | Model | Local scaffold |
| Recipe Planner | `_run_recipe_planner()` | Model | Local scaffold |
| Travel Planner | `_run_travel_planner()` | Model | Local scaffold |
| Event Planner | `_run_event_planner()` | Model | Local scaffold |
| Personal Finance Manager | `_run_personal_finance_manager()` | Model | Local scaffold |
| Privacy Compliance Checker | `_run_privacy_compliance_checker()` | Model | Local scaffold |
| Data Governance Advisor | `_run_data_governance_advisor()` | Model | Local scaffold |
| Curriculum Designer | `_run_curriculum_designer()` | Model | Local scaffold |
| Exam Prep Coach | `_run_exam_prep_coach()` | Model | Local scaffold |

### PAUSED (2 intents — not wired, honest pause)

| Intent | Pause Message |
|--------|--------------|
| Hephaestus Relay | "Hephaestus Proto-Brain integration is not connected in this build." |
| Browser | "Live browser automation is not connected in this build." |

## 3. Capability Aliases (CAPABILITY_ALIASES)

The `CAPABILITY_ALIASES` dict maps **200+ user-facing capability names** to the 56 canonical intents above. Key mappings:

| User-Facing Name | Canonical Intent |
|------------------|-----------------|
| Chat Companion | Chatbot |
| Coding Assistant | Coder |
| Research Assistant | Research |
| Creative Writer | Creative Writing |
| Task / Project Manager | Planner |
| Learning Tutor | Tutor |
| Sales Assistant | Business Workflow |
| Tool User | Tool User |
| Data Analyst Pro | Data Analyst Pro |
| Security Auditor | Security Auditor |
| Financial Gainer | Financial Gainer |
| Activity Watcher | Activity Watcher |
| Memory Recorder | Memory Recorder |
| Game Companion | Game Companion |
| Email Automation | Email Automation |
| API Integrator | API Integrator |
| Team Orchestrator | Team Orchestrator |
| Voice Interface | Voice Interface |
| Visual Canvas | Visual Canvas |
| Medical Researcher | Medical Researcher |
| Legal Document Reviewer | Legal Document Reviewer |
| Wellness Coach | Wellness Coach |
| Content Strategist | Content Strategist |
| Fact Checker | Fact Checker |
| [All Phase 7 capabilities] | [Respective canonical intents] |

## 4. Intent Classification (_classify)

The `_classify()` method at `nexus_ai_runtime.py:1226` uses **keyword matching** to determine intent. The classification checks keywords in order:

1. Capability question detection (e.g., "what can you do") → Chatbot
2. Medical Researcher keywords
3. Legal Document Reviewer keywords
4. Research keywords (research, search, find, analyze, investigate)
5. Coder keywords (code, bug, python, javascript, etc.)
6. Tool User keywords (tool, execute, run, shell, file)
7. Creative Writing keywords
8. Planner keywords
9. Document Processor keywords
10. Notebook keywords
11. Archive keywords
12. Tutor keywords
13. Business Workflow keywords
14. Customer Support AI keywords
15. Data Analyst Pro keywords
16. Code Reviewer keywords
17. Meeting Facilitator keywords
18. Security Auditor keywords
19. Financial Gainer keywords
20. Activity Watcher keywords
21. Memory Recorder keywords
22. Game Companion keywords
23. Email Automation keywords
24. API Integrator keywords
25. Team Orchestrator keywords
26. Voice Interface keywords
27. Visual Canvas keywords
28. Wellness Coach keywords
29. Content Strategist keywords
30. Fact Checker keywords
31. Task Scheduler keywords
32. Form Builder keywords
33. [All Phase 7 capabilities]
34. Default fallback → Chatbot

**Risk:** Keyword-based classification is fragile. Overlapping keywords between capabilities (e.g., "analyze" appears in Research, Data Analyst, and Market Analyst) can cause misclassification. The order of checks matters — first match wins.

## 5. Tier-Based Capability Access

| Tier | Max Capabilities per AI | Key Restrictions |
|------|------------------------|------------------|
| FREE | 3 | Basic capabilities only |
| TRIAL | 5 (Pro-level during trial) | Full access during 3-day trial |
| BASIC (Starter) | 5 | Standard capabilities |
| PRO | 7 | Most capabilities |
| BUSINESS | 10 | Business-focused capabilities |
| ENTERPRISE | 15 | All capabilities + enterprise features |
| ALL_ROUNDER | 999 (effectively unlimited) | Everything |

Individual capabilities can be purchased separately via `CAPABILITY_MIN_TIER` mapping.

## 6. Capability Guardrails

High-risk capabilities have dedicated guardrail walls in `capability_guardrails.py`:

| Capability | Walls | Key Restrictions |
|-----------|-------|------------------|
| Security Auditor | 4 walls | No exploit instructions, no bypass tutorials |
| Code Reviewer | 3 walls | No malicious code analysis, no vulnerability exploitation |
| Medical Researcher | 4 walls | No diagnosis, no prescription, no treatment advice |
| Legal Document Reviewer | 5 walls | No legal advice, no attorney-client relationship |
| Financial Gainer | 4 walls | No investment guarantees, no crypto scams |
| Coder | 2 walls | No malware, no hacking tools |
| Customer Support AI | 1 wall | No data exfiltration |
| Email Automation | 1 wall | No phishing |
| Activity Watcher | 1 wall | No surveillance of others |
| Creative Writing | 1 wall | No explicit content |

## 7. Capability Disclaimers

High-risk capabilities display disclaimers via `capability_disclaimers.py`:

- Medical Researcher: "Not a substitute for professional medical advice"
- Legal Document Reviewer: "Not legal advice; consult an attorney"
- Financial Gainer: "Not financial advice; investments carry risk"
- Security Auditor: "For authorized security testing only"
