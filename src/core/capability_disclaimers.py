# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Capability Disclaimers
======================

Mandatory disclaimers shown when a guarded capability is activated.
Each disclaimer includes:
  - Capability-specific risk acknowledgment
  - Non-liability notice for Avery Logic Works
  - LLM accuracy warning (AI can get things wrong — verify important answers)
  - Reminder that the audit system tracks how answers were arrived at

The user must acknowledge the disclaimer before the capability dialog opens.
Once acknowledged per-session, the disclaimer won't reappear for that capability
until the application is restarted.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QScrollArea, QWidget,
)


# ═══════════════════════════════════════════════════════════════════════════════
# LLM ACCURACY WARNING — shown in every disclaimer
# ═══════════════════════════════════════════════════════════════════════════════

LLM_ACCURACY_WARNING = (
    "AI ACCURACY NOTICE\n"
    "AI can get things wrong. This is true for all LLMs, including this one.\n"
    "Please double-check answers when they matter — especially for legal, medical,\n"
    "financial, security, or code-related decisions.\n"
    "\n"
    "Command Nexus includes an audit system that records how the AI arrived at\n"
    "its answers. You can review the audit trail to see whether the AI actually\n"
    "did research, used sources, or answered from its own training data alone.\n"
    "If the AI didn't do research, you can ask it to actually do the research\n"
    "before trusting the answer.\n"
)

NON_LIABILITY_NOTICE = (
    "NO LIABILITY\n"
    "Avery Logic Works and Command Nexus(TM) are not liable for any decisions,\n"
    "actions, or outcomes resulting from AI-generated responses. Guardrails are\n"
    "in place to block prohibited requests, but no system is perfect. You are\n"
    "responsible for verifying AI output before acting on it.\n"
)


# ═══════════════════════════════════════════════════════════════════════════════
# CAPABILITY-SPECIFIC DISCLAIMER TEXT
# ═══════════════════════════════════════════════════════════════════════════════

