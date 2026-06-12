"""
Command Nexus — Capability Book Engine
Generates Book entries for capabilities automatically.
Each entry describes standalone behavior + interconnections.
Code-driven — no giant static files.
"""

from __future__ import annotations

CAPABILITIES = [
    "Chatbot", "Research", "Creative Writing", "Coder",
    "Planner", "Notebook", "Document Processor", "Archive",
    "Tool User", "Tutor", "Business Workflow", "Hephaestus Relay",
]

STANDALONE = {
    "Chatbot": {"role": "Primary conversation surface and intelligent router", "input": "Natural language questions, commands, requests", "process": "Parse intent → identify capabilities needed → route → synthesize response", "output": "Direct answers or orchestrated multi-capability responses", "fallback": "Ask clarifying questions; suggest available options"},
    "Research": {"role": "Information gathering, verification, synthesis, risk assessment", "input": "Research questions, comparisons, source verification", "process": "Query → sources → evidence → confidence labels → risk assessment", "output": "Findings with confidence, citations, risk comparisons, knowledge gaps", "fallback": "Compile research brief with known/unknown boundaries"},
    "Creative Writing": {"role": "Content drafting, revision, tone control, creative output", "input": "Prompts, drafts, tone/style requests, audience specs", "process": "Understand constraints → draft → iterate → apply tone → flag assumptions", "output": "Drafts, revisions, outlines with assumption/fiction flags", "fallback": "Outline approach; ask for direction before drafting"},
    "Coder": {"role": "Code explanation, drafting, diff preview, safe scaffolding", "input": "Code questions, bugs, features, review needs", "process": "Explain → draft → show diff → outline tests → flag risks", "output": "Explanations, draft code, diff previews, test plans, risk warnings", "fallback": "Explain what WOULD be done; request approval for file/execution"},
    "Planner": {"role": "Goal decomposition, task breakdown, milestone planning, risk assessment", "input": "Goals, projects, objectives, timelines, constraints", "process": "Decompose → dependencies → risk assess → prioritize → timeline", "output": "Task lists, milestone maps, dependency graphs, risk registers", "fallback": "High-level plan with noted information gaps"},
    "Notebook": {"role": "Notes capture, recall, tagging, continuity management", "input": "Notes, recall requests, tagging, continuity needs", "process": "Capture → metadata → index → retrieve → summarize", "output": "Saved notes, retrieved summaries, tagged collections, continuity briefs", "fallback": "Create new entry; ask for tagging guidance"},
    "Document Processor": {"role": "Document intake, analysis, extraction, classification, summarization", "input": "Documents, files, text, classification requests", "process": "Read → extract → classify → identify actions → summarize → compare", "output": "Summaries, extractions, classifications, action items, comparisons", "fallback": "Describe document type; ask what to extract"},
    "Archive": {"role": "Artifact storage, retrieval, indexing, lifecycle management", "input": "Artifacts, retrieval queries, organization requests", "process": "Tag → date → store → index → retrieve → lifecycle manage", "output": "Storage confirmations, retrieval results, organized collections", "fallback": "Temporary record; ask for categorization"},
    "Tool User": {"role": "Tool proposal, rationale, safe invocation scaffolding", "input": "Automation needs, integration requests, multi-step operations", "process": "Identify tools → explain purpose + risks → request approval → scaffold invocation", "output": "Tool proposals, rationale, risk assessments, approval requests, scaffolding", "fallback": "Describe helpful tools; wait for approval"},
    "Tutor": {"role": "Educational explanation, adaptive teaching, assessment, study support", "input": "Learning goals, questions, quiz requests, study needs", "process": "Assess level → explain → check understanding → adapt → provide practice", "output": "Explanations, quizzes, study sheets, practice, assessments", "fallback": "Assess level; ask preferred format"},
    "Business Workflow": {"role": "SOP creation, checklist generation, support drafting, handoff prep", "input": "Process descriptions, support scenarios, SOP requests", "process": "Map → create checklists → draft responses → prepare handoffs → identify automation", "output": "SOPs, checklists, drafts, handoff packets, workflow maps, proposals", "fallback": "Draft workflow; ask for validation"},
    "Hephaestus Relay": {"role": "Design brief intake, constraint analysis, handoff preparation", "input": "Design ideas, requirements, constraints, materials", "process": "Structure requirements → identify constraints → list unknowns → format brief", "output": "Structured briefs, constraint lists, unknown identifications, handoff packets", "fallback": "Preliminary brief; ask for missing requirements"},
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
    sections.append("9. **All capabilities fall back to safe stub mode if backends are not connected.**")
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

    return "\n".join(sections)


def get_capability_summary_for_ui(capability: str) -> str:
    """Return a user-friendly one-line summary of a capability."""
    if capability in STANDALONE:
        return STANDALONE[capability]["role"]
    return f"{capability} capability"
