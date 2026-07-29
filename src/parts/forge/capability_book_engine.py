# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Command Nexus — Capability Knowledge Engine
Generates Knowledge entries for capabilities automatically.
Each entry describes standalone behavior + interconnections + scenarios + memory.
Code-driven — no giant static files.
"""

from __future__ import annotations

from src.core.capability_memory import (
    get_scenarios_as_prompt_text,
    get_all_scenarios_as_prompt_text,
    get_memory_manager,
)

CAPABILITIES = [
    "Chatbot", "Research", "Creative Writing", "Coder",
    "Planner", "Notebook", "Document Processor", "Archive",
    "Tool User", "Tutor", "Business Workflow", "Hephaestus Relay",
    "Activity Watcher", "Financial Gainer", "Memory Recorder", "Game Companion",
    # Phase 5 capabilities
    "Email Automation", "API Integrator", "Team Orchestrator",
    "Voice Interface", "Visual Canvas",
    # Phase 6 capabilities
    "Wellness Coach", "Content Strategist", "Fact Checker",
    # Phase 7 capabilities
    "Task Scheduler", "Form Builder", "Report Generator", "Invoice Processor",
    "Spreadsheet Analyst", "Data Visualizer", "Statistical Modeler", "Trend Forecaster",
    "DevOps Assistant", "Database Manager", "Test Generator", "Documentation Generator",
    "Script Writer", "Copy Editor", "Podcast Planner", "Brand Strategist",
    "Presentation Coach", "PR Assistant", "Internal Comms Writer", "Academic Citation Manager",
    "Patent Researcher", "Market Analyst", "Recipe Planner", "Travel Planner",
    "Event Planner", "Personal Finance Manager", "Privacy Compliance Checker",
    "Data Governance Advisor", "Curriculum Designer", "Exam Prep Coach",
]

STANDALONE = {
    "Chatbot": {"role": "Primary conversation surface and intelligent router", "input": "Natural language questions, commands, requests", "process": "Parse intent → identify capabilities needed → route → synthesize response", "output": "Direct answers or orchestrated multi-capability responses", "fallback": "Ask clarifying questions; suggest available options"},
    "Research": {"role": "Information gathering, verification, synthesis, risk assessment", "input": "Research questions, comparisons, source verification", "process": "Query → sources → evidence → confidence labels → risk assessment", "output": "Findings with confidence, citations, risk comparisons, knowledge gaps", "fallback": "Compile research brief with known/unknown boundaries"},
    "Creative Writing": {"role": "Content drafting, revision, tone control, creative output", "input": "Prompts, drafts, tone/style requests, audience specs", "process": "Understand constraints → draft → iterate → apply tone → flag assumptions", "output": "Drafts, revisions, outlines with assumption/fiction flags", "fallback": "Outline approach; ask for direction before drafting"},
    "Coder": {"role": "Code explanation, drafting, diff preview, approval-gated file/test runs", "input": "Code questions, bugs, features, review needs", "process": "Explain → draft → show diff → outline tests → flag risks", "output": "Explanations, draft code, diff previews, test plans, risk warnings", "fallback": "Explain what WOULD be done; request approval for file/execution"},
    "Planner": {"role": "Goal decomposition, task breakdown, milestone planning, risk assessment", "input": "Goals, projects, objectives, timelines, constraints", "process": "Decompose → dependencies → risk assess → prioritize → timeline", "output": "Task lists, milestone maps, dependency graphs, risk registers", "fallback": "High-level plan with noted information gaps"},
    "Notebook": {"role": "Notes capture, recall, tagging, continuity management", "input": "Notes, recall requests, tagging, continuity needs", "process": "Capture → metadata → index → retrieve → summarize", "output": "Saved notes, retrieved summaries, tagged collections, continuity briefs", "fallback": "Create new entry; ask for tagging guidance"},
    "Document Processor": {"role": "Document intake, analysis, extraction, classification, summarization", "input": "Documents, files, text, classification requests", "process": "Read → extract → classify → identify actions → summarize → compare", "output": "Summaries, extractions, classifications, action items, comparisons", "fallback": "Describe document type; ask what to extract"},
    "Archive": {"role": "Artifact storage, retrieval, indexing, lifecycle management", "input": "Artifacts, retrieval queries, organization requests", "process": "Tag → date → store → index → retrieve → lifecycle manage", "output": "Storage confirmations, retrieval results, organized collections", "fallback": "Temporary record; ask for categorization"},
    "Tool User": {"role": "Tool proposal, rationale, approval-gated invocation", "input": "Automation needs, integration requests, multi-step operations", "process": "Identify tools → explain purpose + risks → request approval → run after approval", "output": "Tool proposals, rationale, risk assessments, approval requests, execution status", "fallback": "Describe helpful tools; wait for approval"},
    "Tutor": {"role": "Educational explanation, adaptive teaching, assessment, study support", "input": "Learning goals, questions, quiz requests, study needs", "process": "Assess level → explain → check understanding → adapt → provide practice", "output": "Explanations, quizzes, study sheets, practice, assessments", "fallback": "Assess level; ask preferred format"},
    "Business Workflow": {"role": "SOP creation, checklist generation, support drafting, handoff prep", "input": "Process descriptions, support scenarios, SOP requests", "process": "Map → create checklists → draft responses → prepare handoffs → identify automation", "output": "SOPs, checklists, drafts, handoff packets, workflow maps, proposals", "fallback": "Draft workflow; ask for validation"},
    "Hephaestus Relay": {"role": "Design brief intake, constraint analysis, handoff preparation", "input": "Design ideas, requirements, constraints, materials", "process": "Structure requirements → identify constraints → list unknowns → format brief", "output": "Structured briefs, constraint lists, unknown identifications, handoff packets", "fallback": "Preliminary brief; ask for missing requirements"},
    "Activity Watcher": {"role": "Observes user work patterns, learns recurring tasks, suggests improvements and can repeat tasks with approval", "input": "User work activity, screen events, task patterns, recurring workflows", "process": "Observe → detect patterns → confirm repetition → suggest improvements → propose automation with approval", "output": "Learned task patterns, improvement suggestions, automation proposals, efficiency reports", "fallback": "Describe what it would watch; ask user to demonstrate the task"},
    "Financial Gainer": {"role": "Explores income opportunities, side hustles, monetization strategies, and financial productivity (advisory only, no guarantees)", "input": "User skills, interests, available time, financial goals, current resources", "process": "Assess skills → research opportunities → estimate ROI → flag risks → present realistic paths with disclaimer", "output": "Income path suggestions, ROI estimates, risk assessments, skill development recommendations (all advisory)", "fallback": "Provide general guidance; remind user that results depend on their effort and market conditions"},
    "Memory Recorder": {"role": "Records all session activity for auditability, recollection, and continuity — like a flight recorder for work", "input": "User actions, AI interactions, decisions, task outcomes, capability usage", "process": "Capture events → timestamp → index → store securely → enable search and replay", "output": "Session timelines, audit trails, searchable event logs, replay capability, compliance exports", "fallback": "Record what it can; flag any gaps in coverage"},
    "Game Companion": {"role": "Learns and plays games, teaches rules, suggests strategy, analyzes positions, and provides practice for individual enjoyment", "input": "Game rules, board states, user skill level, game preferences", "process": "Learn rules → assess position → suggest strategy → adapt to skill level → provide practice", "output": "Rule explanations, strategy suggestions, position analysis, practice games, skill assessments", "fallback": "Explain rules at a basic level; suggest resources for deeper learning"},
    # ─── Phase 5 Capabilities ───────────────────────────────────────
    "Email Automation": {"role": "Drafts, organizes, and manages email communications (advisory — never auto-sends)", "input": "Email requests, draft needs, inbox organization, campaign planning", "process": "Identify email type → draft content → suggest organization → plan sequences → flag compliance", "output": "Email drafts, organization frameworks, campaign plans, template suggestions", "fallback": "Provide email draft outline; remind user to review before sending"},
    "API Integrator": {"role": "Connects external APIs and services securely (advisory — never exposes credentials)", "input": "API connection requests, webhook setup, integration debugging", "process": "Identify API → determine auth method → plan connection → security checklist → test guidance", "output": "Integration plans, security checklists, debugging frameworks, configuration guidance", "fallback": "Provide integration framework; emphasize security best practices"},
    "Team Orchestrator": {"role": "Coordinates multiple AIs for complex multi-step tasks", "input": "Complex projects, multi-step workflows, task decomposition needs", "process": "Decompose task → match sub-tasks to AIs by capability → define handoffs → set execution order → aggregate results", "output": "Task assignments, workflow designs, handoff specifications, coordination plans", "fallback": "Provide decomposition framework; suggest which capabilities to use"},
    "Voice Interface": {"role": "Enables voice commands, dictation, and text-to-speech (all processing local)", "input": "Voice commands, dictation text, TTS requests, voice configuration", "process": "Receive voice input → transcribe → route to appropriate capability → synthesize response if needed", "output": "Transcribed commands, executed actions, spoken responses, voice configuration guidance", "fallback": "Provide voice command reference; suggest text input as alternative"},
    "Visual Canvas": {"role": "Creates visual representations — diagrams, mind maps, layouts, and flowcharts", "input": "Diagram requests, mind map topics, layout needs, visual organization tasks", "process": "Identify visual type → determine structure → provide text representation → suggest layout → guide creation", "output": "Text-based diagrams, mind map structures, layout frameworks, visual guidance", "fallback": "Provide text-based visual representation; suggest using Visual Canvas workspace"},
    # ─── Phase 6 Capabilities ───────────────────────────────────────
    "Wellness Coach": {"role": "Fitness planning, nutrition guidance, mental wellness support, habit building (advisory only)", "input": "Fitness goals, nutrition needs, stress management, habit tracking", "process": "Assess goals → suggest routines → provide nutrition guidance → support mental wellness → track progress", "output": "Fitness plans, meal suggestions, wellness exercises, habit trackers, progress summaries", "fallback": "Provide general wellness guidance; remind user to consult healthcare professional"},
    "Content Strategist": {"role": "Content calendar planning, audience analysis, platform optimization, brand voice development", "input": "Content goals, target audience, platform requirements, brand guidelines", "process": "Analyze audience → plan calendar → optimize per platform → repurpose content → maintain brand voice", "output": "Content calendars, audience profiles, platform-optimized content, repurposing plans, brand voice guides", "fallback": "Provide content framework; ask for audience and platform details"},
    "Fact Checker": {"role": "Claim verification, source tracking, bias detection, credibility assessment", "input": "Claims to verify, articles to check, sources to evaluate", "process": "Extract claims → identify sources → verify against multiple sources → assess credibility → report confidence", "output": "Verification status, source lists, credibility scores, bias assessments, confidence labels", "fallback": "Flag as unverified; suggest primary sources to check"},
    # ─── Phase 7 Capabilities ───────────────────────────────────────
    "Task Scheduler": {"role": "Time blocking, scheduling suggestions, reminder planning (no auto-scheduling)", "input": "Tasks to schedule, time preferences, deadline constraints", "process": "Identify priorities → estimate durations → suggest time blocks → set reminders", "output": "Schedules, time blocks, reminder suggestions, priority rankings", "fallback": "Provide scheduling framework; ask for calendar access details"},
    "Form Builder": {"role": "Form, survey, and questionnaire design with appropriate question types", "input": "Form requirements, survey goals, target respondents", "process": "Identify purpose → select question types → structure flow → design fields → provide template", "output": "Form designs, survey structures, question recommendations, field specifications", "fallback": "Provide basic form template; ask for specific requirements"},
    "Report Generator": {"role": "Structured report creation from data and context", "input": "Report requirements, data sources, audience and format needs", "process": "Structure report → generate executive summary → compile findings → add recommendations → format", "output": "Formatted reports with summaries, findings, and recommendations", "fallback": "Provide report template; ask for data input"},
    "Invoice Processor": {"role": "Invoice creation, formatting, and calculation guidance (no auto-send)", "input": "Invoice requirements, line items, tax and discount details", "process": "Gather line items → calculate totals → apply tax/discounts → format invoice → add payment terms", "output": "Formatted invoices with calculations and payment terms", "fallback": "Provide invoice template; ask for line item details"},
    "Spreadsheet Analyst": {"role": "Spreadsheet formula guidance, pivot table help, data analysis", "input": "Formula questions, data analysis needs, spreadsheet problems", "process": "Understand data → provide formula → explain logic → suggest alternatives → verify approach", "output": "Formula solutions, pivot table guidance, analysis steps, explanations", "fallback": "Provide formula reference; ask for spreadsheet structure details"},
    "Data Visualizer": {"role": "Chart type recommendations and visualization strategy", "input": "Data descriptions, visualization goals, audience needs", "process": "Analyze data type → determine goal → recommend chart types → provide design tips → explain rationale", "output": "Chart recommendations, design guidelines, visualization strategies, rationale", "fallback": "Suggest basic chart types; ask for data sample"},
    "Statistical Modeler": {"role": "Regression, hypothesis testing, and statistical analysis guidance", "input": "Analysis questions, data descriptions, statistical requirements", "process": "Select method → check assumptions → guide analysis → interpret results → report effect sizes", "output": "Method recommendations, analysis steps, interpretation guidance, assumption checks", "fallback": "Suggest basic statistical approach; ask for data details"},
    "Trend Forecaster": {"role": "Forecasting and prediction from historical data patterns", "input": "Historical data, forecasting horizon, confidence level needs", "process": "Analyze patterns → select forecasting method → project trends → provide confidence intervals", "output": "Forecasts with methodology, projections, and confidence intervals", "fallback": "Provide basic trend analysis; ask for historical data"},
    "DevOps Assistant": {"role": "CI/CD, Docker, Kubernetes, and infrastructure guidance (no production deployment)", "input": "Pipeline needs, containerization questions, infrastructure requirements", "process": "Understand requirements → provide configuration → explain best practices → flag security concerns", "output": "Pipeline configs, Dockerfiles, K8s manifests, infrastructure guidance", "fallback": "Provide general DevOps guidance; ask for specific stack details"},
    "Database Manager": {"role": "Schema design, query optimization, and migration guidance (no direct DB access)", "input": "Schema requirements, query problems, migration needs", "process": "Analyze requirements → design schema → optimize queries → plan migration → provide SQL", "output": "Schema designs, optimized queries, migration plans, SQL scripts", "fallback": "Provide schema template; ask for database type and requirements"},
    "Test Generator": {"role": "Unit, integration, and edge case test generation (execution requires approval)", "input": "Code to test, test requirements, coverage goals", "process": "Analyze code → identify test cases → generate tests → cover edge cases → add assertions", "output": "Test suites with unit tests, integration tests, edge cases, and assertions", "fallback": "Provide test template; ask for code to test"},
    "Documentation Generator": {"role": "API docs, READMEs, and user guide generation", "input": "Code descriptions, API specs, documentation requirements", "process": "Analyze code/API → structure docs → generate content → add examples → format", "output": "API documentation, READMEs, user guides, code documentation", "fallback": "Provide doc template; ask for code/API details"},
    "Script Writer": {"role": "Automation script generation in Python, shell, PowerShell (execution requires approval)", "input": "Automation needs, script requirements, language preferences", "process": "Understand task → select language → write script → add error handling → include comments", "output": "Complete scripts with comments, error handling, and usage instructions", "fallback": "Provide script template; ask for specific automation requirements"},
    "Copy Editor": {"role": "Grammar, style, clarity, and tone editing while preserving author voice", "input": "Text to edit, style guidelines, tone requirements", "process": "Read text → identify issues → edit grammar → improve clarity → adjust style → explain changes", "output": "Edited text with change notes and explanations", "fallback": "Provide editing suggestions; ask for specific concerns"},
    "Podcast Planner": {"role": "Podcast episode planning, show notes, and segment structure", "input": "Podcast topic, episode goals, target audience", "process": "Plan episode → structure segments → create show notes → suggest timestamps → provide talking points", "output": "Episode plans, show notes, segment structures, talking points", "fallback": "Provide basic episode template; ask for podcast theme"},
    "Brand Strategist": {"role": "Brand identity, positioning, values, and personality development", "input": "Business context, brand goals, target market, competitive landscape", "process": "Analyze market → define mission/vision → establish values → create positioning → develop personality", "output": "Brand strategy documents with positioning, values, personality, and voice", "fallback": "Provide brand strategy framework; ask for business context"},
    "Presentation Coach": {"role": "Presentation structure, talking points, and delivery coaching", "input": "Presentation topic, audience, time limit, goals", "process": "Structure presentation → create talking points → provide delivery tips → suggest visuals → time practice", "output": "Presentation outlines, talking points, delivery coaching tips", "fallback": "Provide presentation template; ask for topic and audience"},
    "PR Assistant": {"role": "Press releases, media pitches, and crisis response drafting (distribution requires approval)", "input": "PR needs, announcement details, target media, crisis context", "process": "Understand news → draft press release → format properly → include boilerplate → suggest distribution", "output": "Press releases, media pitches, crisis statements, PR strategies", "fallback": "Provide PR template; ask for announcement details"},
    "Internal Comms Writer": {"role": "Company announcements, team updates, and change management messages", "input": "Communication needs, audience, message context, change details", "process": "Understand context → draft message → structure clearly → add empathy → include next steps", "output": "Internal communications, announcements, team updates, change messages", "fallback": "Provide comms template; ask for message context"},
    "Academic Citation Manager": {"role": "Citation formatting in APA, MLA, Chicago, and other academic styles", "input": "Source details, citation style, bibliography requirements", "process": "Identify style → gather source details → format citation → create bibliography → verify completeness", "output": "Formatted citations, bibliographies, reference lists", "fallback": "Provide citation template; ask for source details and style"},
    "Patent Researcher": {"role": "Prior art search guidance, patent claim analysis (informational only)", "input": "Invention description, patent questions, search requirements", "process": "Guide search strategy → suggest databases → provide keywords → analyze claims → summarize findings", "output": "Search strategies, database suggestions, claim analyses, research guidance", "fallback": "Provide search framework; remind user to consult patent attorney"},
    "Market Analyst": {"role": "Market size, trends, competitor analysis, and opportunity assessment", "input": "Market questions, competitor data, industry context", "process": "Analyze market size → identify trends → assess competitors → evaluate opportunities → estimate TAM/SAM/SOM", "output": "Market analyses with size estimates, trend assessments, competitive landscapes", "fallback": "Provide market analysis framework; ask for industry details"},
    "Recipe Planner": {"role": "Meal planning, recipe suggestions, and weekly meal prep", "input": "Dietary preferences, ingredient constraints, meal count, time limits", "process": "Understand preferences → suggest recipes → create meal plan → build shopping list → provide prep tips", "output": "Weekly meal plans, recipes, shopping lists, prep instructions", "fallback": "Suggest basic meal ideas; ask for dietary preferences"},
    "Travel Planner": {"role": "Travel itinerary planning, activity suggestions, and logistics", "input": "Destination, trip duration, budget, interests", "process": "Research destination → plan daily itinerary → suggest activities → estimate costs → provide tips", "output": "Day-by-day itineraries, activity suggestions, budget estimates, travel tips", "fallback": "Provide basic itinerary template; ask for destination and budget"},
    "Event Planner": {"role": "Event planning with timeline, logistics, and checklists", "input": "Event type, guest count, budget, date, venue needs", "process": "Define scope → create timeline → plan logistics → build checklist → estimate budget → plan contingencies", "output": "Event plans with timelines, checklists, budgets, logistics", "fallback": "Provide event planning template; ask for event type and scale"},
    "Personal Finance Manager": {"role": "Budgeting, debt repayment, and savings guidance (advisory only)", "input": "Income, expenses, financial goals, debt details", "process": "Analyze income/expenses → suggest budget allocation → plan debt repayment → set savings goals → track progress", "output": "Budget plans, debt repayment strategies, savings goals, financial guidance", "fallback": "Provide budgeting framework; remind user this is not financial advice"},
    "Privacy Compliance Checker": {"role": "GDPR, CCPA, and privacy regulation compliance guidance (informational only)", "input": "Compliance questions, data practices, privacy policy needs", "process": "Identify applicable regulations → review data practices → check requirements → identify gaps → provide recommendations", "output": "Compliance assessments, gap analyses, privacy policy guidance", "fallback": "Provide compliance checklist; remind user to consult legal professional"},
    "Data Governance Advisor": {"role": "Data governance framework, quality metrics, and stewardship roles", "input": "Governance needs, data management questions, organization context", "process": "Assess needs → design framework → define roles → create policies → establish quality metrics", "output": "Governance frameworks, policy templates, role definitions, quality metrics", "fallback": "Provide governance framework template; ask for organization details"},
    "Curriculum Designer": {"role": "Course and curriculum design with learning objectives and assessments", "input": "Course topic, target learners, duration, learning goals", "process": "Define objectives → structure modules → create lessons → design activities → plan assessments", "output": "Curricula with modules, lessons, activities, assessments, and objectives", "fallback": "Provide curriculum template; ask for subject and learner level"},
    "Exam Prep Coach": {"role": "Study plans, practice strategies, and exam preparation coaching", "input": "Exam type, timeline, current level, study preferences", "process": "Assess baseline → create study schedule → suggest practice strategies → provide test-taking tips → track progress", "output": "Study plans, practice schedules, test-taking strategies, progress tracking", "fallback": "Provide study plan template; ask for exam type and timeline"},
}

# (trigger, pattern, description, conflict, synergy)
INTERCONNECTIONS = {
    "Chatbot": {
        "Research": ("User asks fact-based question", "router_researcher", "Chatbot routes to Research → Research returns findings → Chatbot presents conversationally", "Chatbot ALWAYS leads user-facing; Research never speaks directly to user", "Research enriches Chatbot with verified facts; Chatbot makes research conversational"),
        "Creative Writing": ("User wants content created", "router_creator", "Chatbot passes prompt + context to Writing → Writing returns draft → Chatbot presents", "Writing returns drafts WITH assumption flags; Chatbot strips metadata for presentation", "Writing creates; Chatbot curates; user gets polished, safe content"),
        "Coder": ("User asks code question", "router_technical", "Chatbot passes context to Coder → Coder returns explanation/draft → Chatbot presents with warnings", "Coder is show-code-only; Chatbot manages approval workflow; NEVER auto-apply", "Coder provides technical depth; Chatbot makes it accessible and safe"),
        "Planner": ("User mentions goals/tasks", "router_organizer", "Chatbot passes goals to Planner → Planner returns breakdown → Chatbot presents conversationally", "Planner creates structure; Chatbot handles the goal-setting conversation", "Planner brings order; Chatbot brings flexibility in goal exploration"),
        "Notebook": ("User wants to save or recall", "router_memory", "Chatbot auto-saves important context to Notebook; queries Notebook for continuity", "Notebook works silently; never interrupts conversation", "Notebook provides long-term memory; Chatbot provides real-time interaction"),
        "Document Processor": ("User mentions documents", "router_analyzer", "Chatbot routes document analysis; presents findings; can route to other capabilities", "Document Processor reads safely; Chatbot asks what specifically to extract", "Document Processor extracts; Chatbot orchestrates multi-capability workflows"),
        "Archive": ("User wants to save/retrieve old work", "router_storage", "Chatbot stores conversation outputs in Archive; queries Archive for historical context", "Archive auto-tags silently; Chatbot presents retrieval results", "Archive preserves history; Chatbot provides continuity across sessions"),
        "Tool User": ("User asks for automation/tools", "router_automation", "Chatbot describes need → Tool User proposes tool chain + rationale → Chatbot presents for approval", "Tool User NEVER auto-invokes; always returns proposal to Chatbot", "Tool User identifies automation; Chatbot manages the human approval loop"),
        "Tutor": ("User wants to learn", "router_teacher", "Chatbot routes learning requests → Tutor adapts level → returns content → Chatbot presents", "Tutor assesses level internally; Chatbot manages the learning conversation", "Tutor provides pedagogy; Chatbot provides conversational engagement"),
        "Business Workflow": ("User mentions processes/SOPs", "router_business", "Chatbot routes business process requests → Business Workflow creates SOPs/checklists → Chatbot presents", "Business Workflow separates draft from execution; Chatbot makes this clear", "Business Workflow structures processes; Chatbot manages business conversation"),
        "Hephaestus Relay": ("User has design ideas", "router_design", "Chatbot routes design requests → Relay structures brief → Chatbot presents with refinement loop", "Relay identifies constraints and unknowns; Chatbot asks user to fill gaps", "Relay structures requirements; Chatbot manages the design exploration"),
    },
    "Research": {
        "Chatbot": ("Research has findings to report", "researcher_router", "Research returns structured findings to Chatbot; Chatbot mediates follow-up questions", "Research outputs structured data; Chatbot converts to conversation", "Chatbot makes research accessible; Research makes Chatbot accurate"),
        "Creative Writing": ("Writing needs factual foundation", "fact_foundation", "Research provides verified facts + confidence → Writing creates content using or flagging", "Writing NEVER invents sources; uses Research findings or flags as fiction", "Research grounds creativity in facts; Writing makes facts engaging"),
        "Coder": ("Coding needs docs/API info", "tech_research", "Research gathers API docs, best practices, known issues → Coder applies to code", "Coder asks Research for specifics; Research flags deprecated/risky approaches", "Research keeps code current; Coder implements findings safely"),
        "Planner": ("Planning needs risk/feasibility data", "evidence_planning", "Research evaluates risks, competitors, feasibility → Planner integrates into plans", "Planner uses Research confidence; low-confidence gets flagged in plans", "Research provides evidence; Planner structures action"),
        "Notebook": ("Findings need storage/recall", "knowledge_storage", "All Research findings auto-save to Notebook with metadata; Notebook enables recall", "Notebook stores Research output WITHOUT modifying it", "Research discovers; Notebook remembers; both serve accuracy"),
        "Document Processor": ("Documents need research context", "doc_verification", "Document Processor extracts facts; Research verifies against external sources", "Document Processor preserves original; Research adds external context", "Document Processor reads; Research verifies; combined output is reliable"),
        "Archive": ("Findings need long-term storage", "research_history", "Research stores findings in Archive with full metadata; Archive provides historical context", "Archive maintains research history; Research queries for longitudinal analysis", "Archive preserves research evolution; Research builds on past findings"),
        "Tool User": ("Research needs automated data collection", "data_collection", "Research identifies data needs; Tool User proposes safe collection; Research evaluates results", "Tool User NEVER auto-collects; Research evaluates quality post-collection", "Tool User gathers; Research validates; combined output is verified data"),
        "Tutor": ("Teaching needs verified information", "verified_teaching", "Research verifies all teaching material; Tutor adapts to learner level", "Research flags uncertain areas; Tutor teaches critical thinking for those", "Research ensures accuracy; Tutor ensures accessibility"),
        "Business Workflow": ("Business needs market/competitive data", "intel_intelligence", "Research provides market/competitive/compliance data → Business Workflow creates evidence-based processes", "Research provides confidence levels; Business Workflow uses high-confidence for SOPs", "Research brings market reality; Business Workflow brings organizational structure"),
        "Hephaestus Relay": ("Design needs technical research", "tech_briefing", "Research evaluates technical feasibility → Relay incorporates as constraints/requirements", "Research flags unknowns; Relay lists them as open questions in brief", "Research grounds design in reality; Relay structures requirements clearly"),
    },
    "Creative Writing": {
        "Chatbot": ("Writing has drafts to present", "creator_router", "Writing returns drafts to Chatbot; Chatbot strips metadata and presents polished output", "Writing NEVER auto-publishes; always returns to Chatbot for user review", "Writing creates; Chatbot curates; user gets polished, safe content"),
        "Research": ("See Research → Creative Writing (symmetric)", "foundation_creation", "Research provides verified facts + confidence → Writing creates content using or flagging", "Writing uses high-confidence facts directly; flags low-confidence as assumptions", "Research provides foundation; Writing builds engaging content on top"),
        "Coder": ("Writing needs technical documentation", "tech_docs", "Coder provides technical content; Writing adapts tone and structure for audience", "Coder reviews Writing's technical accuracy; Writing improves Coder's accessibility", "Coder ensures accuracy; Writing ensures readability"),
        "Planner": ("Writing project needs structure", "content_schedule", "Planner creates content production phases; Writing executes within schedule", "Planner manages timeline; Writing manages quality; both report status", "Planner brings discipline; Writing brings creativity; combined = productive creation"),
        "Notebook": ("Ideas/drafts need storage", "idea_vault", "Writing stores all drafts in Notebook with version tags; retrieves on request", "Notebook preserves every version; Writing can branch from any point", "Notebook is the vault; Writing is the forge; combined = iterative creation"),
        "Document Processor": ("Writing needs source material", "source_adaptation", "Document Processor extracts content; Writing transforms into new content", "Document Processor preserves original; Writing creates derivative", "Document Processor sources; Writing creates; combined = new creations from sources"),
        "Archive": ("Completed works need storage", "content_library", "Writing stores completed works in Archive; queries Archive for reference material", "Archive stores with metadata; Writing uses as reference, not copy", "Archive is the library; Writing is the author; combined = informed creation"),
        "Tool User": ("Writing needs publishing tools", "content_pipeline", "Writing prepares content; Tool User proposes publishing/distribution tools", "Tool User NEVER auto-publishes; Writing prepares in tool-ready formats", "Writing creates; Tool User delivers; approval gate ensures safety"),
        "Tutor": ("Writing needs to teach/explain", "edu_content", "Tutor defines objectives and level; Writing creates educational content to match", "Tutor provides pedagogical guidance; Writing executes content creation", "Tutor knows HOW to teach; Writing knows WHAT to create; combined = effective education"),
        "Business Workflow": ("Business needs professional content", "pro_content", "Business Workflow defines format/audience/compliance; Writing creates professional output", "Business Workflow specifies requirements; Writing creates; both iterate", "Business Workflow knows standards; Writing knows craft; combined = professional content"),
        "Hephaestus Relay": ("Relay needs narrative documentation", "design_narrative", "Relay provides technical content; Writing creates accessible narrative documentation", "Relay reviews technical accuracy; Writing reviews clarity; both iterate", "Relay brings technical rigor; Writing brings narrative clarity; combined = clear design docs"),
    },
    "Coder": {
        "Chatbot": ("Coder has explanations/drafts", "tech_router", "Coder returns code/explanations to Chatbot; Chatbot presents with syntax highlighting and warnings", "Coder is show-code-only; Chatbot manages approval workflow", "Coder provides technical depth; Chatbot provides safety and accessibility"),
        "Research": ("See Research → Coder (symmetric)", "informed_coding", "Research provides API docs, best practices → Coder implements with current knowledge", "Coder asks Research for specifics; Research flags deprecated approaches", "Research keeps code current; Coder keeps code working"),
        "Creative Writing": ("See Creative Writing → Coder (symmetric)", "doc_engineering", "Coder creates code; Writing creates READMEs, comments, user guides", "Coder reviews Writing's technical accuracy; Writing reviews Coder's clarity", "Coder builds; Writing explains; combined = usable software"),
        "Planner": ("Coding project needs structure", "dev_project", "Planner creates dev schedule with phases; Coder implements; reports blockers", "Planner manages timeline; Coder manages implementation; both adjust", "Planner structures; Coder executes; combined = on-time delivery"),
        "Notebook": ("Solutions need storage", "code_memory", "Coder stores solutions in Notebook with language/problem tags; retrieves on similar issues", "Notebook preserves exact solutions; Coder adapts them to new contexts", "Notebook remembers; Coder adapts; combined = growing code expertise"),
        "Document Processor": ("Coding needs requirements from docs", "spec_driven", "Document Processor extracts specs from requirements; Coder implements; generates API docs", "Document Processor preserves requirements; Coder implements; both verify", "Document Processor defines WHAT; Coder defines HOW; combined = spec-driven development"),
        "Archive": ("Code versions need storage", "code_versions", "Coder stores versions in Archive; retrieves historical code for comparison/rollback", "Archive stores with metadata; Coder manages active development", "Archive preserves history; Coder creates future; combined = versioned development"),
        "Tool User": ("Coding needs build/test/deploy tools", "dev_tools", "Coder describes tooling needs; Tool User proposes safe build/test/deploy scaffolding", "Tool User NEVER auto-runs; Coder defines what; Tool User defines how", "Coder knows what to build; Tool User knows how to tool; combined = productive development"),
        "Tutor": ("Coding needs teaching", "code_edu", "Tutor assesses coding level; Coder creates level-appropriate examples and exercises", "Tutor evaluates pedagogy; Coder evaluates correctness; both review", "Tutor knows learning; Coder knows code; combined = effective coding education"),
        "Business Workflow": ("Business needs software solutions", "biz_dev", "Business Workflow defines user stories/acceptance criteria; Coder implements", "Business Workflow specifies requirements; Coder delivers; both iterate", "Business Workflow knows needs; Coder knows solutions; combined = business software"),
        "Hephaestus Relay": ("Relay design needs implementation", "design_impl", "Relay structures design requirements; Coder evaluates implementation feasibility", "Relay defines WHAT to build; Coder defines HOW to build; both align", "Relay designs; Coder builds; combined = from concept to code"),
    },
    "Planner": {
        "Chatbot": ("Planner has plans to present", "organizer_router", "Planner returns structured plans to Chatbot; Chatbot presents conversationally", "Planner creates structure; Chatbot manages the flexible goal conversation", "Planner brings order; Chatbot brings exploration; combined = planned yet flexible"),
        "Research": ("See Research → Planner (symmetric)", "evidence_planning", "Research evaluates risks/feasibility → Planner integrates into risk register and mitigation", "Planner uses Research confidence; low-confidence gets flagged in plans", "Research brings evidence; Planner structures action"),
        "Creative Writing": ("See Creative Writing → Planner (symmetric)", "content_planning", "Planner creates content production phases; Writing executes within plan", "Planner manages timeline; Writing manages quality; both report", "Planner schedules; Writing creates; combined = productive content creation"),
        "Coder": ("See Coder → Planner (symmetric)", "dev_planning", "Planner creates dev schedule; Coder implements; reports blockers; adjusts timeline", "Planner manages timeline; Coder manages implementation; both iterate", "Planner structures; Coder executes; combined = on-time software delivery"),
        "Notebook": ("Plans need storage/recall", "plan_memory", "Planner stores all plans in Notebook; Notebook recalls previous plans for reference", "Notebook preserves plans; Planner creates new from current context", "Notebook remembers plans; Planner creates new; combined = learning organization"),
        "Document Processor": ("Planning needs requirements from docs", "doc_planning", "Document Processor extracts requirements from documents; Planner creates project structure", "Document Processor reads; Planner structures; both verify completeness", "Document Processor finds requirements; Planner organizes work; combined = document-driven plans"),
        "Archive": ("Plans need historical context", "plan_history", "Planner stores completed plans in Archive; Archive provides historical project data", "Archive preserves plan history; Planner uses history for estimation", "Archive is the project archive; Planner is the project manager; combined = informed planning"),
        "Tool User": ("Planning identifies automation", "automation_planning", "Planner identifies automation opportunities; Tool User proposes tool chains", "Planner defines WHAT to automate; Tool User defines HOW; both align", "Planner sees opportunities; Tool User enables them; combined = efficient workflows"),
        "Tutor": ("Learning needs structure", "learning_plan", "Tutor defines learning objectives; Planner creates study schedule with milestones", "Tutor defines content; Planner defines timing; both adjust for learner pace", "Tutor knows WHAT to learn; Planner knows WHEN to learn; combined = structured education"),
        "Business Workflow": ("Business projects need structure", "biz_planning", "Planner structures business projects; Business Workflow creates SOPs and checklists", "Planner manages project; Business Workflow manages process; both align", "Planner manages projects; Business Workflow manages operations; combined = business execution"),
        "Hephaestus Relay": ("Design projects need scheduling", "design_planning", "Planner creates design project schedule; Relay structures requirements within timeline", "Planner manages time; Relay manages requirements; both iterate on feasibility", "Planner schedules; Relay defines; combined = feasible design projects"),
    },
    "Notebook": {
        "Chatbot": ("See Chatbot → Notebook (symmetric)", "memory_router", "Notebook auto-saves conversation context; Chatbot queries for continuity", "Notebook works silently; Chatbot presents retrieved context conversationally", "Notebook remembers; Chatbot engages; combined = continuous conversation"),
        "Research": ("See Research → Notebook (symmetric)", "knowledge_base", "All Research findings auto-save to Notebook with metadata; Notebook enables recall", "Notebook stores Research output without modification", "Research discovers; Notebook preserves; combined = growing knowledge base"),
        "Creative Writing": ("See Creative Writing → Notebook (symmetric)", "idea_vault", "Writing stores all drafts in Notebook with version tags; retrieves on request", "Notebook preserves every version; Writing can branch from any point", "Notebook is the vault; Writing is the forge; combined = iterative creation"),
        "Coder": ("See Coder → Notebook (symmetric)", "code_knowledge", "Coder stores solutions in Notebook; retrieves on similar problems", "Notebook preserves exact solutions; Coder adapts to new contexts", "Notebook remembers; Coder adapts; combined = growing code expertise"),
        "Planner": ("See Planner → Notebook (symmetric)", "plan_memory", "Planner stores plans in Notebook; Notebook recalls previous plans", "Notebook preserves; Planner creates new from current context", "Notebook remembers plans; Planner creates new; combined = learning organization"),
        "Document Processor": ("Document insights need notes", "doc_notes", "Document Processor extracts key points; Notebook stores as structured notes", "Document Processor extracts; Notebook stores; both preserve original", "Document Processor reads; Notebook remembers; combined = document comprehension"),
        "Archive": ("Active vs completed separation", "active_archive", "Notebook holds active working notes; Archive holds completed artifacts", "Notebook = workspace; Archive = repository; items move when complete", "Notebook is the desk; Archive is the filing cabinet; combined = organized workflow"),
        "Tool User": ("Tool configs need storage", "tool_notes", "Tool User stores tool configurations in Notebook; retrieves for reuse", "Notebook stores configs; Tool User executes; both maintain tool library", "Notebook remembers tool configs; Tool User uses them; combined = efficient tooling"),
        "Tutor": ("Study materials need preservation", "study_notes", "Tutor creates study materials; Notebook stores for learner review", "Tutor creates content; Notebook organizes; learner accesses both", "Tutor teaches; Notebook preserves; combined = lasting learning resources"),
        "Business Workflow": ("Process notes need storage", "process_notes", "Business Workflow creates SOPs; Notebook stores active process notes", "Business Workflow creates formal docs; Notebook holds working notes", "Business Workflow formalizes; Notebook operationalizes; combined = living processes"),
        "Hephaestus Relay": ("Design notes need preservation", "design_notes", "Relay creates briefs; Notebook stores design exploration notes and iterations", "Relay creates formal brief; Notebook holds exploratory notes", "Relay formalizes; Notebook explores; combined = thorough design process"),
    },
    "Document Processor": {
        "Chatbot": ("See Chatbot → Document Processor (symmetric)", "analyzer_router", "Document Processor extracts content; Chatbot presents and routes to other capabilities", "Document Processor reads safely; Chatbot asks what specifically to extract", "Document Processor extracts; Chatbot orchestrates; combined = intelligent document handling"),
        "Research": ("See Research → Document Processor (symmetric)", "doc_research", "Document Processor extracts facts; Research verifies against external sources", "Document Processor preserves original; Research adds external context", "Document Processor reads; Research verifies; combined = reliable document analysis"),
        "Creative Writing": ("See Creative Writing → Document Processor (symmetric)", "doc_creation", "Document Processor extracts content; Writing transforms into new content", "Document Processor preserves original; Writing creates derivative", "Document Processor sources; Writing creates; combined = derivative creation"),
        "Coder": ("See Coder → Document Processor (symmetric)", "spec_dev", "Document Processor extracts specs from requirements; Coder implements; generates API docs", "Document Processor preserves requirements; Coder implements; both verify", "Document Processor defines WHAT; Coder defines HOW; combined = spec-driven development"),
        "Planner": ("See Planner → Document Processor (symmetric)", "req_planning", "Document Processor extracts requirements from documents; Planner creates project structure", "Document Processor reads; Planner structures; both verify completeness", "Document Processor finds requirements; Planner organizes work; combined = document-driven plans"),
        "Notebook": ("See Notebook → Document Processor (symmetric)", "doc_notes", "Document Processor extracts key points; Notebook stores as structured notes", "Document Processor extracts; Notebook stores; both preserve original", "Document Processor reads; Notebook remembers; combined = document comprehension"),
        "Archive": ("Documents need long-term storage", "doc_storage", "Document Processor analyzes documents; Archive stores originals + analyses", "Document Processor creates analysis; Archive stores both original and analysis", "Document Processor analyzes; Archive preserves; combined = document archive"),
        "Tool User": ("Document processing needs tools", "doc_tools", "Document Processor identifies tool needs (OCR, format conversion); Tool User proposes safe tools", "Tool User NEVER auto-processes; always proposes and waits for approval", "Document Processor identifies needs; Tool User enables safe processing"),
        "Tutor": ("Documents need educational analysis", "edu_docs", "Document Processor extracts content; Tutor creates educational material from it", "Document Processor preserves original; Tutor creates derivative educational content", "Document Processor sources; Tutor teaches; combined = educational document use"),
        "Business Workflow": ("Business docs need processing", "biz_docs", "Document Processor analyzes business documents; Business Workflow creates processes from findings", "Document Processor extracts; Business Workflow structures; both verify compliance", "Document Processor finds; Business Workflow acts; combined = document-driven business"),
        "Hephaestus Relay": ("Design docs need processing", "design_docs", "Document Processor extracts design requirements; Relay structures them into briefs", "Document Processor reads requirements; Relay structures them; both identify gaps", "Document Processor sources; Relay structures; combined = requirement-driven design"),
    },
    "Archive": {
        "Chatbot": ("See Chatbot → Archive (symmetric)", "storage_router", "Chatbot stores conversation outputs in Archive; queries Archive for historical context", "Archive auto-tags; Chatbot presents retrieval results", "Archive preserves history; Chatbot provides continuity across sessions"),
        "Research": ("See Research → Archive (symmetric)", "research_archive", "Research stores findings in Archive with full metadata; Archive provides historical context", "Archive maintains research history; Research queries for longitudinal analysis", "Archive preserves research evolution; Research builds on past findings"),
        "Creative Writing": ("See Creative Writing → Archive (symmetric)", "content_archive", "Writing stores completed works in Archive; queries Archive for reference material", "Archive stores with metadata; Writing uses as reference, not copy", "Archive is the library; Writing is the author; combined = informed creation"),
        "Coder": ("See Coder → Archive (symmetric)", "code_archive", "Coder stores versions in Archive; retrieves historical code for comparison/rollback", "Archive stores with metadata; Coder manages active development", "Archive preserves history; Coder creates future; combined = versioned development"),
        "Planner": ("See Planner → Archive (symmetric)", "plan_archive", "Planner stores completed plans in Archive; Archive provides historical project data", "Archive preserves plan history; Planner uses history for estimation", "Archive is the project archive; Planner is the project manager; combined = informed planning"),
        "Notebook": ("See Notebook → Archive (symmetric)", "active_archive", "Notebook holds active working notes; Archive holds completed artifacts", "Notebook = workspace; Archive = repository; items move when complete", "Notebook is the desk; Archive is the filing cabinet; combined = organized workflow"),
        "Document Processor": ("See Document Processor → Archive (symmetric)", "doc_archive", "Document Processor analyzes documents; Archive stores originals + analyses", "Document Processor creates analysis; Archive stores both original and analysis", "Document Processor analyzes; Archive preserves; combined = document archive"),
        "Tool User": ("Archive needs management tools", "archive_tools", "Archive identifies management needs; Tool User proposes safe organization/migration tools", "Tool User NEVER auto-moves; always proposes and waits for approval", "Archive identifies needs; Tool User enables safe management"),
        "Tutor": ("Learning materials need archiving", "edu_archive", "Tutor creates study materials; Archive stores completed courses/lessons for reuse", "Archive stores completed materials; Tutor retrieves for adaptation", "Tutor creates; Archive preserves; combined = reusable education library"),
        "Business Workflow": ("Business artifacts need archiving", "biz_archive", "Business Workflow creates SOPs/checklists; Archive stores approved versions for compliance", "Archive stores approved versions; Business Workflow retrieves for updates", "Business Workflow creates; Archive preserves approved versions; combined = compliant operations"),
        "Hephaestus Relay": ("Design briefs need archiving", "design_archive", "Relay creates briefs; Archive stores completed briefs and design history", "Archive stores design history; Relay retrieves for iteration reference", "Relay creates; Archive preserves; combined = design evolution tracking"),
    },
    "Tool User": {
        "Chatbot": ("See Chatbot → Tool User (symmetric)", "automation_router", "Chatbot describes need → Tool User proposes tool chain + rationale → Chatbot presents for approval", "Tool User NEVER auto-invokes; always returns proposal to Chatbot", "Tool User identifies automation; Chatbot manages the human approval loop"),
        "Research": ("See Research → Tool User (symmetric)", "research_tools", "Research identifies data needs; Tool User proposes safe collection; Research evaluates results", "Tool User NEVER auto-collects; Research evaluates quality post-collection", "Tool User gathers; Research validates; combined output is verified data"),
        "Creative Writing": ("See Creative Writing → Tool User (symmetric)", "content_pipeline", "Writing prepares content; Tool User proposes publishing/distribution tools", "Tool User NEVER auto-publishes; Writing prepares in tool-ready formats", "Writing creates; Tool User delivers; approval gate ensures safety"),
        "Coder": ("See Coder → Tool User (symmetric)", "dev_tools", "Coder describes tooling needs; Tool User proposes safe build/test/deploy scaffolding", "Tool User NEVER auto-runs; Coder defines what; Tool User defines how", "Coder knows what to build; Tool User knows how to tool; combined = productive development"),
        "Planner": ("See Planner → Tool User (symmetric)", "automation_planning", "Planner identifies automation opportunities; Tool User proposes tool chains", "Planner defines WHAT to automate; Tool User defines HOW; both align", "Planner sees opportunities; Tool User enables them; combined = efficient workflows"),
        "Notebook": ("See Notebook → Tool User (symmetric)", "tool_notes", "Tool User stores tool configurations in Notebook; retrieves for reuse", "Notebook stores configs; Tool User executes; both maintain tool library", "Notebook remembers tool configs; Tool User uses them; combined = efficient tooling"),
        "Document Processor": ("See Document Processor → Tool User (symmetric)", "doc_tools", "Document Processor identifies tool needs (OCR, format conversion); Tool User proposes safe tools", "Tool User NEVER auto-processes; always proposes and waits for approval", "Document Processor identifies needs; Tool User enables safe processing"),
        "Archive": ("See Archive → Tool User (symmetric)", "archive_tools", "Archive identifies management needs; Tool User proposes safe organization/migration tools", "Tool User NEVER auto-moves; always proposes and waits for approval", "Archive identifies needs; Tool User enables safe management"),
        "Tutor": ("Learning needs interactive tools", "edu_tools", "Tutor identifies interactive tool needs; Tool User proposes safe educational tools", "Tool User NEVER auto-deploys; Tutor reviews pedagogical safety", "Tutor defines learning needs; Tool User enables safe interaction"),
        "Business Workflow": ("Business needs automation tools", "biz_tools", "Business Workflow identifies automation needs; Tool User proposes safe business tool chains", "Tool User NEVER auto-executes business actions; always proposes and waits", "Business Workflow defines processes; Tool User enables safe automation"),
        "Hephaestus Relay": ("Design needs implementation tools", "design_tools", "Relay identifies implementation tool needs; Tool User proposes safe prototyping/build tools", "Tool User NEVER auto-builds; Relay reviews design feasibility", "Relay defines design requirements; Tool User enables safe implementation exploration"),
    },
    "Tutor": {
        "Chatbot": ("See Chatbot → Tutor (symmetric)", "teacher_router", "Chatbot routes learning requests → Tutor adapts level → returns content → Chatbot presents", "Tutor assesses level internally; Chatbot manages the learning conversation", "Tutor provides pedagogy; Chatbot provides conversational engagement"),
        "Research": ("See Research → Tutor (symmetric)", "verified_teaching", "Research verifies all teaching material; Tutor adapts to learner level", "Research flags uncertain areas; Tutor teaches critical thinking for those", "Research ensures accuracy; Tutor ensures accessibility"),
        "Creative Writing": ("See Creative Writing → Tutor (symmetric)", "edu_content", "Tutor defines objectives and level; Writing creates educational content to match", "Tutor provides pedagogical guidance; Writing executes content creation", "Tutor knows HOW to teach; Writing knows WHAT to create; combined = effective education"),
        "Coder": ("See Coder → Tutor (symmetric)", "code_edu", "Tutor assesses coding level; Coder creates level-appropriate examples and exercises", "Tutor evaluates pedagogy; Coder evaluates correctness; both review", "Tutor knows learning; Coder knows code; combined = effective coding education"),
        "Planner": ("See Planner → Tutor (symmetric)", "learning_plan", "Tutor defines learning objectives; Planner creates study schedule with milestones", "Tutor defines content; Planner defines timing; both adjust for learner pace", "Tutor knows WHAT to learn; Planner knows WHEN to learn; combined = structured education"),
        "Notebook": ("See Notebook → Tutor (symmetric)", "study_notes", "Tutor creates study materials; Notebook stores for learner review", "Tutor creates content; Notebook organizes; learner accesses both", "Tutor teaches; Notebook preserves; combined = lasting learning resources"),
        "Document Processor": ("See Document Processor → Tutor (symmetric)", "edu_docs", "Document Processor extracts content; Tutor creates educational material from it", "Document Processor preserves original; Tutor creates derivative educational content", "Document Processor sources; Tutor teaches; combined = educational document use"),
        "Archive": ("See Archive → Tutor (symmetric)", "edu_archive", "Tutor creates study materials; Archive stores completed courses/lessons for reuse", "Archive stores completed materials; Tutor retrieves for adaptation", "Tutor creates; Archive preserves; combined = reusable education library"),
        "Tool User": ("See Tool User → Tutor (symmetric)", "edu_tools", "Tutor identifies interactive tool needs; Tool User proposes safe educational tools", "Tool User NEVER auto-deploys; Tutor reviews pedagogical safety", "Tutor defines learning needs; Tool User enables safe interaction"),
        "Business Workflow": ("Business training needs structure", "biz_edu", "Tutor defines training objectives; Business Workflow creates training SOPs and checklists", "Tutor defines learning outcomes; Business Workflow structures training delivery", "Tutor knows what to teach; Business Workflow knows how to deliver; combined = structured training"),
        "Hephaestus Relay": ("Design education needs structure", "design_edu", "Tutor creates design learning paths; Relay provides real-world design briefs as exercises", "Tutor ensures pedagogical soundness; Relay provides authentic challenges", "Tutor teaches principles; Relay provides practice; combined = applied design education"),
    },
    "Business Workflow": {
        "Chatbot": ("See Chatbot → Business Workflow (symmetric)", "business_router", "Chatbot routes business process requests → Business Workflow creates SOPs/checklists → Chatbot presents", "Business Workflow separates draft from execution; Chatbot makes this clear", "Business Workflow structures processes; Chatbot manages business conversation"),
        "Research": ("See Research → Business Workflow (symmetric)", "intel_intelligence", "Research provides market/competitive/compliance data → Business Workflow creates evidence-based processes", "Research provides confidence levels; Business Workflow uses high-confidence for SOPs", "Research brings market reality; Business Workflow brings organizational structure"),
        "Creative Writing": ("See Creative Writing → Business Workflow (symmetric)", "pro_content", "Business Workflow defines format/audience/compliance; Writing creates professional output", "Business Workflow specifies requirements; Writing creates; both iterate", "Business Workflow knows standards; Writing knows craft; combined = professional content"),
        "Coder": ("See Coder → Business Workflow (symmetric)", "biz_dev", "Business Workflow defines user stories/acceptance criteria; Coder implements", "Business Workflow specifies requirements; Coder delivers; both iterate", "Business Workflow knows needs; Coder knows solutions; combined = business software"),
        "Planner": ("See Planner → Business Workflow (symmetric)", "biz_planning", "Planner structures business projects; Business Workflow creates SOPs and checklists", "Planner manages project; Business Workflow manages process; both align", "Planner manages projects; Business Workflow manages operations; combined = business execution"),
        "Notebook": ("See Notebook → Business Workflow (symmetric)", "process_notes", "Business Workflow creates SOPs; Notebook stores active process notes", "Business Workflow creates formal docs; Notebook holds working notes", "Business Workflow formalizes; Notebook operationalizes; combined = living processes"),
        "Document Processor": ("See Document Processor → Business Workflow (symmetric)", "biz_docs", "Document Processor analyzes business documents; Business Workflow creates processes from findings", "Document Processor extracts; Business Workflow structures; both verify compliance", "Document Processor finds; Business Workflow acts; combined = document-driven business"),
        "Archive": ("See Archive → Business Workflow (symmetric)", "biz_archive", "Business Workflow creates SOPs/checklists; Archive stores approved versions for compliance", "Archive stores approved versions; Business Workflow retrieves for updates", "Business Workflow creates; Archive preserves approved versions; combined = compliant operations"),
        "Tool User": ("See Tool User → Business Workflow (symmetric)", "biz_tools", "Business Workflow identifies automation needs; Tool User proposes safe business tool chains", "Tool User NEVER auto-executes business actions; always proposes and waits", "Business Workflow defines processes; Tool User enables safe automation"),
        "Tutor": ("See Tutor → Business Workflow (symmetric)", "biz_edu", "Tutor defines training objectives; Business Workflow creates training SOPs and checklists", "Tutor defines learning outcomes; Business Workflow structures training delivery", "Tutor knows what to teach; Business Workflow knows how to deliver; combined = structured training"),
        "Hephaestus Relay": ("Business design needs handoff", "biz_design", "Business Workflow defines business requirements; Relay structures them into design briefs", "Business Workflow defines business needs; Relay structures for implementation", "Business Workflow defines WHAT; Relay structures HOW to deliver; combined = business-driven design"),
    },
    "Hephaestus Relay": {
        "Chatbot": ("See Chatbot → Hephaestus Relay (symmetric)", "design_router", "Chatbot routes design requests → Relay structures brief → Chatbot presents with refinement loop", "Relay identifies constraints and unknowns; Chatbot asks user to fill gaps", "Relay structures requirements; Chatbot manages the design exploration"),
        "Research": ("See Research → Hephaestus Relay (symmetric)", "tech_briefing", "Research evaluates technical feasibility → Relay incorporates as constraints/requirements", "Research flags unknowns; Relay lists them as open questions in brief", "Research grounds design in reality; Relay structures requirements clearly"),
        "Creative Writing": ("See Creative Writing → Hephaestus Relay (symmetric)", "design_narrative", "Relay provides technical content; Writing creates accessible narrative documentation", "Relay reviews technical accuracy; Writing reviews clarity; both iterate", "Relay brings technical rigor; Writing brings narrative clarity; combined = clear design docs"),
        "Coder": ("See Coder → Hephaestus Relay (symmetric)", "design_impl", "Relay structures design requirements; Coder evaluates implementation feasibility", "Relay defines WHAT to build; Coder defines HOW to build; both align", "Relay designs; Coder builds; combined = from concept to code"),
        "Planner": ("See Planner → Hephaestus Relay (symmetric)", "design_planning", "Planner creates design project schedule; Relay structures requirements within timeline", "Planner manages time; Relay manages requirements; both iterate on feasibility", "Planner schedules; Relay defines; combined = feasible design projects"),
        "Notebook": ("See Notebook → Hephaestus Relay (symmetric)", "design_notes", "Relay creates briefs; Notebook stores design exploration notes and iterations", "Relay creates formal brief; Notebook holds exploratory notes", "Relay formalizes; Notebook explores; combined = thorough design process"),
        "Document Processor": ("See Document Processor → Hephaestus Relay (symmetric)", "design_docs", "Document Processor extracts design requirements; Relay structures them into briefs", "Document Processor reads requirements; Relay structures them; both identify gaps", "Document Processor sources; Relay structures; combined = requirement-driven design"),
        "Archive": ("See Archive → Hephaestus Relay (symmetric)", "design_archive", "Relay creates briefs; Archive stores completed briefs and design history", "Archive stores design history; Relay retrieves for iteration reference", "Relay creates; Archive preserves; combined = design evolution tracking"),
        "Tool User": ("See Tool User → Hephaestus Relay (symmetric)", "design_tools", "Relay identifies implementation tool needs; Tool User proposes safe prototyping/build tools", "Tool User NEVER auto-builds; Relay reviews design feasibility", "Relay defines design requirements; Tool User enables safe implementation exploration"),
        "Tutor": ("See Tutor → Hephaestus Relay (symmetric)", "design_edu", "Tutor creates design learning paths; Relay provides real-world design briefs as exercises", "Tutor ensures pedagogical soundness; Relay provides authentic challenges", "Tutor teaches principles; Relay provides practice; combined = applied design education"),
        "Business Workflow": ("See Business Workflow → Hephaestus Relay (symmetric)", "biz_design", "Business Workflow defines business requirements; Relay structures them into design briefs", "Business Workflow defines business needs; Relay structures for implementation", "Business Workflow defines WHAT; Relay structures HOW to deliver; combined = business-driven design"),
    },

    # ─── Activity Watcher ──────────────────────────────────────────────
    "Activity Watcher": {
        "Chatbot": ("User asks about learned patterns", "watcher_router", "Activity Watcher reports learned patterns to Chatbot; Chatbot presents suggestions conversationally", "Activity Watcher never interrupts; Chatbot decides when to surface suggestions", "Activity Watcher learns; Chatbot communicates; combined = proactive assistance"),
        "Planner": ("Learned tasks need scheduling", "watcher_planner", "Activity Watcher identifies recurring tasks; Planner creates optimized schedules around them", "Planner structures; Activity Watcher provides data; both align on timing", "Activity Watcher finds patterns; Planner optimizes schedules; combined = efficient workflows"),
        "Tool User": ("Learned task can be automated", "watcher_tools", "Activity Watcher identifies automatable patterns; Tool User proposes safe automation with approval", "Tool User NEVER auto-automates; Activity Watcher suggests; both require approval", "Activity Watcher finds automation; Tool User enables it safely; combined = smart automation"),
        "Memory Recorder": ("Observations need logging", "watcher_recorder", "Activity Watcher logs all observations to Memory Recorder for auditability", "Memory Recorder records silently; Activity Watcher provides the data", "Activity Watcher observes; Memory Recorder preserves; combined = auditable learning"),
        "Notebook": ("Learned patterns need notes", "watcher_notes", "Activity Watcher stores pattern descriptions in Notebook for recall", "Notebook stores pattern summaries; Activity Watcher provides raw observations", "Activity Watcher discovers; Notebook remembers; combined = persistent learning"),
    },

    # ─── Financial Gainer ──────────────────────────────────────────────
    "Financial Gainer": {
        "Chatbot": ("User asks about making money", "gainer_router", "Chatbot routes financial opportunity questions to Financial Gainer; Gainer returns advisory suggestions", "Financial Gainer ALWAYS shows disclaimer; Chatbot presents results", "Chatbot routes; Financial Gainer advises; combined = safe financial guidance"),
        "Research": ("Opportunities need research", "gainer_research", "Research investigates market viability, competition, and demand for suggested income paths", "Research provides facts; Financial Gainer adds advisory framing with disclaimers", "Research validates; Financial Gainer advises; combined = evidence-based opportunities"),
        "Planner": ("Income path needs a plan", "gainer_planner", "Financial Gainer suggests income paths; Planner creates step-by-step execution plans", "Planner structures the effort; Financial Gainer provides the direction", "Financial Gainer identifies; Planner structures; combined = actionable income plans"),
        "Business Workflow": ("Side hustle needs SOPs", "gainer_business", "Financial Gainer identifies business opportunity; Business Workflow creates SOPs and checklists", "Business Workflow formalizes; Financial Gainer provides the idea", "Financial Gainer finds; Business Workflow structures; combined = real business execution"),
        "Data Analyst Pro": ("ROI needs analysis", "gainer_analyst", "Data Analyst Pro estimates ROI and financial projections; Financial Gainer presents with disclaimers", "Data Analyst Pro provides numbers; Financial Gainer adds context and disclaimers", "Data Analyst Pro quantifies; Financial Gainer contextualizes; combined = realistic projections"),
    },

    # ─── Memory Recorder ───────────────────────────────────────────────
    "Memory Recorder": {
        "Chatbot": ("Session needs context", "recorder_router", "Memory Recorder provides session history to Chatbot for continuity", "Memory Recorder works silently; Chatbot uses data for context", "Memory Recorder captures; Chatbot uses; combined = continuous sessions"),
        "Notebook": ("Active notes vs recordings", "recorder_notes", "Notebook holds user-created notes; Memory Recorder holds automatic session logs", "Notebook is user-driven; Memory Recorder is automatic; both serve different purposes", "Notebook is the journal; Memory Recorder is the camera; combined = complete record"),
        "Archive": ("Recordings need long-term storage", "recorder_archive", "Memory Recorder stores session logs in Archive for long-term retrieval", "Archive stores recordings; Memory Recorder creates them", "Memory Recorder records; Archive preserves; combined = permanent audit trail"),
        "Activity Watcher": ("Observations feed the recorder", "recorder_watcher", "Activity Watcher sends observations to Memory Recorder for logging", "Activity Watcher provides data; Memory Recorder stores it", "Activity Watcher watches; Memory Recorder remembers; combined = complete activity log"),
        "Document Processor": ("Recordings need searchability", "recorder_docs", "Document Processor indexes recordings for search; Memory Recorder provides the raw logs", "Document Processor structures; Memory Recorder provides content", "Memory Recorder captures; Document Processor organizes; combined = searchable history"),
    },

    # ─── Game Companion ────────────────────────────────────────────────
    "Game Companion": {
        "Chatbot": ("User wants to play", "game_router", "Chatbot routes game requests to Game Companion; Companion returns analysis/suggestions", "Game Companion is advisory; Chatbot presents conversationally", "Chatbot routes; Game Companion advises; combined = friendly game help"),
        "Tutor": ("Game needs teaching", "game_tutor", "Tutor provides pedagogical structure; Game Companion provides game-specific content", "Tutor adapts to skill level; Game Companion knows the game", "Tutor teaches how to learn; Game Companion teaches the game; combined = effective game education"),
        "Research": ("Strategy needs research", "game_research", "Research finds optimal strategies, openings, and game theory; Game Companion adapts to user level", "Research provides theory; Game Companion makes it practical", "Research finds; Game Companion applies; combined = informed gameplay"),
    },

    # ─── Email Automation ──────────────────────────────────────────────
    "Email Automation": {
        "Chatbot": ("User asks about email", "email_router", "Chatbot routes email requests to Email Automation; Automation returns drafts/plans", "Email Automation NEVER auto-sends; Chatbot presents drafts for review", "Chatbot routes; Email Automation drafts; combined = safe email assistance"),
        "Business Workflow": ("Email needs business context", "email_business", "Business Workflow provides context and tone; Email Automation drafts the email", "Business Workflow defines requirements; Email Automation creates the draft", "Business Workflow knows the audience; Email Automation knows the format; combined = professional emails"),
        "Research": ("Email needs facts", "email_research", "Research provides verified information; Email Automation incorporates into drafts", "Research provides facts with confidence; Email Automation includes or flags", "Research ensures accuracy; Email Automation ensures readability; combined = factual emails"),
        "Planner": ("Email campaign needs scheduling", "email_planner", "Planner creates email sequence timeline; Email Automation drafts each email", "Planner manages schedule; Email Automation manages content", "Planner structures the campaign; Email Automation creates the content; combined = organized campaigns"),
    },

    # ─── API Integrator ────────────────────────────────────────────────
    "API Integrator": {
        "Chatbot": ("User asks about API integration", "api_router", "Chatbot routes API requests to API Integrator; Integrator returns plans/checklists", "API Integrator NEVER auto-connects; Chatbot presents plans for approval", "Chatbot routes; API Integrator advises; combined = safe API guidance"),
        "Coder": ("API integration needs code", "api_coder", "API Integrator defines the integration; Coder implements the connection code", "API Integrator defines what; Coder defines how; both ensure security", "API Integrator plans; Coder implements; combined = working integrations"),
        "Tool User": ("API needs tool execution", "api_tools", "API Integrator identifies needs; Tool User proposes safe testing tools", "Tool User NEVER auto-executes API calls; always proposes and waits", "API Integrator plans; Tool User enables safe testing; combined = verified integrations"),
        "Research": ("API needs documentation", "api_research", "Research finds API docs and best practices; API Integrator incorporates into plan", "Research provides current docs; API Integrator structures the integration", "Research finds docs; API Integrator applies them; combined = informed integrations"),
    },

    # ─── Team Orchestrator ─────────────────────────────────────────────
    "Team Orchestrator": {
        "Chatbot": ("User has a complex multi-step task", "team_router", "Chatbot routes to Team Orchestrator; Orchestrator decomposes and assigns", "Team Orchestrator plans; Chatbot presents plan conversationally", "Chatbot routes; Team Orchestrator structures; combined = organized multi-AI work"),
        "Planner": ("Multi-AI work needs scheduling", "team_planner", "Team Orchestrator defines sub-tasks; Planner creates timeline for each", "Team Orchestrator assigns; Planner schedules; both align on dependencies", "Team Orchestrator decomposes; Planner schedules; combined = coordinated execution"),
        "Activity Watcher": ("Team workflow needs observation", "team_watcher", "Activity Watcher monitors multi-AI handoffs; Team Orchestrator adjusts based on observations", "Activity Watcher observes; Team Orchestrator adapts; both improve over time", "Activity Watcher finds bottlenecks; Team Orchestrator optimizes; combined = efficient multi-AI work"),
    },

    # ─── Voice Interface ───────────────────────────────────────────────
    "Voice Interface": {
        "Chatbot": ("User wants voice interaction", "voice_router", "Chatbot routes voice requests; Voice Interface handles speech input/output", "Voice Interface processes audio; Chatbot handles the conversation", "Voice Interface enables hands-free; Chatbot enables natural conversation; combined = accessible AI"),
        "Tutor": ("Learning needs voice support", "voice_tutor", "Voice Interface enables spoken questions; Tutor provides spoken explanations", "Voice Interface transcribes; Tutor teaches; Voice Interface can read aloud", "Voice Interface enables accessibility; Tutor enables learning; combined = accessible education"),
        "Memory Recorder": ("Voice sessions need recording", "voice_recorder", "Voice Interface transcribes speech; Memory Recorder stores transcripts", "Voice Interface captures; Memory Recorder preserves; both maintain privacy", "Voice Interface enables input; Memory Recorder ensures continuity; combined = hands-free memory"),
    },

    # ─── Visual Canvas ─────────────────────────────────────────────────
    "Visual Canvas": {
        "Chatbot": ("User wants visual representation", "canvas_router", "Chatbot routes to Visual Canvas; Canvas returns text-based visual structures", "Visual Canvas provides structure; Chatbot presents conversationally", "Chatbot routes; Visual Canvas structures; combined = visual guidance"),
        "Planner": ("Plans need visual representation", "canvas_planner", "Planner creates task breakdown; Visual Canvas represents as flowchart/mind map", "Planner creates structure; Visual Canvas visualizes it", "Planner structures; Visual Canvas visualizes; combined = visual planning"),
        "Research": ("Research needs visual organization", "canvas_research", "Research provides findings; Visual Canvas organizes as mind map or diagram", "Research provides data; Visual Canvas structures visually", "Research discovers; Visual Canvas organizes; combined = visual knowledge maps"),
        "Business Workflow": ("Processes need flowcharts", "canvas_business", "Business Workflow defines process; Visual Canvas creates flowchart representation", "Business Workflow defines steps; Visual Canvas visualizes the flow", "Business Workflow structures; Visual Canvas visualizes; combined = visual process docs"),
    },
}


def generate_capability_book_entry(capability: str) -> str:
    """Generate a full Book entry for a single capability."""
    if capability not in STANDALONE:
        return f"## {capability}\n\nUnregistered capability. Safe stub mode active.\n"

    s = STANDALONE[capability]
    lines = [
        f"## Capability: {capability}",
        "",
        f"**Role:** {s['role']}",
        f"**Input:** {s['input']}",
        f"**Process:** {s['process']}",
        f"**Output:** {s['output']}",
        f"**Fallback:** {s['fallback']}",
        "",
        "### Standalone Behavior",
        f"When operating alone, {capability} handles: {s['input']}. "
        f"It follows the process: {s['process']}. "
        f"If context is insufficient, it falls back to: {s['fallback']}.",
        "",
    ]

    # Add interconnections
    conns = INTERCONNECTIONS.get(capability, {})
    if conns:
        lines.append("### Interconnections with Other Capabilities")
        lines.append("")
        for other, (trigger, pattern, desc, conflict, synergy) in conns.items():
            lines.append(f"**With {other}:**")
            lines.append(f"- Trigger: {trigger}")
            lines.append(f"- Pattern: {pattern}")
            lines.append(f"- Flow: {desc}")
            lines.append(f"- Conflict Resolution: {conflict}")
            lines.append(f"- Synergy: {synergy}")
            lines.append("")

    # Add scenarios (use-case reference for the AI)
    scenario_text = get_scenarios_as_prompt_text(capability)
    if scenario_text:
        lines.append(scenario_text)

    # Add learned memory (AI-updated, scope-validated)
    mem_manager = get_memory_manager()
    mem = mem_manager.get_memory(capability)
    memory_text = mem.to_prompt_context()
    if memory_text:
        lines.append(memory_text)

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_full_book_for_ai(capabilities: list[str]) -> str:
    """Generate the complete Book content for an AI with the given capabilities."""
    sections = [
        "# AI Capability Book",
        "",
        "This document defines how each capability behaves standalone and how they interconnect.",
        "It is used internally by the AI to route requests, resolve conflicts, and maintain synergy.",
        "",
        "---",
        "",
    ]

    # Generate entries for each capability this AI has
    for cap in capabilities:
        sections.append(generate_capability_book_entry(cap))

    # Add cross-capability priority rules
    sections.append("## Cross-Capability Priority Rules")
    sections.append("")
    sections.append("1. **Chatbot always leads user-facing interactions.** No other capability speaks directly to the user.")
    sections.append("2. **Research feeds facts to all creative/technical capabilities.** Facts must have confidence labels.")
    sections.append("3. **Planner structures work for all execution capabilities.** Coder, Writing, Business Workflow follow Planner timelines.")
    sections.append("4. **Notebook auto-saves from all capabilities.** It is the shared memory layer.")
    sections.append("5. **Archive receives completed artifacts from all capabilities.** It is the final repository.")
    sections.append("6. **Tool User is the ONLY capability that proposes external actions.** All proposals require approval.")
    sections.append("7. **Document Processor feeds extracted content to Research, Writing, Coder, and Planner.**")
    sections.append("8. **When capabilities conflict, the user's explicit request takes priority, then Chatbot mediates.**")
    sections.append("9. **All capabilities work with built-in local intelligence. Optional backends can be configured for enhanced output.**")
    sections.append("10. **Hephaestus Relay structures output for external handoff; it never modifies internal systems.**")
    sections.append("")
    sections.append("---")
    sections.append("")
    sections.append("## Conflict Resolution Matrix")
    sections.append("")
    sections.append("| If | And | Then |")
    sections.append("|----|-----|------|")
    sections.append("| Chatbot + Research both want to respond | User asked a question | Chatbot responds using Research data |")
    sections.append("| Writing + Coder both want to create content | User asked for technical writing | Coder creates technical content; Writing adapts tone |")
    sections.append("| Planner + Business Workflow both want to structure work | User specified a business project | Planner creates timeline; Business Workflow creates SOPs |")
    sections.append("| Research + Document Processor both want to analyze | User uploaded a document | Document Processor extracts; Research verifies externally |")
    sections.append("| Tool User + Any capability wants external action | User did not explicitly request it | Tool User proposes; capability waits for approval |")
    sections.append("")

    # Add all scenarios for quick reference
    sections.append(get_all_scenarios_as_prompt_text(capabilities))

    # Add learned memory from all capabilities
    mem_manager = get_memory_manager()
    sections.append(mem_manager.get_all_memory_as_prompt_text(capabilities))

    return "\n".join(sections)


def get_capability_summary_for_ui(capability: str) -> str:
    """Return a user-friendly one-line summary of a capability."""
    if capability in STANDALONE:
        return STANDALONE[capability]["role"]
    return f"{capability} capability"