CAPABILITY_DISCLAIMERS: dict[str, str] = {
    "Security Auditor": (
        "SECURITY AUDITOR — DISCLAIMER\n"
        "\n"
        "This capability provides defensive security analysis only. It cannot\n"
        "help infiltrate, breach, or hack systems you do not own or have explicit\n"
        "authorization to test.\n"
        "\n"
        "All security findings are advisory. Do not act on vulnerability reports\n"
        "without verifying them independently. Unauthorized scanning or testing\n"
        "of systems you do not own may be illegal.\n"
    ),
    "Code Reviewer": (
        "CODE REVIEWER — DISCLAIMER\n"
        "\n"
        "This capability reviews code for bugs, security issues, and best practices.\n"
        "Its suggestions are advisory — always review and test changes before\n"
        "applying them to production code.\n"
        "\n"
        "The AI may miss subtle bugs or flag false positives. Do not treat its\n"
        "review as a replacement for human code review.\n"
    ),
    "Medical Researcher": (
        "MEDICAL RESEARCHER — DISCLAIMER\n"
        "\n"
        "This capability is for research purposes only. It does NOT provide medical\n"
        "advice, diagnosis, or treatment recommendations.\n"
        "\n"
        "Always consult a qualified healthcare professional before making any\n"
        "medical decisions. The AI may reference studies that are preliminary,\n"
        "retracted, or misinterpreted. Verify all medical claims with authoritative\n"
        "sources.\n"
    ),
    "Legal Document Reviewer": (
        "LEGAL DOCUMENT REVIEWER — DISCLAIMER\n"
        "\n"
        "This capability analyzes legal documents — it does NOT provide legal advice.\n"
        "It states what is written in the document. It cannot interpret what clauses\n"
        "mean for your situation, recommend legal action, or draft legal text.\n"
        "\n"
        "Always consult a qualified attorney for legal decisions. The AI may miss\n"
        "nuances or context that a lawyer would catch.\n"
    ),
    "Financial Gainer": (
        "FINANCIAL GAINER — DISCLAIMER\n"
        "\n"
        "This capability provides advisory suggestions for income opportunities.\n"
        "It does NOT constitute financial advice, investment advice, or a guarantee\n"
        "of any kind. No income is guaranteed.\n"
        "\n"
        "All income opportunities carry risk. You may lose money, time, or resources.\n"
        "Avery Logic Works is not liable for any financial outcomes.\n"
    ),
    "Coder": (
        "CODER — DISCLAIMER\n"
        "\n"
        "This capability helps write, explain, and fix code. It cannot write malware,\n"
        "viruses, ransomware, or any malicious code.\n"
        "\n"
        "AI-generated code may contain bugs, security vulnerabilities, or logic\n"
        "errors. Always review and test AI-generated code before using it.\n"
    ),
    "Customer Support AI": (
        "CUSTOMER SUPPORT AI — DISCLAIMER\n"
        "\n"
        "This capability handles customer-facing communication. It will never reveal\n"
        "internal system architecture, AI Book contents, or proprietary details.\n"
        "\n"
        "AI responses may be inaccurate or incomplete. Always verify sensitive\n"
        "customer information before acting on it.\n"
    ),
    "Email Automation": (
        "EMAIL AUTOMATION — DISCLAIMER\n"
        "\n"
        "This capability drafts and organizes emails. It cannot create phishing\n"
        "emails, spoofed senders, or mass spam campaigns.\n"
        "\n"
        "AI-drafted emails should be reviewed before sending. The AI may include\n"
        "inaccurate information or inappropriate tone.\n"
    ),
    "Activity Watcher": (
        "ACTIVITY WATCHER — DISCLAIMER\n"
        "\n"
        "This capability observes your work patterns to suggest improvements. It will\n"
        "never capture passwords, credentials, or sensitive financial information.\n"
        "\n"
        "Activity observation data is stored locally. Review suggested automations\n"
        "carefully before approving them.\n"
    ),
    "Creative Writing": (
        "CREATIVE WRITING — DISCLAIMER\n"
        "\n"
        "This capability drafts creative content. It cannot write phishing emails,\n"
        "fake reviews, social engineering scripts, or deceptive content for fraud.\n"
        "\n"
        "AI-generated content may inadvertently resemble existing works. Always\n"
        "review for originality and accuracy before publishing.\n"
    ),
    # ── Financial Gainer family ──
    "Crypto Scout": (
        "CRYPTO SCOUT — DISCLAIMER\n"
        "\n"
        "This capability provides crypto asset research only. It does NOT constitute\n"
        "financial advice, investment recommendations, or a guarantee of any kind.\n"
        "\n"
        "Crypto markets are extremely volatile and largely unregulated. You may lose\n"
        "your entire investment. Always do your own research and consult a qualified\n"
        "financial professional before making investment decisions."
    ),
    "Affiliate Strategist": (
        "AFFILIATE STRATEGIST — DISCLAIMER\n"
        "\n"
        "This capability helps plan affiliate marketing strategies. It does NOT\n"
        "guarantee any income or commission earnings.\n"
        "\n"
        "Affiliate marketing is subject to FTC disclosure requirements and platform\n"
        "terms of service. You are responsible for complying with all applicable\n"
        "laws and regulations. Avery Logic Works is not liable for any outcomes."
    ),
    "Click Commission Tracker": (
        "CLICK COMMISSION TRACKER — DISCLAIMER\n"
        "\n"
        "This capability tracks and estimates commission earnings. Estimates are\n"
        "based on your inputs and may not reflect actual earnings.\n"
        "\n"
        "Commission rates, platform terms, and payout structures can change without\n"
        "notice. Avery Logic Works is not liable for any discrepancies between\n"
        "estimates and actual earnings."
    ),
    "Sales Funnel Builder": (
        "SALES FUNNEL BUILDER — DISCLAIMER\n"
        "\n"
        "This capability helps design sales funnels. It does NOT guarantee any\n"
        "conversion rates, sales, or revenue.\n"
        "\n"
        "Marketing regulations vary by jurisdiction. Ensure compliance with consumer\n"
        "protection laws, FTC guidelines, and platform advertising policies.\n"
        "Avery Logic Works is not liable for any business outcomes."
    ),
    "Side Hustle Scout": (
        "SIDE HUSTLE SCOUT — DISCLAIMER\n"
        "\n"
        "This capability suggests side hustle and gig opportunities. It does NOT\n"
        "guarantee any income or success.\n"
        "\n"
        "Platform availability, rates, and requirements vary and may change.\n"
        "Always verify platform terms before committing time or resources.\n"
        "Avery Logic Works is not liable for any outcomes."
    ),
    "Skill Monetizer": (
        "SKILL MONETIZER — DISCLAIMER\n"
        "\n"
        "This capability helps identify ways to monetize your skills. It does NOT\n"
        "guarantee any income or business success.\n"
        "\n"
        "Market demand, pricing, and competition vary. You are responsible for\n"
        "evaluating opportunities and complying with applicable laws.\n"
        "Avery Logic Works is not liable for any financial outcomes."
    ),
    "Investment Researcher": (
        "INVESTMENT RESEARCHER — DISCLAIMER\n"
        "\n"
        "This capability provides investment research information. It does NOT\n"
        "constitute investment advice, recommendations, or a guarantee of returns.\n"
        "\n"
        "Past performance does not guarantee future results. All investments carry\n"
        "risk, including the potential loss of principal. Consult a qualified\n"
        "financial advisor before making investment decisions."
    ),
    "ROI Calculator": (
        "ROI CALCULATOR — DISCLAIMER\n"
        "\n"
        "This capability calculates return on investment estimates. Calculations\n"
        "are based on your inputs and assumptions, which may be inaccurate.\n"
        "\n"
        "ROI estimates are not financial advice. Actual results may differ\n"
        "significantly. Avery Logic Works is not liable for any financial decisions\n"
        "made based on these calculations."
    ),
    "Market Gap Finder": (
        "MARKET GAP FINDER — DISCLAIMER\n"
        "\n"
        "This capability helps identify potential market opportunities. It does NOT\n"
        "guarantee any business success or profitability.\n"
        "\n"
        "Market research is advisory only. You are responsible for validating\n"
        "opportunities independently before investing time or capital.\n"
        "Avery Logic Works is not liable for any business outcomes."
    ),
    "Negotiation Coach": (
        "NEGOTIATION COACH — DISCLAIMER\n"
        "\n"
        "This capability provides negotiation preparation and practice. It does NOT\n"
        "constitute legal advice or guarantee any negotiation outcome.\n"
        "\n"
        "Negotiation strategies may not be appropriate for every situation. Consult\n"
        "a qualified attorney for legal matters. Avery Logic Works is not liable\n"
        "for any outcomes resulting from negotiation strategies used."
    ),
    # ── Gaming ──
    "Game Companion": (
        "GAME COMPANION — DISCLAIMER\n"
        "\n"
        "This capability provides game strategy and companion play. It does NOT\n"
        "facilitate gambling, betting, or real-money wagering.\n"
        "\n"
        "Game strategies are advisory and may not guarantee wins. The AI cannot\n"
        "access live game data or play games on your behalf. Practice responsible\n"
        "gaming habits and take breaks."
    ),
    # ── Data & Development ──
    "Data Analyst Pro": (
        "DATA ANALYST PRO — DISCLAIMER\n"
        "\n"
        "This capability analyzes data and produces statistics. Calculations may\n"
        "contain errors — always verify results independently before using them\n"
        "for decisions.\n"
        "\n"
        "Data analysis output is advisory. Avery Logic Works is not liable for\n"
        "any decisions made based on AI-generated analysis."
    ),
    "Meeting Facilitator": (
        "MEETING FACILITATOR — DISCLAIMER\n"
        "\n"
        "This capability helps plan and facilitate meetings. It does NOT guarantee\n"
        "meeting outcomes or participant agreement.\n"
        "\n"
        "AI-generated agendas and action items are advisory. You are responsible\n"
        "for reviewing and adapting them to your specific context."
    ),
    # ── Memory Saver family ──
    "Memory Recorder": (
        "MEMORY RECORDER — DISCLAIMER\n"
        "\n"
        "This capability records your session activity. Recorded data is stored\n"
        "locally on your device.\n"
        "\n"
        "Be aware that session recordings may contain sensitive information.\n"
        "You are responsible for managing and securing your recorded data.\n"
        "Avery Logic Works does not transmit or store your recordings externally."
    ),
    "Session Replay": (
        "SESSION REPLAY — DISCLAIMER\n"
        "\n"
        "This capability replays past session recordings. Replays may contain\n"
        "sensitive information from previous sessions.\n"
        "\n"
        "Session data is stored locally. You are responsible for managing access\n"
        "to your replay data."
    ),
    "Smart Recall": (
        "SMART RECALL — DISCLAIMER\n"
        "\n"
        "This capability searches across all stored memory. Search results may\n"
        "include sensitive information from past sessions.\n"
        "\n"
        "Memory data is stored locally. You are responsible for managing what\n"
        "information is retained and searched."
    ),
    "Decision Tracker": (
        "DECISION TRACKER — DISCLAIMER\n"
        "\n"
        "This capability logs and tracks decisions you record. Decision logs are\n"
        "personal records and do not constitute professional advice.\n"
        "\n"
        "You are responsible for the accuracy of recorded decisions and any actions\n"
        "taken based on them."
    ),
    "Knowledge Archive": (
        "KNOWLEDGE ARCHIVE — DISCLAIMER\n"
        "\n"
        "This capability stores and organizes your knowledge locally. Archived\n"
        "content may contain sensitive information.\n"
        "\n"
        "You are responsible for managing and securing your archived knowledge.\n"
        "Avery Logic Works does not transmit your archives externally."
    ),
    "Habit Tracker": (
        "HABIT TRACKER — DISCLAIMER\n"
        "\n"
        "This capability tracks personal habits and routines. It does NOT make\n"
        "any health, medical, or psychological claims.\n"
        "\n"
        "Habit tracking is a personal productivity tool. Consult a healthcare\n"
        "professional for health-related advice."
    ),
    "Progress Journal": (
        "PROGRESS JOURNAL — DISCLAIMER\n"
        "\n"
        "This capability provides a personal journal for tracking progress. It does\n"
        "NOT guarantee any specific outcome or result.\n"
        "\n"
        "Journal entries are personal records. You are responsible for the content\n"
        "and any actions taken based on your reflections."
    ),
    "Context Keeper": (
        "CONTEXT KEEPER — DISCLAIMER\n"
        "\n"
        "This capability preserves and restores your work context between sessions.\n"
        "Saved context may contain sensitive information.\n"
        "\n"
        "Context data is stored locally. You are responsible for managing access\n"
        "to your saved context."
    ),
    "Audit Trail Builder": (
        "AUDIT TRAIL BUILDER — DISCLAIMER\n"
        "\n"
        "This capability builds audit trails of system activity. Audit trails may\n"
        "contain sensitive information about your work patterns and actions.\n"
        "\n"
        "Audit data is stored locally. You are responsible for managing and\n"
        "securing your audit trails, especially if used for compliance purposes."
    ),
    # ── Other capabilities ──
    "Translation Expert": (
        "TRANSLATION EXPERT — DISCLAIMER\n"
        "\n"
        "This capability provides AI-powered translations. Translations may contain\n"
        "errors, inaccuracies, or loss of nuance.\n"
        "\n"
        "Do not rely on AI translations for legal, medical, or critical business\n"
        "documents without human verification. Avery Logic Works is not liable for\n"
        "any consequences resulting from translation errors."
    ),
    "Fact Checker": (
        "FACT CHECKER — DISCLAIMER\n"
        "\n"
        "This capability helps verify claims and statements. Verification results\n"
        "are advisory and may not be definitive.\n"
        "\n"
        "The AI may not have access to the latest information or may interpret\n"
        "sources incorrectly. Always cross-reference with authoritative sources\n"
        "for critical decisions."
    ),
    "Voice Interface": (
        "VOICE INTERFACE — DISCLAIMER\n"
        "\n"
        "This capability processes voice input. Voice data is processed locally\n"
        "and is not transmitted externally.\n"
        "\n"
        "Voice recognition may produce errors. You are responsible for reviewing\n"
        "transcribed text before acting on it."
    ),
    "API Integrator": (
        "API INTEGRATOR — DISCLAIMER\n"
        "\n"
        "This capability helps plan API integrations. External API calls carry\n"
        "security and privacy risks.\n"
        "\n"
        "You are responsible for securing API keys, reviewing terms of service,\n"
        "and ensuring compliance with data protection regulations. Avery Logic\n"
        "Works is not liable for any outcomes from external API usage."
    ),
    "Competitive Analyst": (
        "COMPETITIVE ANALYST — DISCLAIMER\n"
        "\n"
        "This capability provides competitive intelligence analysis. Information\n"
        "may be incomplete, outdated, or inaccurate.\n"
        "\n"
        "Competitive analysis is advisory only. Verify all information\n"
        "independently before making business decisions based on it."
    ),
    "Spreadsheet Wizard": (
        "SPREADSHEET WIZARD — DISCLAIMER\n"
        "\n"
        "This capability helps create and analyze spreadsheets. Formulas and\n"
        "calculations may contain errors.\n"
        "\n"
        "Always verify formula results independently before using them for\n"
        "financial or business decisions."
    ),
    "Workflow Automator": (
        "WORKFLOW AUTOMATOR — DISCLAIMER\n"
        "\n"
        "This capability helps design workflow automations. Automated actions may\n"
        "have unintended effects.\n"
        "\n"
        "Always test automations in a safe environment before deploying.\n"
        "You are responsible for monitoring automated processes and any outcomes\n"
        "they produce."
    ),
    "Team Orchestrator": (
        "TEAM ORCHESTRATOR — DISCLAIMER\n"
        "\n"
        "This capability helps coordinate multi-AI workflows. Coordination is\n"
        "advisory and does not guarantee task completion.\n"
        "\n"
        "You are responsible for reviewing and approving all coordinated actions\n"
        "before execution."
    ),
    "Memory Bridge": (
        "MEMORY BRIDGE — DISCLAIMER\n"
        "\n"
        "This capability manages persistent memory across sessions. Stored memory\n"
        "may contain sensitive information.\n"
        "\n"
        "Memory data is stored locally. You are responsible for managing what\n"
        "information is retained."
    ),
    "Visual Canvas": (
        "VISUAL CANVAS — DISCLAIMER\n"
        "\n"
        "This capability provides visual workspace tools. AI-generated visual\n"
        "content may not meet professional design standards.\n"
        "\n"
        "Always review visual output before using it in professional or\n"
        "published materials."
    ),
    "Knowledge Base Builder": (
        "KNOWLEDGE BASE BUILDER — DISCLAIMER\n"
        "\n"
        "This capability helps build and organize knowledge bases. Content may\n"
        "contain inaccuracies or become outdated.\n"
        "\n"
        "You are responsible for verifying knowledge base content and keeping\n"
        "it up to date."
    ),
    "Calendar Manager": (
        "CALENDAR MANAGER — DISCLAIMER\n"
        "\n"
        "This capability helps manage schedules and calendars. Scheduling\n"
        "suggestions are advisory only.\n"
        "\n"
        "You are responsible for confirming appointments and managing your own\n"
        "schedule. Avery Logic Works is not liable for missed or incorrect\n"
        "scheduling."
    ),
    "Document Generator": (
        "DOCUMENT GENERATOR — DISCLAIMER\n"
        "\n"
        "This capability generates documents from templates and inputs. Generated\n"
        "documents may contain errors or inappropriate content.\n"
        "\n"
        "Always review generated documents before using them in professional,\n"
        "legal, or business contexts."
    ),
    "Presentation Builder": (
        "PRESENTATION BUILDER — DISCLAIMER\n"
        "\n"
        "This capability helps create presentations. AI-generated content may\n"
        "contain inaccuracies or design issues.\n"
        "\n"
        "Always review and customize presentations before presenting to an\n"
        "audience."
    ),
    "Accessibility Assistant": (
        "ACCESSIBILITY ASSISTANT — DISCLAIMER\n"
        "\n"
        "This capability provides accessibility support for content. Accessibility\n"
        "suggestions are advisory and may not cover all needs.\n"
        "\n"
        "You are responsible for ensuring compliance with applicable accessibility\n"
        "standards (ADA, WCAG, etc.) for your specific context."
    ),
    "Learning Path Creator": (
        "LEARNING PATH CREATOR — DISCLAIMER\n"
        "\n"
        "This capability creates educational learning paths. Learning paths are\n"
        "advisory and may not suit every learner's needs.\n"
        "\n"
        "You are responsible for evaluating and adapting learning paths for your\n"
        "specific educational context."
    ),
    "Smart Search": (
        "SMART SEARCH — DISCLAIMER\n"
        "\n"
        "This capability provides enhanced search functionality. Search results\n"
        "may be incomplete or outdated.\n"
        "\n"
        "Always verify critical information from search results with authoritative\n"
        "sources before acting on it."
    ),
    "Wellness Coach": (
        "WELLNESS COACH — DISCLAIMER\n"
        "\n"
        "This capability provides advisory wellness guidance only. It does NOT\n"
        "provide medical advice, diagnosis, or treatment recommendations.\n"
        "\n"
        "Always consult a qualified healthcare professional before making any\n"
        "medical decisions or starting a new fitness or nutrition program. The AI\n"
        "may suggest exercises or foods that are not appropriate for your individual\n"
        "health conditions. If you experience pain, discomfort, or distress, stop\n"
        "and seek professional help immediately.\n"
        "\n"
        "Crisis resources: 988 (US Suicide & Crisis Lifeline) or your local\n"
        "emergency number."
    ),
    "Content Strategist": (
        "CONTENT STRATEGIST — DISCLAIMER\n"
        "\n"
        "This capability helps plan and optimize content strategy. It does NOT\n"
        "publish, schedule, or automate social media posts without explicit approval.\n"
        "\n"
        "AI-generated content may contain inaccuracies, unverified claims, or\n"
        "inappropriate tone for your brand. Always review content before publishing.\n"
        "Ensure compliance with platform terms of service, FTC disclosure\n"
        "requirements, and copyright laws. Avery Logic Works is not liable for\n"
        "any outcomes from published content."
    ),
    # Phase 7 — new capability disclaimers
    "Task Scheduler": (
        "TASK SCHEDULER — DISCLAIMER\n\n"
        "This capability helps plan schedules and set reminders. It does NOT\n"
        "auto-schedule or modify calendars without confirmation. Always verify\n"
        "times and timezones before confirming."
    ),
    "Form Builder": (
        "FORM BUILDER — DISCLAIMER\n\n"
        "This capability helps design forms and surveys. It does NOT deploy\n"
        "or publish forms. Review all questions for clarity and privacy\n"
        "compliance before deployment."
    ),
    "Report Generator": (
        "REPORT GENERATOR — DISCLAIMER\n\n"
        "Reports are generated from provided data and context. The AI may\n"
        "make assumptions or miss nuances. Always verify report accuracy\n"
        "before distributing."
    ),
    "Invoice Processor": (
        "INVOICE PROCESSOR — DISCLAIMER\n\n"
        "This capability helps create and format invoices. It does NOT send\n"
        "invoices or process payments. Always verify calculations, tax rates,\n"
        "and payment terms before sending to clients."
    ),
    "Spreadsheet Analyst": (
        "SPREADSHEET ANALYST — DISCLAIMER\n\n"
        "This capability provides formula suggestions and analysis guidance.\n"
        "It does NOT modify your files. Always test formulas on a copy before\n"
        "applying to production data."
    ),
    "Data Visualizer": (
        "DATA VISUALIZER — DISCLAIMER\n\n"
        "This capability recommends visualization approaches and describes\n"
        "charts. It does NOT generate image files. Verify that the recommended\n"
        "visualization accurately represents your data."
    ),
    "Statistical Modeler": (
        "STATISTICAL MODELER — DISCLAIMER\n\n"
        "This capability provides statistical analysis guidance. Statistical\n"
        "results require proper interpretation. Always check assumptions and\n"
        "consult a statistician for critical decisions."
    ),
    "Trend Forecaster": (
        "TREND FORECASTER — DISCLAIMER\n\n"
        "Forecasts are estimates based on historical patterns. External events\n"
        "can invalidate projections. Never make business decisions solely on\n"
        "AI-generated forecasts without independent validation."
    ),
    "DevOps Assistant": (
        "DEVOPS ASSISTANT — DISCLAIMER\n\n"
        "This capability provides DevOps guidance and configuration templates.\n"
        "It does NOT execute deployments or modify infrastructure. Always test\n"
        "in staging first and have a rollback plan."
    ),
    "Database Manager": (
        "DATABASE MANAGER — DISCLAIMER\n\n"
        "This capability helps with SQL queries and schema design. It does NOT\n"
        "execute queries against your databases. Always backup before schema\n"
        "changes and test on development databases first."
    ),
    "Test Generator": (
        "TEST GENERATOR — DISCLAIMER\n\n"
        "Generated tests should be reviewed before adding to your test suite.\n"
        "The AI may not understand your full codebase context. Verify that\n"
        "tests cover the intended behavior."
    ),
    "Documentation Generator": (
        "DOCUMENTATION GENERATOR — DISCLAIMER\n\n"
        "Generated documentation should be reviewed for accuracy. The AI may\n"
        "not capture all edge cases or API behaviors. Never fabricate API\n"
        "endpoints or parameters that don't exist."
    ),
    "Script Writer": (
        "SCRIPT WRITER — DISCLAIMER\n\n"
        "Generated scripts are creative drafts. They may contain formatting\n"
        "issues or structural problems. Review and revise before production use."
    ),
    "Copy Editor": (
        "COPY EDITOR — DISCLAIMER\n\n"
        "Editing suggestions preserve the author's voice but may not catch\n"
        "every error. Always do a final manual proofread. The AI may flag\n"
        "factual claims that need your verification."
    ),
    "Podcast Planner": (
        "PODCAST PLANNER — DISCLAIMER\n\n"
        "This capability helps plan podcast episodes and structure shows.\n"
        "Content suggestions are advisory. Verify any factual claims made in\n"
        "episode content before publishing."
    ),
    "Brand Strategist": (
        "BRAND STRATEGIST — DISCLAIMER\n\n"
        "Brand strategy suggestions are advisory and based on general best\n"
        "practices. Market conditions and target audience specifics may require\n"
        "professional brand consulting for optimal results."
    ),
    "Presentation Coach": (
        "PRESENTATION COACH — DISCLAIMER\n\n"
        "Coaching feedback is advisory. Practice and rehearsal are essential\n"
        "for effective delivery. The AI cannot evaluate your actual delivery\n"
        "style or body language."
    ),
    "PR Assistant": (
        "PR ASSISTANT — DISCLAIMER\n\n"
        "This capability drafts PR content. It does NOT send to media. Always\n"
        "review for accuracy, legal compliance, and potential crisis implications\n"
        "before distribution."
    ),
    "Internal Comms Writer": (
        "INTERNAL COMMS WRITER — DISCLAIMER\n\n"
        "Drafted communications should be reviewed for tone, accuracy, and\n"
        "appropriate distribution. Flag sensitive information for legal or\n"
        "HR review before sending."
    ),
    "Academic Citation Manager": (
        "ACADEMIC CITATION MANAGER — DISCLAIMER\n\n"
        "Citation formatting is automated. Always verify against the actual\n"
        "source. Never fabricate sources, page numbers, or DOIs. Check\n"
        "your institution's specific citation requirements."
    ),
    "Patent Researcher": (
        "PATENT RESEARCHER — DISCLAIMER\n\n"
        "This capability provides patent research assistance only. It is NOT\n"
        "legal advice. Always consult a qualified patent attorney for filing,\n"
        "prosecution, or freedom-to-operate opinions."
    ),
    "Market Analyst": (
        "MARKET ANALYST — DISCLAIMER\n\n"
        "Market analysis is based on available information and estimates.\n"
        "TAM/SAM/SOM figures are approximations. Never guarantee market\n"
        "outcomes. Validate with primary research before making investment\n"
        "decisions."
    ),
    "Recipe Planner": (
        "RECIPE PLANNER — DISCLAIMER\n\n"
        "Recipe suggestions are general. Always check for allergens and\n"
        "dietary restrictions. Consult a nutritionist or doctor for specific\n"
        "dietary needs or medical conditions."
    ),
    "Travel Planner": (
        "TRAVEL PLANNER — DISCLAIMER\n\n"
        "Travel plans are advisory. This capability does NOT book trips.\n"
        "Always verify visa requirements, safety advisories, and booking\n"
        "details before traveling."
    ),
    "Event Planner": (
        "EVENT PLANNER — DISCLAIMER\n\n"
        "Event planning suggestions are advisory. Verify venue availability,\n"
        "vendor pricing, and permit requirements independently. The AI cannot\n"
        "guarantee event success."
    ),
    "Personal Finance Manager": (
        "PERSONAL FINANCE MANAGER — DISCLAIMER\n\n"
        "This capability provides general budgeting guidance. It is NOT\n"
        "financial advice. Never make investment decisions based solely on\n"
        "AI suggestions. Consult a qualified financial advisor."
    ),
    "Privacy Compliance Checker": (
        "PRIVACY COMPLIANCE CHECKER — DISCLAIMER\n\n"
        "This capability provides compliance guidance. It is NOT legal advice.\n"
        "Privacy regulations vary by jurisdiction and change frequently.\n"
        "Always consult a privacy attorney for compliance decisions."
    ),
    "Data Governance Advisor": (
        "DATA GOVERNANCE ADVISOR — DISCLAIMER\n\n"
        "Governance frameworks are advisory. Implement based on your\n"
        "organization's specific needs and regulatory requirements.\n"
        "Consult data governance professionals for enterprise implementations."
    ),
    "Curriculum Designer": (
        "CURRICULUM DESIGNER — DISCLAIMER\n\n"
        "Curriculum designs are advisory. Verify alignment with educational\n"
        "standards, accreditation requirements, and institutional policies.\n"
        "Adapt to your specific learner needs."
    ),
    "Exam Prep Coach": (
        "EXAM PREP COACH — DISCLAIMER\n\n"
        "Study plans are advisory. The AI cannot guarantee exam outcomes.\n"
        "Adapt the plan to your learning style and schedule. Consult your\n"
        "instructor for subject-specific guidance."
    ),
}


