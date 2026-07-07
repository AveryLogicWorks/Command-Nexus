# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Easy Mode — Child-friendly quick-start system for every Command Nexus capability.

Every capability gets:
  - An emoji icon and color
  - A simple 2-3 word title
  - One plain-English question
  - 4 example prompts a 7-year-old could understand

The SimpleCapabilityLauncher is a one-box-one-button dialog that lets
anyone use any capability without knowing anything about AI.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QWidget, QScrollArea, QFrame,
)

from ...core.settings_manager import SettingsManager


# ===========================================================================
# Quick-start registry — one entry per capability (user-facing names)
# ===========================================================================

CAPABILITY_QUICK_START: dict[str, dict] = {
    # ── Chat & Communication ──
    "Chat Companion": {"emoji": "\U0001F4AC", "color": "#1a73e8", "title": "Let's Talk!", "question": "What do you want to talk about?", "examples": ["Tell me a fun fact", "What's the weather like?", "Help me think through a problem", "Tell me a joke"]},
    "Chat": {"emoji": "\U0001F4AC", "color": "#1a73e8", "title": "Let's Talk!", "question": "What do you want to talk about?", "examples": ["Tell me a fun fact", "What's the weather like?", "Help me think through a problem", "Tell me a joke"]},
    "Customer Support AI": {"emoji": "\U0001F91D", "color": "#1a73e8", "title": "Help Desk", "question": "What does the customer need help with?", "examples": ["Customer can't log in", "Refund request for order #123", "How do I reset my password?", "Billing question about my plan"]},
    "Customer Support Agent": {"emoji": "\U0001F91D", "color": "#1a73e8", "title": "Help Desk", "question": "What does the customer need help with?", "examples": ["Customer can't log in", "Refund request for order #123", "How do I reset my password?", "Billing question about my plan"]},
    "Email Sifter & Responder": {"emoji": "\u2709\ufe0f", "color": "#1a73e8", "title": "Email Helper", "question": "What do you want to do with emails?", "examples": ["Sort my inbox by importance", "Draft a reply to my boss", "Find urgent emails", "Create a template for follow-ups"]},
    "Email Automation": {"emoji": "\u2709\ufe0f", "color": "#1a73e8", "title": "Email Helper", "question": "What do you want to do with emails?", "examples": ["Sort my inbox by importance", "Draft a reply to my boss", "Find urgent emails", "Create a template for follow-ups"]},

    # ── Research & Search ──
    "Research Assistant": {"emoji": "\U0001F50D", "color": "#0d6efd", "title": "Research Time!", "question": "What do you want to learn about?", "examples": ["Find information about space", "Compare iPhone vs Android", "What are the latest AI news?", "Research the best gaming laptops"]},
    "Academic Researcher": {"emoji": "\U0001F4DA", "color": "#0d6efd", "title": "Research Time!", "question": "What topic are you studying?", "examples": ["Find papers on climate change", "Research the causes of WWI", "Gather sources for my essay", "Find evidence about exercise and health"]},
    "Smart Search": {"emoji": "\U0001F50E", "color": "#0d6efd", "title": "Search Everything", "question": "What are you looking for?", "examples": ["Find documents about my project", "Search for similar content to this", "Find all my notes from last week", "Look up this topic across my files"]},
    "Fact Checker": {"emoji": "\u2705", "color": "#0d6efd", "title": "Is It True?", "question": "What claim do you want to check?", "examples": ["Is it true that sharks don't sleep?", "Check this news article for accuracy", "Verify this statistic about climate", "Is this quote real?"]},
    "Business Intelligence Analyst": {"emoji": "\U0001F4CA", "color": "#0d6efd", "title": "Business Insights", "question": "What business data do you want to understand?", "examples": ["Show me sales trends this quarter", "Which products are growing?", "Summarize our customer data", "What are the top opportunities?"]},

    # ── Coding ──
    "Coding Assistant": {"emoji": "\U0001F4BB", "color": "#2ea043", "title": "Code Helper", "question": "What do you want to code?", "examples": ["Explain what this code does", "Fix this bug in my program", "Write a Python function to sort numbers", "Help me build a website"]},
    "IT Operations Agent": {"emoji": "\U0001F5A5\ufe0f", "color": "#2ea043", "title": "Tech Support", "question": "What tech problem are you having?", "examples": ["My computer is running slow", "How do I check my network status?", "Diagnose this error message", "Set up a new server"]},
    "Code Reviewer": {"emoji": "\U0001F501", "color": "#2ea043", "title": "Code Checkup", "question": "What code do you want reviewed?", "examples": ["Review my code for bugs", "Check this for security issues", "Suggest improvements for this function", "Find performance problems"]},

    # ── Creative ──
    "Creative Writer": {"emoji": "\u270d\ufe0f", "color": "#8957e5", "title": "Let's Write!", "question": "What do you want to write?", "examples": ["Write a story about a dragon", "Draft a poem about the ocean", "Create a script for a video", "Help me brainstorm ideas for a song"]},
    "Marketing Generator": {"emoji": "\U0001F4E3", "color": "#8957e5", "title": "Marketing Helper", "question": "What do you want to promote?", "examples": ["Write a social media post about my product", "Create an ad for my sale", "Draft a newsletter about new features", "Slogans for my coffee shop"]},

    # ── Learning & Education ──
    "Learning Tutor": {"emoji": "\U0001F4A1", "color": "#f0883e", "title": "Let's Learn!", "question": "What do you want to learn?", "examples": ["Explain fractions step by step", "Quiz me on world capitals", "Help me understand photosynthesis", "Make a study sheet for my test"]},
    "Classroom Tutor": {"emoji": "\U0001F3EB", "color": "#f0883e", "title": "Let's Learn!", "question": "What subject are you studying?", "examples": ["Explain how gravity works", "Quiz me on Spanish verbs", "Help me solve this math problem", "Create a practice test for history"]},
    "Assignment Grader": {"emoji": "\U0001F4DD", "color": "#f0883e", "title": "Grade My Work", "question": "What do you want graded?", "examples": ["Grade this essay against the rubric", "Check my math homework", "Review my code assignment", "Give feedback on my presentation"]},
    "Lesson Planner": {"emoji": "\U0001F4C6", "color": "#f0883e", "title": "Plan a Lesson", "question": "What do you want to teach?", "examples": ["Plan a lesson about the solar system", "Create activities for learning fractions", "Outline a 5-day unit on poetry", "Sequence topics for beginner Python"]},
    "Language Coach": {"emoji": "\U0001F310", "color": "#f0883e", "title": "Language Practice", "question": "What language are you practicing?", "examples": ["Practice Spanish conversation with me", "Correct my French pronunciation", "Build my vocabulary for Japanese", "Translate this sentence to German"]},
    "Accessibility Aide": {"emoji": "\U0001F9E0", "color": "#f0883e", "title": "Make It Easier", "question": "How can I make this easier for you?", "examples": ["Summarize this in simpler words", "Make this text bigger and clearer", "Read this document aloud", "Convert this to plain language"]},
    "Learning Path Creator": {"emoji": "\U0001F9ED", "color": "#f0883e", "title": "Learning Path", "question": "What do you want to master?", "examples": ["Create a learning path for Python", "Design a 4-week study plan for algebra", "Build a curriculum for beginner guitar", "Plan assessments for this course"]},
    "Study Coach": {"emoji": "\U0001F393", "color": "#f0883e", "title": "Study Buddy", "question": "What are you studying for?", "examples": ["Make me a study plan for finals", "Create flashcards for biology", "Quiz me on history dates", "Help me prep for my math exam"]},
    "Plagiarism Checker": {"emoji": "\U0001F50D", "color": "#f0883e", "title": "Originality Check", "question": "What text do you want to check?", "examples": ["Check this essay for plagiarism", "Is this text copied from somewhere?", "Check similarity of this paragraph", "Find sources for this passage"]},

    # ── Organization & Planning ──
    "Personal Organizer": {"emoji": "\U0001F4CB", "color": "#d29922", "title": "Get Organized", "question": "What do you want to organize?", "examples": ["Make a to-do list for today", "Remind me about my appointment", "Organize my tasks by priority", "Create a grocery list"]},
    "Task / Project Manager": {"emoji": "\U0001F4C5", "color": "#d29922", "title": "Project Planner", "question": "What project are you working on?", "examples": ["Break this project into steps", "Track progress on my app", "What are my deadlines this week?", "Create a milestone plan"]},
    "Strategic Planner": {"emoji": "\U0001F3AF", "color": "#d29922", "title": "Big Picture Planner", "question": "What's your big goal?", "examples": ["Plan a 1-year strategy for my business", "Map out long-term goals", "Identify risks and opportunities", "Build a phased action plan"]},
    "Workflow Automator": {"emoji": "\u2699\ufe0f", "color": "#d29922", "title": "Automate It", "question": "What repetitive task do you want to automate?", "examples": ["Automate my weekly report", "Create a workflow for new emails", "Build an approval process", "Set up a when-this-happens-do-that chain"]},
    "Calendar Manager": {"emoji": "\U0001F4C6", "color": "#d29922", "title": "Schedule Helper", "question": "What do you need scheduled?", "examples": ["Find the best time for a meeting", "Detect conflicts in my schedule", "Suggest focus blocks for deep work", "Plan my week for maximum productivity"]},
    "Meeting Facilitator": {"emoji": "\U0001F4DD", "color": "#d29922", "title": "Meeting Helper", "question": "What meeting do you need help with?", "examples": ["Create an agenda for my team meeting", "Take notes during this call", "Extract action items from our discussion", "Plan follow-ups after the meeting"]},
    "Meeting Scribe": {"emoji": "\U0001F4DD", "color": "#d29922", "title": "Meeting Notes", "question": "What was discussed in the meeting?", "examples": ["Summarize what we talked about", "Track decisions from the meeting", "List action items from today's call", "Create clean meeting notes"]},

    # ── Documents ──
    "Document Processor": {"emoji": "\U0001F4C4", "color": "#6e7681", "title": "Document Helper", "question": "What do you want to do with this document?", "examples": ["Summarize this document", "Extract the key points", "Find action items in this text", "Classify what type of document this is"]},
    "Document Generator": {"emoji": "\U0001F4DD", "color": "#6e7681", "title": "Create a Document", "question": "What kind of document do you need?", "examples": ["Create a professional report", "Make a proposal from this template", "Format this as a letter", "Generate a PDF with my branding"]},
    "Presentation Builder": {"emoji": "\U0001F4A1", "color": "#6e7681", "title": "Make Slides", "question": "What do you want to present?", "examples": ["Create slides from this outline", "Suggest visuals for my presentation", "Generate speaker notes", "Make a 10-slide deck about my topic"]},
    "Translation Expert": {"emoji": "\U0001F310", "color": "#6e7681", "title": "Translate It", "question": "What do you want translated?", "examples": ["Translate this to Spanish", "Keep the formal tone in French", "Translate this document to Japanese", "Create a glossary for my project"]},
    "Spreadsheet Wizard": {"emoji": "\U0001F4CA", "color": "#6e7681", "title": "Spreadsheet Helper", "question": "What do you want to do with your spreadsheet?", "examples": ["Create a formula for this calculation", "Build a pivot table from my data", "Automate this spreadsheet task", "Explain this complex formula"]},
    "Form Builder": {"emoji": "\U0001F4DD", "color": "#6e7681", "title": "Make a Form", "question": "What kind of form do you need?", "examples": ["Create a feedback form", "Make a registration form", "Build a survey questionnaire", "Create an intake form for new clients"]},
    "Survey Analyzer": {"emoji": "\U0001F4CA", "color": "#6e7681", "title": "Survey Results", "question": "What do you want to learn from your survey?", "examples": ["Find trends in survey responses", "Summarize the key insights", "Create charts from this data", "What patterns do you see?"]},

    # ── Notes & Memory ──
    "Notebook": {"emoji": "\U0001F4D3", "color": "#d29922", "title": "My Notes", "question": "What do you want to note down?", "examples": ["Take notes on this meeting", "Summarize notes tagged important", "Turn this note into tasks", "Find my notes about the project"]},
    "Memory Bridge": {"emoji": "\U0001F9E0", "color": "#d29922", "title": "Memory Helper", "question": "What do you want to remember?", "examples": ["Remember I prefer short answers", "What did we talk about last time?", "Continue where we left off", "What are my saved preferences?"]},
    "Memory Recorder": {"emoji": "\u23f1\ufe0f", "color": "#d29922", "title": "Session Recorder", "question": "What do you want to record or find?", "examples": ["What did I do last Tuesday?", "Show me the audit trail for this decision", "Search my recordings for invoices", "Export this session for compliance"]},
    "Session Replay": {"emoji": "\u23ea", "color": "#d29922", "title": "Replay Past Work", "question": "What session do you want to replay?", "examples": ["Replay what I did yesterday", "Show me step-by-step from last week", "What decisions did I make?", "Play back my last coding session"]},
    "Smart Recall": {"emoji": "\U0001F9E0", "color": "#d29922", "title": "Search My History", "question": "What are you trying to remember?", "examples": ["Find when I discussed the budget", "Search for notes about the client meeting", "What did I say about this topic?", "Find that thing I was working on"]},
    "Decision Tracker": {"emoji": "\u2696\ufe0f", "color": "#d29922", "title": "Decision Log", "question": "What decision do you want to track?", "examples": ["Log my decision to switch suppliers", "Why did I choose this option?", "Show me my recent decisions", "Track the outcome of my last decision"]},
    "Knowledge Archive": {"emoji": "\U0001F3DB\ufe0f", "color": "#d29922", "title": "Knowledge Keeper", "question": "What do you want to save or find?", "examples": ["Archive this research", "Find what I saved about marketing", "Save this for later", "Search my knowledge base"]},
    "Habit Tracker": {"emoji": "\u2705", "color": "#d29922", "title": "Habit Helper", "question": "What habit are you tracking?", "examples": ["Track my daily exercise", "How consistent am I with reading?", "Show my habit streak", "Which habits need improvement?"]},
    "Progress Journal": {"emoji": "\U0001F4D6", "color": "#d29922", "title": "My Progress", "question": "What progress do you want to track?", "examples": ["What milestones did I hit this week?", "Log my progress on learning Python", "Show my achievements this month", "Journal about today's work"]},
    "Context Keeper": {"emoji": "\U0001F4CD", "color": "#d29922", "title": "Pick Up Where I Left Off", "question": "What were you working on?", "examples": ["Where did I leave off?", "Restore my last session", "What was I thinking about last time?", "Bring me back to my last project"]},
    "Audit Trail Builder": {"emoji": "\U0001F4DC", "color": "#d29922", "title": "Audit Report", "question": "What do you need an audit trail for?", "examples": ["Build an audit report for this project", "Show compliance-ready logs", "Create a trail of all decisions", "Format events for regulatory review"]},

    # ── Data & Analysis ──
    "Data Analyst Pro": {"emoji": "\U0001F4CA", "color": "#0d6efd", "title": "Data Detective", "question": "What data do you want to understand?", "examples": ["Analyze this spreadsheet for trends", "Create a chart from my data", "Find patterns in my sales numbers", "What's the story in this data?"]},
    "Data Entry Agent": {"emoji": "\u2328\ufe0f", "color": "#0d6efd", "title": "Data Entry Helper", "question": "What data do you need entered?", "examples": ["Organize this information into a table", "Check this data for errors", "Format these entries correctly", "Clean up this messy data"]},
    "Content Moderator": {"emoji": "\U0001F6E1\ufe0f", "color": "#0d6efd", "title": "Content Check", "question": "What content do you want reviewed?", "examples": ["Check this for inappropriate content", "Flag off-topic material in these posts", "Review these comments for spam", "Apply my moderation rules to this"]},

    # ── Business ──
    "Sales Assistant": {"emoji": "\U0001F4B0", "color": "#2ea043", "title": "Sales Helper", "question": "What do you need help selling?", "examples": ["Draft a pitch for my product", "Track my leads this week", "Prepare a follow-up message", "Help me close this deal"]},
    "Financial Analyst": {"emoji": "\U0001F4B8", "color": "#2ea043", "title": "Money Analyst", "question": "What financial question do you have?", "examples": ["Explain my spending patterns", "What trends do you see in my budget?", "Organize my expense data", "Where can I save money?"]},
    "HR Assistant": {"emoji": "\U0001F465", "color": "#2ea043", "title": "HR Helper", "question": "What HR task do you need help with?", "examples": ["Draft a job description", "Create interview questions", "Make an onboarding checklist", "Review this resume"]},
    "Compliance Auditor": {"emoji": "\U0001F50F", "color": "#2ea043", "title": "Compliance Check", "question": "What do you need audited?", "examples": ["Review this process for compliance", "Flag anything that breaks the rules", "Check this document against policy", "Generate a compliance report"]},
    "Supply Chain Coordinator": {"emoji": "\U0001F69A", "color": "#2ea043", "title": "Supply Chain Helper", "question": "What do you need tracked or coordinated?", "examples": ["Track my inventory levels", "Plan delivery schedules", "Check supplier status", "Balance resources for this order"]},
    "Multi-Department Orchestrator": {"emoji": "\U0001F3D7\ufe0f", "color": "#2ea043", "title": "Team Coordinator", "question": "What needs coordinating across teams?", "examples": ["Track handoffs between departments", "Coordinate this project across teams", "Who needs to do what by when?", "Align deadlines across teams"]},
    "Competitive Analyst": {"emoji": "\U0001F52C", "color": "#2ea043", "title": "Competitor Research", "question": "What do you want to know about competitors?", "examples": ["Analyze my top 3 competitors", "Generate a SWOT for my product", "Track market trends in my industry", "What are competitors doing differently?"]},
    "Knowledge Base Builder": {"emoji": "\U0001F3DB\ufe0f", "color": "#2ea043", "title": "Build a Knowledge Base", "question": "What do you want to organize into a knowledge base?", "examples": ["Create a help center for my product", "Organize these documents into topics", "Build searchable documentation", "Structure this information for easy lookup"]},
    "Team Orchestrator": {"emoji": "\U0001F465", "color": "#2ea043", "title": "AI Team Manager", "question": "What do you want your AI team to do?", "examples": ["Create a team of AIs for this project", "Assign roles: researcher, writer, reviewer", "Get consensus before proceeding", "Track what each AI is working on"]},

    # ── Financial Gainer ──
    "Financial Gainer": {"emoji": "\U0001F4B0", "color": "#2ea043", "title": "Make Money Helper", "question": "How do you want to make money?", "examples": ["What side hustles match my skills?", "How can I monetize my writing?", "Analyze the ROI of my business idea", "What skills should I learn to earn more?"]},
    "Crypto Scout": {"emoji": "\U0001FA99", "color": "#2ea043", "title": "Crypto Explorer", "question": "What do you want to know about crypto?", "examples": ["What's the trend on Bitcoin?", "Explain what staking is", "Compare these three altcoins", "What crypto scams should I watch for?"]},
    "Affiliate Strategist": {"emoji": "\U0001F517", "color": "#2ea043", "title": "Affiliate Helper", "question": "What do you want to promote?", "examples": ["Find affiliate programs for fitness products", "Draft a review for this software", "Compare commission rates", "What products match my audience?"]},
    "Click Commission Tracker": {"emoji": "\U0001F4F1", "color": "#2ea043", "title": "Link Performance", "question": "What do you want to know about your links?", "examples": ["Analyze my click-through rates", "Which links are performing best?", "How can I improve my conversion rate?", "Compare earnings across programs"]},
    "Sales Funnel Builder": {"emoji": "\U0001F6E4\ufe0f", "color": "#2ea043", "title": "Sales Funnel Builder", "question": "What kind of sales funnel do you need?", "examples": ["Design a funnel for my product", "Draft landing page copy", "Create an email sequence", "Suggest ways to improve conversions"]},
    "Side Hustle Scout": {"emoji": "\U0001F50D", "color": "#2ea043", "title": "Side Hustle Finder", "question": "What kind of side job are you looking for?", "examples": ["Find side hustles I can do from home", "What gigs match my schedule?", "Research gig platforms for me", "Find micro-business ideas for my skills"]},
    "Skill Monetizer": {"emoji": "\U0001F4B8", "color": "#2ea043", "title": "Turn Skills Into Money", "question": "What skills do you want to monetize?", "examples": ["How can I make money from my writing?", "Turn my coding skills into income", "Package my knowledge into a course", "What services can I offer?"]},
    "Investment Researcher": {"emoji": "\U0001F4B9", "color": "#2ea043", "title": "Investment Explorer", "question": "What do you want to research?", "examples": ["Research this stock for me", "Explain what ETFs are", "Compare these investment options", "What are the risks of this investment?"]},
    "ROI Calculator": {"emoji": "\U0001F4CA", "color": "#2ea043", "title": "ROI Calculator", "question": "What do you want to calculate?", "examples": ["Calculate ROI for my business idea", "When will I break even?", "Best and worst case for this project", "Is this investment worth it?"]},
    "Market Gap Finder": {"emoji": "\U0001F50D", "color": "#2ea043", "title": "Find Opportunities", "question": "What market are you exploring?", "examples": ["Find gaps in the fitness market", "What needs aren't being met?", "Where are the opportunities?", "Analyze this market for gaps"]},
    "Negotiation Coach": {"emoji": "\U0001F91D", "color": "#2ea043", "title": "Negotiation Coach", "question": "What do you want to negotiate?", "examples": ["Help me negotiate a raise", "Practice negotiating with a role-play", "Give me scripts for this deal", "How do I ask for a better rate?"]},
    "Budget Tracker": {"emoji": "\U0001F4B3", "color": "#2ea043", "title": "Budget Helper", "question": "What do you want to track?", "examples": ["Track my income and expenses", "Categorize my spending", "Create a budget report", "Where is my money going?"]},
    "Social Media Manager": {"emoji": "\U0001F4F1", "color": "#2ea043", "title": "Social Media Helper", "question": "What do you want to post?", "examples": ["Draft a post for Instagram", "Create a content calendar", "Suggest engagement ideas", "Write a tweet about my new product"]},

    # ── Enterprise & Security ──
    "Security Auditor": {"emoji": "\U0001F6E1\ufe0f", "color": "#da3633", "title": "Security Check", "question": "What do you want to check for security?", "examples": ["Scan this code for vulnerabilities", "Check my config for weaknesses", "Generate a security report", "Find security issues in this system"]},
    "Legal Document Reviewer": {"emoji": "\u2696\ufe0f", "color": "#da3633", "title": "Legal Document Reader", "question": "What legal document do you want reviewed?", "examples": ["Summarize this contract", "Find the termination clauses", "Flag risks in this agreement", "What are the key terms?"]},
    "Medical Researcher": {"emoji": "\U0001F52C", "color": "#da3633", "title": "Medical Research", "question": "What do you want to research?", "examples": ["Find studies on this treatment", "Compare clinical trial results", "Summarize evidence on this drug", "Check for drug interactions"]},
    "API Integrator": {"emoji": "\U0001F517", "color": "#da3633", "title": "Connect Apps", "question": "What do you want to connect?", "examples": ["Connect to my CRM", "Set up a webhook for orders", "Sync data with an external platform", "Build an API integration"]},

    # ── Creative & Visual ──
    "Visual Canvas": {"emoji": "\U0001F3A8", "color": "#8957e5", "title": "Create Images", "question": "What image do you want to create?", "examples": ["Generate an image of a sunset", "Create a diagram of my workflow", "Make a visual for my presentation", "Design a logo concept"]},
    "Voice Interface": {"emoji": "\U0001F3A4", "color": "#8957e5", "title": "Talk to Your AI", "question": "What do you want to say?", "examples": ["Start a voice conversation", "Read this response aloud", "Change the voice settings", "Listen to my notes"]},
    "Game Companion": {"emoji": "\U0001F3AE", "color": "#8957e5", "title": "Game Buddy", "question": "What game do you want to play?", "examples": ["Teach me chess rules", "Suggest a strategy for this game", "Play a practice round with me", "Explain how this game works"]},
    "Activity Watcher": {"emoji": "\U0001F441\ufe0f", "color": "#8957e5", "title": "Work Helper", "question": "What do you want me to watch or learn?", "examples": ["Watch how I process invoices", "What tasks do I do repeatedly?", "Suggest a faster way to do my work", "Repeat the task you learned yesterday"]},

    # ── Archive ──
    "Archive": {"emoji": "\U0001F4E6", "color": "#6e7681", "title": "Save It", "question": "What do you want to save or find?", "examples": ["Archive this result", "Find what I saved before", "List my saved outputs", "Retrieve something I archived"]},

    # ── Tools ──
    "Tool User": {"emoji": "\U0001F527", "color": "#6e7681", "title": "Tool Helper", "question": "What do you need help with?", "examples": ["What tools can help with this?", "Propose a tool chain", "Prepare an approval request", "What's the best tool for this job?"]},

    # ── Other ──
    "Hephaestus Relay": {"emoji": "\U0001F528", "color": "#6e7681", "title": "Design Helper", "question": "What do you want to design?", "examples": ["Turn this idea into a design brief", "List constraints and unknowns", "Prepare a handoff packet", "Structure my design requirements"]},
    "Accessibility Assistant": {"emoji": "\U0001F9E0", "color": "#f0883e", "title": "Make It Easier", "question": "How can I make this easier for you?", "examples": ["Read this aloud", "Increase text size", "Convert to screen reader format", "Provide alternative input methods"]},
}