# Capabilities that require a disclaimer before activation
GUARDED_CAPABILITIES = set(CAPABILITY_DISCLAIMERS.keys())


# Map dialog class names to capability names for disclaimer lookup.
# This is the single source of truth — both forge_window.py and capability_actions.py
# import from here to avoid duplication drift.
DIALOG_TO_CAPABILITY: dict[str, str] = {
    "SecurityAuditorDialog": "Security Auditor",
    "CodeReviewerDialog": "Code Reviewer",
    "MedicalResearcherDialog": "Medical Researcher",
    "LegalDocumentReviewerDialog": "Legal Document Reviewer",
    "FinancialGainerDialog": "Financial Gainer",
    "CodingCapabilityDialog": "Coder",
    "EmailAutomationDialog": "Email Automation",
    "ActivityWatcherDialog": "Activity Watcher",
    "CreativeWriterCapabilityDialog": "Creative Writing",
    "CustomerSupportDialog": "Customer Support AI",
    # Financial Gainer family
    "CryptoScoutDialog": "Crypto Scout",
    "AffiliateStrategistDialog": "Affiliate Strategist",
    "ClickCommissionDialog": "Click Commission Tracker",
    "SalesFunnelDialog": "Sales Funnel Builder",
    "SideHustleScoutDialog": "Side Hustle Scout",
    "SkillMonetizerDialog": "Skill Monetizer",
    "InvestmentResearcherDialog": "Investment Researcher",
    "ROICalculatorDialog": "ROI Calculator",
    "MarketGapFinderDialog": "Market Gap Finder",
    "NegotiationCoachDialog": "Negotiation Coach",
    # Gaming
    "GameCompanionDialog": "Game Companion",
    # Data & Development
    "DataAnalystDialog": "Data Analyst Pro",
    "MeetingFacilitatorDialog": "Meeting Facilitator",
    # Memory Saver family
    "MemoryRecorderDialog": "Memory Recorder",
    "SessionReplayDialog": "Session Replay",
    "SmartRecallDialog": "Smart Recall",
    "DecisionTrackerDialog": "Decision Tracker",
    "KnowledgeArchiveDialog": "Knowledge Archive",
    "HabitTrackerDialog": "Habit Tracker",
    "ProgressJournalDialog": "Progress Journal",
    "ContextKeeperDialog": "Context Keeper",
    "AuditTrailBuilderDialog": "Audit Trail Builder",
    # Other capabilities
    "TranslationExpertDialog": "Translation Expert",
    "FactCheckerDialog": "Fact Checker",
    "VoiceInterfaceDialog": "Voice Interface",
    "APIIntegratorDialog": "API Integrator",
    "CompetitiveAnalystDialog": "Competitive Analyst",
    "SpreadsheetWizardDialog": "Spreadsheet Wizard",
    "WorkflowAutomatorDialog": "Workflow Automator",
    "TeamOrchestratorDialog": "Team Orchestrator",
    "MemoryBridgeDialog": "Memory Bridge",
    "VisualCanvasDialog": "Visual Canvas",
    "KnowledgeBaseDialog": "Knowledge Base Builder",
    "CalendarManagerDialog": "Calendar Manager",
    "DocumentGeneratorDialog": "Document Generator",
    "PresentationBuilderDialog": "Presentation Builder",
    "AccessibilityAssistantDialog": "Accessibility Assistant",
    "LearningPathCreatorDialog": "Learning Path Creator",
    "SmartSearchDialog": "Smart Search",
    # Phase 6 — Wellness & Content Strategy
    "WellnessCoachDialog": "Wellness Coach",
    "ContentStrategistDialog": "Content Strategist",
    # Phase 7 — new capability dialogs
    "TaskSchedulerDialog": "Task Scheduler",
    "FormBuilderDialog": "Form Builder",
    "ReportGeneratorDialog": "Report Generator",
    "InvoiceProcessorDialog": "Invoice Processor",
    "SpreadsheetAnalystDialog": "Spreadsheet Analyst",
    "DataVisualizerDialog": "Data Visualizer",
    "StatisticalModelerDialog": "Statistical Modeler",
    "TrendForecasterDialog": "Trend Forecaster",
    "DevOpsAssistantDialog": "DevOps Assistant",
    "DatabaseManagerDialog": "Database Manager",
    "TestGeneratorDialog": "Test Generator",
    "DocumentationGeneratorDialog": "Documentation Generator",
    "ScriptWriterDialog": "Script Writer",
    "CopyEditorDialog": "Copy Editor",
    "PodcastPlannerDialog": "Podcast Planner",
    "BrandStrategistDialog": "Brand Strategist",
    "PresentationCoachDialog": "Presentation Coach",
    "PRAssistantDialog": "PR Assistant",
    "InternalCommsWriterDialog": "Internal Comms Writer",
    "AcademicCitationManagerDialog": "Academic Citation Manager",
    "PatentResearcherDialog": "Patent Researcher",
    "MarketAnalystDialog": "Market Analyst",
    "RecipePlannerDialog": "Recipe Planner",
    "TravelPlannerDialog": "Travel Planner",
    "EventPlannerDialog": "Event Planner",
    "PersonalFinanceManagerDialog": "Personal Finance Manager",
    "PrivacyComplianceCheckerDialog": "Privacy Compliance Checker",
    "DataGovernanceAdvisorDialog": "Data Governance Advisor",
    "CurriculumDesignerDialog": "Curriculum Designer",
    "ExamPrepCoachDialog": "Exam Prep Coach",
}


# Track which disclaimers have been acknowledged this session
_session_acknowledged: set[str] = set()


def is_disclaimer_acknowledged(capability: str) -> bool:
    """Check if a capability's disclaimer has been acknowledged this session."""
    return capability in _session_acknowledged


def reset_session_acknowledgments():
    """Reset all session acknowledgments (called on app restart)."""
    _session_acknowledged.clear()


def _build_disclaimer_text(capability: str) -> str:
    """Build the full disclaimer text for a capability."""
    cap_text = CAPABILITY_DISCLAIMERS.get(capability, "")
    parts = []
    if cap_text:
        parts.append(cap_text)
    parts.append(LLM_ACCURACY_WARNING)
    parts.append(NON_LIABILITY_NOTICE)
    parts.append(
        "By clicking 'I Understand & Continue', you acknowledge that you have read\n"
        "and understood this disclaimer."
    )
    return "\n".join(parts)


class CapabilityDisclaimerDialog(QDialog):
    """Mandatory disclaimer dialog shown before a guarded capability opens."""

    def __init__(self, capability: str, parent=None):
        super().__init__(parent)
        self._capability = capability
        self._accepted = False
        self.setWindowTitle(f"{capability} — Disclaimer")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(520)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel(f"⚠ {self._capability} — Please Read Before Continuing")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #d97706; "
            "padding: 16px;  "
            "border-bottom: 2px solid #fcd34d;"
        )
        layout.addWidget(header)

        # Scrollable disclaimer text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none;  }"
            "QScrollBar:vertical { background: #161b22; width: 10px; }"
            "QScrollBar::handle:vertical { background: #30363d; border-radius: 5px; }"
        )

        content = QWidget()
        content.setStyleSheet("")
        content_layout = QVBoxLayout(content)

        disclaimer_label = QLabel(_build_disclaimer_text(self._capability))
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setTextFormat(Qt.TextFormat.PlainText)
        disclaimer_label.setStyleSheet(
            "color: #c9d1d9; font-size: 12px; padding: 20px; "
            "font-family: 'Consolas', 'Courier New', monospace;"
        )
        disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(disclaimer_label)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Bottom bar
        bottom = QWidget()
        bottom.setStyleSheet(
            " border-top: 2px solid #fcd34d; padding: 12px;"
        )
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setSpacing(8)

        self.ack_checkbox = QCheckBox(
            "I have read and understood this disclaimer. I understand that AI can "
            "get things wrong and that Avery Logic Works is not liable for outcomes."
        )
        self.ack_checkbox.setWordWrap(True)
        self.ack_checkbox.setStyleSheet(
            "QCheckBox { color: #c9d1d9; font-size: 12px; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        self.ack_checkbox.toggled.connect(self._on_checkbox_toggled)
        bottom_layout.addWidget(self.ack_checkbox)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            "QPushButton {  color: #f85149; "
            "border: 1px solid #f85149; border-radius: 6px; padding: 8px 20px; "
            "font-size: 13px; font-weight: bold; }"
        )
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.continue_btn = QPushButton("I Understand & Continue")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(
            "QPushButton { background-color: #d97706; color: white; "
            "border: none; border-radius: 6px; padding: 8px 24px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:disabled {  color: #484f58; }"
        )
        self.continue_btn.clicked.connect(self._on_continue)
        btn_row.addWidget(self.continue_btn)

        bottom_layout.addLayout(btn_row)
        layout.addWidget(bottom)

    def _on_checkbox_toggled(self, checked: bool):
        self.continue_btn.setEnabled(checked)
        if checked:
            self.continue_btn.setStyleSheet(
                "QPushButton { background-color: #059669; color: white; "
                "border: none; border-radius: 6px; padding: 8px 24px; "
                "font-size: 13px; font-weight: bold; }"
            )
        else:
            self.continue_btn.setStyleSheet(
                "QPushButton { background-color: #d97706; color: white; "
                "border: none; border-radius: 6px; padding: 8px 24px; "
                "font-size: 13px; font-weight: bold; }"
                "QPushButton:disabled {  color: #484f58; }"
            )

    def _on_continue(self):
        self._accepted = True
        _session_acknowledged.add(self._capability)
        self.accept()

    @property
    def was_accepted(self) -> bool:
        return self._accepted