def get_quick_start(capability_name: str) -> dict:
    """Get quick-start config for a capability, with a sensible default."""
    qs = CAPABILITY_QUICK_START.get(capability_name)
    if qs:
        return qs
    return {
        "emoji": "\u2753", "color": "#6e7681",
        "title": capability_name,
        "question": f"What do you want to do with {capability_name.lower()}?",
        "examples": [f"Help me with {capability_name.lower()}", "Explain what this does", "Get started", "Show me an example"],
    }


# ===========================================================================
# SimpleCapabilityLauncher — one input, one button, one result
# ===========================================================================

class SimpleCapabilityLauncher(QDialog):
    """Child-friendly one-click capability launcher.

    Shows:
      - Big emoji + title at top
      - One question prompt
      - One text input box
      - 4 clickable example chips
      - One big GO button
      - Results area below
    """

    def __init__(self, capability_name: str, ai_name: str = "AI", ai_uuid: str = "",
                 abilities=None, book_path=None, guardrails=None, libraries=None,
                 use_case: str = "", parent=None):
        super().__init__(parent)
        self._capability_name = capability_name
        self._ai_name = ai_name
        self._ai_uuid = ai_uuid
        self._abilities = abilities or []
        self._book_path = book_path
        self._guardrails = guardrails or []
        self._libraries = libraries or []
        self._use_case = use_case

        qs = get_quick_start(capability_name)
        self._qs = qs

        self.setWindowTitle(f"{qs['emoji']} {qs['title']} — {ai_name} | Command Nexus\u2122")
        self.resize(700, 550)
        self.setStyleSheet(" color: #c9d1d9;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Header: big emoji + title ──
        header_row = QHBoxLayout()
        emoji_lbl = QLabel(qs["emoji"])
        emoji_lbl.setStyleSheet("font-size: 36px;")
        emoji_lbl.setFixedSize(50, 50)
        header_row.addWidget(emoji_lbl)

        title_lbl = QLabel(f"<h2>{qs['title']}</h2>")
        title_lbl.setStyleSheet(f"color: {qs['color']}; font-size: 18px; font-weight: bold;")
        header_row.addWidget(title_lbl, stretch=1)
        layout.addLayout(header_row)

        # ── Question prompt ──
        question_lbl = QLabel(qs["question"])
        question_lbl.setStyleSheet("color: #8b949e; font-size: 14px; padding: 4px 0;")
        layout.addWidget(question_lbl)

        # ── Input box ──
        self._input = QLineEdit()
        self._input.setPlaceholderText(f"Type here... or click an example below")
        self._input.setStyleSheet(
            f" color: #e2e8f0; border: 2px solid {qs['color']}; "
            f"padding: 10px; border-radius: 6px; font-size: 14px;"
        )
        self._input.returnPressed.connect(self._on_go)
        layout.addWidget(self._input)

        # ── Example chips ──
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        for ex in qs.get("examples", []):
            chip = QPushButton(ex)
            chip.setStyleSheet(
                f"background-color: {qs['color']}22; color: {qs['color']}; "
                f"border: 1px solid {qs['color']}66; border-radius: 12px; "
                f"padding: 4px 10px; font-size: 11px;"
            )
            chip.clicked.connect(lambda checked, e=ex: self._on_chip_click(e))
            chips_row.addWidget(chip)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        # ── GO button ──
        self._go_btn = QPushButton(f"\u2713  GO!")
        self._go_btn.setStyleSheet(
            f"background-color: {qs['color']}; color: white; font-size: 16px; "
            f"font-weight: bold; padding: 10px; border-radius: 6px; min-height: 40px;"
        )
        self._go_btn.clicked.connect(self._on_go)
        layout.addWidget(self._go_btn)

        # ── Results area ──
        layout.addWidget(QLabel("Result:"))
        self._result = QTextEdit()
        self._result.setReadOnly(True)
        self._result.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; "
            "border-radius: 6px; padding: 8px; font-size: 13px;"
        )
        self._result.setPlaceholderText("Your result will appear here after you click GO!")
        layout.addWidget(self._result, stretch=1)

        # ── Close button ──
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

    def _on_chip_click(self, text: str):
        """Fill the input box with the clicked example."""
        self._input.setText(text)
        self._input.setFocus()

    def _on_go(self):
        """Run the task through NexusAIRuntime and show the result."""
        msg = self._input.text().strip()
        if not msg:
            self._result.setText("\u26a0\ufe0f Please type something first, or click an example!")
            return

        self._go_btn.setEnabled(False)
        self._go_btn.setText("Working...")
        self._result.setText("\u23f3 Thinking...")

        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            settings = SettingsManager()
            settings.initialize()
            runtime = NexusAIRuntime(settings=settings)
            result = runtime.run(
                task=msg,
                ai_name=self._ai_name,
                ai_uuid=self._ai_uuid,
                ai_metadata={
                    "abilities": self._abilities or [self._capability_name],
                    "use_case": self._use_case,
                    "guardrails": self._guardrails,
                    "libraries": self._libraries,
                },
            )
            if result.result_text:
                self._result.setHtml(f"<b>{self._ai_name}:</b> {result.result_text}")
            else:
                self._result.setText("I processed your request but didn't produce output. Try rephrasing your question.")
        except Exception as e:
            try:
                from ...core.backend_manager import BackendManager
                settings = SettingsManager()
                settings.initialize()
                backend = BackendManager(settings)
                prompt = (
                    f"You are {self._ai_name}, a Command Nexus governed AI.\n"
                    f"Capability: {self._capability_name}\n"
                    f"Use case: {self._use_case}\n"
                    f"Abilities: {', '.join(self._abilities) or self._capability_name}\n\n"
                    f"User message: {msg}\n\n"
                    "Respond helpfully in plain, simple language."
                )
                response = backend.call_model(prompt)
                if response.error:
                    self._result.setText(f"Error: {response.error}")
                elif response.text:
                    self._result.setHtml(f"<b>{self._ai_name}:</b> {response.text}")
                else:
                    self._result.setText("I couldn't generate a response. Please try again.")
            except Exception as e2:
                self._result.setText(f"I'm having trouble connecting: {e2}")

        self._go_btn.setEnabled(True)
        self._go_btn.setText("\u2713  GO!")
        self._input.clear()