def show_capability_disclaimer(capability: str, parent=None) -> bool:
    """Show the disclaimer dialog for a capability.

    Returns True if:
      - The disclaimer was already acknowledged this session, OR
      - The user acknowledged it just now.
    Returns False if the user cancelled.

    For high-risk capabilities, a persistent Terms of Use dialog is shown first
    (once per capability, persisted via marker file). Then the standard
    session-based disclaimer popup is shown.
    """
    if capability not in GUARDED_CAPABILITIES:
        return True

    # Tier 2: High-risk capabilities get a persistent Terms of Use dialog first
    if capability in HIGH_RISK_CAPABILITIES:
        if not CapabilityTermsDialog.has_been_accepted(capability):
            terms_dlg = CapabilityTermsDialog(capability, parent)
            terms_dlg.exec()
            if not terms_dlg.was_accepted:
                return False

    # Tier 1: Standard session-based disclaimer popup
    if is_disclaimer_acknowledged(capability):
        return True
    dlg = CapabilityDisclaimerDialog(capability, parent)
    dlg.exec()
    return dlg.was_accepted


# ═══════════════════════════════════════════════════════════════════════════════
# HIGH-RISK CAPABILITIES — Tier 2: get dedicated persistent Terms of Use dialog
# ═══════════════════════════════════════════════════════════════════════════════

HIGH_RISK_CAPABILITIES: set[str] = {
    "Financial Gainer",
    "Crypto Scout",
    "Investment Researcher",
    "ROI Calculator",
    "Side Hustle Scout",
    "Skill Monetizer",
    "Affiliate Strategist",
    "Click Commission Tracker",
    "Sales Funnel Builder",
    "Market Gap Finder",
    "Negotiation Coach",
    "Legal Document Reviewer",
    "Medical Researcher",
    "Security Auditor",
    "Code Reviewer",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CAPABILITY-SPECIFIC TERMS OF USE TEXT (Tier 2)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_terms_text(capability: str) -> str:
    """Build the full Terms of Use text for a high-risk capability."""
    cap_disclaimer = CAPABILITY_DISCLAIMERS.get(capability, "")
    risk_category = _RISK_CATEGORIES.get(capability, "high-risk")
    parts = [
        f"COMMAND NEXUS — {capability.upper()} TERMS OF USE",
        "=" * 60,
        "",
        f"Last updated: 2026",
        f"Avery Logic Works — Command Nexus(TM)",
        "",
        f"Risk Category: {risk_category.upper()}",
        "",
        "By using this capability, you agree to the following terms:",
        "",
        "1. ADVISORY NATURE",
        "-" * 40,
    ]

    if cap_disclaimer:
        parts.append(cap_disclaimer)
        parts.append("")

    parts.extend([
        "2. NO GUARANTEE",
        "-" * 40,
        "Avery Logic Works does not guarantee any specific outcome, result,",
        "income, accuracy, or performance from using this capability. All",
        "outputs are advisory and generated by AI, which can be incorrect.",
        "",
        "3. USER RESPONSIBILITY",
        "-" * 40,
        "You are solely responsible for:",
        "  - Verifying all AI-generated output before acting on it",
        "  - Complying with all applicable laws and regulations",
        "  - Protecting your own data, credentials, and privacy",
        "  - Any decisions made based on AI-generated content",
        "  - Any financial, legal, medical, or business outcomes",
        "",
        "4. NO LIABILITY",
        "-" * 40,
        "To the maximum extent permitted by law, Avery Logic Works and",
        "Command Nexus(TM) shall not be liable for any direct, indirect,",
        "incidental, special, consequential, or punitive damages, or any",
        "loss of profits, revenue, data, or capital arising from the use",
        "of this capability.",
        "",
        "5. THIRD-PARTY PLATFORMS",
        "-" * 40,
        "This capability may reference third-party platforms, services, or",
        "tools. Avery Logic Works is not affiliated with these third parties",
        "and is not responsible for their terms, policies, or availability.",
        "You are responsible for reviewing and complying with third-party",
        "terms of service.",
        "",
        "6. ACCEPTABLE USE",
        "-" * 40,
        "This capability must be used for lawful, ethical purposes only.",
        "Misuse includes but is not limited to:",
        "  - Using outputs for fraud, deception, or illegal activities",
        "  - Attempting to bypass safety measures or guardrails",
        "  - Using outputs without required disclosures (e.g., FTC)",
        "  - Redistributing AI-generated content as professional advice",
        "",
        "7. CHANGES TO TERMS",
        "-" * 40,
        "Avery Logic Works reserves the right to update these terms at any",
        "time. Continued use of this capability after changes constitutes",
        "acceptance of the updated terms.",
        "",
        "8. GOVERNING LAW",
        "-" * 40,
        "These terms shall be governed by the laws of the jurisdiction in",
        "which Avery Logic Works is registered.",
        "",
        "=" * 60,
        "For questions: support@averylogicworks.com",
        "=" * 60,
    ])
    return "\n".join(parts)


_RISK_CATEGORIES: dict[str, str] = {
    "Financial Gainer": "financial",
    "Crypto Scout": "financial — extreme volatility",
    "Investment Researcher": "financial — investment risk",
    "ROI Calculator": "financial — estimation accuracy",
    "Side Hustle Scout": "financial — income not guaranteed",
    "Skill Monetizer": "financial — market dependent",
    "Affiliate Strategist": "financial / marketing — FTC compliance",
    "Click Commission Tracker": "financial — earnings not guaranteed",
    "Sales Funnel Builder": "marketing — no guaranteed conversions",
    "Market Gap Finder": "business — no guaranteed success",
    "Negotiation Coach": "legal-adjacent — not legal advice",
    "Legal Document Reviewer": "legal — not legal advice",
    "Medical Researcher": "medical — not medical advice",
    "Security Auditor": "security — defensive use only",
    "Code Reviewer": "code quality — not a replacement for human review",
}


class CapabilityTermsDialog(QDialog):
    """Full Terms of Use dialog for high-risk capabilities.

    Similar to GovernanceDisclaimerDialog but capability-specific.
    Acceptance is persisted via marker file so it's shown once per capability.
    """

    def __init__(self, capability: str, parent=None):
        super().__init__(parent)
        self._capability = capability
        self._accepted = False
        self.setWindowTitle(f"{capability} — Terms of Use")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel(f"COMMAND NEXUS — {self._capability}")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #f85149; "
            "padding: 20px;  "
            "border-bottom: 2px solid #da3633;"
        )
        layout.addWidget(header)

        subheader = QLabel("Terms of Use — High-Risk Capability")
        subheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subheader.setStyleSheet(
            "font-size: 14px; color: #8b949e; padding: 8px; "
            " border-bottom: 1px solid #30363d;"
        )
        layout.addWidget(subheader)

        # Scrollable terms text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none;  }"
            "QScrollBar:vertical { background: #161b22; width: 10px; }"
            "QScrollBar::handle:vertical { background: #30363d; border-radius: 5px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        content = QWidget()
        content.setStyleSheet("")
        content_layout = QVBoxLayout(content)

        terms_label = QLabel(_build_terms_text(self._capability))
        terms_label.setWordWrap(True)
        terms_label.setTextFormat(Qt.TextFormat.PlainText)
        terms_label.setStyleSheet(
            "color: #c9d1d9; font-size: 13px; padding: 20px; "
            "font-family: 'Consolas', 'Courier New', monospace;"
        )
        terms_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(terms_label)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Bottom bar
        bottom = QWidget()
        bottom.setStyleSheet(
            " border-top: 2px solid #da3633; padding: 12px;"
        )
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setSpacing(8)

        self._agree_checkbox = QCheckBox(
            f"I have read and agree to the Terms of Use for {self._capability}. "
            "I understand this is a high-risk capability and that Avery Logic Works "
            "is not liable for any outcomes."
        )
        self._agree_checkbox.setWordWrap(True)
        self._agree_checkbox.setStyleSheet(
            "QCheckBox { color: #c9d1d9; font-size: 12px; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        self._agree_checkbox.toggled.connect(self._on_checkbox_toggled)
        bottom_layout.addWidget(self._agree_checkbox)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._decline_btn = QPushButton("Decline & Cancel")
        self._decline_btn.setStyleSheet(
            "QPushButton {  color: #f85149; "
            "border: 1px solid #f85149; border-radius: 6px; padding: 8px 20px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da363340; }"
        )
        self._decline_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._decline_btn)

        self._accept_btn = QPushButton("Accept & Continue")
        self._accept_btn.setEnabled(False)
        self._accept_btn.setStyleSheet(
            "QPushButton { background-color: #1f6feb; color: white; "
            "border: none; border-radius: 6px; padding: 8px 24px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #58a6ff; }"
            "QPushButton:disabled {  color: #484f58; }"
        )
        self._accept_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self._accept_btn)

        bottom_layout.addLayout(btn_row)
        layout.addWidget(bottom)

    def _on_checkbox_toggled(self, checked: bool):
        self._accept_btn.setEnabled(checked)

    def _on_accept(self):
        self._accepted = True
        marker = Path.home() / ".command_nexus" / f"terms_{self._capability.replace(' ', '_').lower()}.accepted"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        self.accept()

    @property
    def was_accepted(self) -> bool:
        return self._accepted

    @staticmethod
    def has_been_accepted(capability: str) -> bool:
        """Check if the Terms of Use for this capability has been accepted."""
        marker = Path.home() / ".command_nexus" / f"terms_{capability.replace(' ', '_').lower()}.accepted"
        return marker.exists()
