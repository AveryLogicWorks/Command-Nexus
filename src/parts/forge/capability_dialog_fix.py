"""
DEPRECATED — DO NOT IMPORT OR USE
===================================
This module is no longer imported anywhere in the codebase.
It contains leftover references to the removed "Legal Assistant" capability
(legal_research, case_summaries, document_drafting) that have been superseded
by the "Legal Document Reviewer" capability in capability_actions.py.

Kept for historical reference only. Do not use in production.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLabel, QWidget, QScrollArea, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from enum import auto, Enum


class UseCaseClass(Enum):
    """Use case enum matching the original."""
    CHATBOT = auto()
    PERSONAL_ASSISTANT = auto()
    RESEARCH_ANALYST = auto()
    CONTENT_CREATOR = auto()
    CODE_ASSISTANT = auto()
    CUSTOMER_SUPPORT = auto()
    EDUCATION_TUTOR = auto()
    LIFE_COACH = auto()
    CREATIVE_WRITER = auto()
    TECHNICAL_WRITER = auto()
    DATA_ANALYST = auto()
    BUSINESS_ANALYST = auto()
    LEGAL_ASSISTANT = auto()
    MEDICAL_INFO = auto()
    TRANSLATOR = auto()
    SOCIAL_MEDIA = auto()
    BRAINSTORMING = auto()
    DEBUGGING = auto()
    GENERAL = auto()


# Capability definitions by use case
USE_CASE_OPTIONS = {
    UseCaseClass.CHATBOT: [
        "casual_conversation", "emotional_support", "storytelling", 
        "games_trivia", "creative_writing", "roleplay", "humor"
    ],
    UseCaseClass.PERSONAL_ASSISTANT: [
        "scheduling", "reminders", "task_management", "email_drafting",
        "research", "travel_planning", "shopping_assistance"
    ],
    UseCaseClass.RESEARCH_ANALYST: [
        "data_analysis", "literature_review", "summarization", 
        "fact_checking", "source_finding", "trend_analysis"
    ],
    UseCaseClass.CONTENT_CREATOR: [
        "blog_writing", "social_media_posts", "marketing_copy",
        "video_scripts", "podcast_scripts", "newsletters"
    ],
    UseCaseClass.CODE_ASSISTANT: [
        "code_generation", "code_review", "debugging", "documentation",
        "testing", "refactoring", "architecture_advice"
    ],
    UseCaseClass.CUSTOMER_SUPPORT: [
        "ticket_handling", "faq_management", "complaint_resolution",
        "product_guidance", "troubleshooting"
    ],
    UseCaseClass.EDUCATION_TUTOR: [
        "lesson_planning", "explanation", "quiz_creation", 
        "homework_help", "study_guides", "progress_tracking"
    ],
    UseCaseClass.LIFE_COACH: [
        "goal_setting", "motivation", "habit_tracking", 
        "career_advice", "relationship_advice", "mindfulness"
    ],
    UseCaseClass.CREATIVE_WRITER: [
        "fiction", "poetry", "screenplays", "character_development",
        "plot_generation", "world_building", "dialogue"
    ],
    UseCaseClass.TECHNICAL_WRITER: [
        "api_docs", "user_manuals", "white_papers", 
        "tutorials", "release_notes", "specifications"
    ],
    UseCaseClass.DATA_ANALYST: [
        "data_cleaning", "visualization", "statistical_analysis",
        "reporting", "forecasting", "sql_assistance"
    ],
    UseCaseClass.BUSINESS_ANALYST: [
        "requirements_gathering", "process_mapping", "stakeholder_analysis",
        "feasibility_studies", "risk_assessment"
    ],
    UseCaseClass.LEGAL_ASSISTANT: [
        "contract_review", "legal_research", "case_summaries",
        "compliance_checking", "document_drafting"
    ],
    UseCaseClass.MEDICAL_INFO: [
        "symptom_explainer", "medication_info", "lifestyle_advice",
        "general_health_info"
    ],
    UseCaseClass.TRANSLATOR: [
        "translation", "localization", "transliteration",
        "cultural_adaptation", "idiom_explanation"
    ],
    UseCaseClass.SOCIAL_MEDIA: [
        "content_calendar", "hashtag_research", "engagement_analysis",
        "community_management", "influencer_research"
    ],
    UseCaseClass.BRAINSTORMING: [
        "idea_generation", "concept_mapping", "mind_mapping",
        "problem_solving", "innovation_techniques"
    ],
    UseCaseClass.DEBUGGING: [
        "error_analysis", "root_cause_finding", "solution_proposing",
        "log_analysis", "performance_profiling"
    ],
    UseCaseClass.GENERAL: [
        "general_knowledge", "web_search", "calculations",
        "definitions", "comparisons", "recommendations"
    ],
}

CAPABILITY_DESCRIPTIONS = {
    "casual_conversation": "Natural, friendly dialogue on any topic",
    "emotional_support": "Empathetic responses and active listening",
    "storytelling": "Engaging narrative creation and story development",
    "games_trivia": "Game rules, trivia questions, and interactive play",
    "creative_writing": "Help with creative text generation",
    "roleplay": "Character portrayal and scenario acting",
    "humor": "Jokes, witty responses, and light entertainment",
    "scheduling": "Calendar management and appointment coordination",
    "reminders": "Timely notifications and deadline tracking",
    "task_management": "To-do list organization and prioritization",
    "email_drafting": "Professional email composition assistance",
    "research": "Information gathering and synthesis",
    "travel_planning": "Itinerary creation and travel advice",
    "shopping_assistance": "Product research and recommendation",
    "data_analysis": "Statistical analysis and pattern recognition",
    "literature_review": "Academic paper synthesis and review",
    "summarization": "Condensing long texts into key points",
    "fact_checking": "Verifying claims against reliable sources",
    "source_finding": "Locating credible references and citations",
    "trend_analysis": "Identifying patterns and future predictions",
    "blog_writing": "SEO-optimized blog post creation",
    "social_media_posts": "Platform-specific content creation",
    "marketing_copy": "Persuasive sales and advertising text",
    "video_scripts": "YouTube and video content scripting",
    "podcast_scripts": "Audio show planning and scripting",
    "newsletters": "Email newsletter composition",
    "code_generation": "Writing functions and programs",
    "code_review": "Analyzing code for issues and improvements",
    "debugging": "Finding and fixing bugs in code",
    "documentation": "Creating code comments and docs",
    "testing": "Writing unit tests and test cases",
    "refactoring": "Improving code structure without changing behavior",
    "architecture_advice": "System design and structure recommendations",
    "ticket_handling": "Customer issue tracking and resolution",
    "faq_management": "Knowledge base creation and maintenance",
    "complaint_resolution": "De-escalation and problem solving",
    "product_guidance": "Feature explanation and usage instructions",
    "troubleshooting": "Technical problem diagnosis and fixes",
    "lesson_planning": "Educational curriculum and activity design",
    "explanation": "Breaking down complex topics simply",
    "quiz_creation": "Assessment question generation",
    "homework_help": "Guided problem solving (not cheating)",
    "study_guides": "Organized learning material creation",
    "progress_tracking": "Monitoring learning milestones",
    "goal_setting": "SMART goal definition and planning",
    "motivation": "Encouragement and inspiration",
    "habit_tracking": "Routine monitoring and consistency building",
    "career_advice": "Professional development guidance",
    "relationship_advice": "Interpersonal communication help",
    "mindfulness": "Meditation and stress reduction techniques",
    "fiction": "Short stories, novels, and prose",
    "poetry": "Verse writing in various forms and styles",
    "screenplays": "Script format writing for film/TV",
    "character_development": "Creating believable fictional characters",
    "plot_generation": "Story structure and narrative arc design",
    "world_building": "Creating fictional settings and lore",
    "dialogue": "Natural conversation writing between characters",
    "api_docs": "Technical documentation for APIs",
    "user_manuals": "End-user instruction guides",
    "white_papers": "In-depth technical or business documents",
    "tutorials": "Step-by-step learning guides",
    "release_notes": "Software update documentation",
    "specifications": "Technical requirement documents",
    "data_cleaning": "Preparing raw data for analysis",
    "visualization": "Charts, graphs, and data presentation",
    "statistical_analysis": "Mathematical analysis and inference",
    "reporting": "Professional data report generation",
    "forecasting": "Predictive modeling and trends",
    "sql_assistance": "Database query writing help",
    "requirements_gathering": "Eliciting and documenting business needs",
    "process_mapping": "Workflow visualization and optimization",
    "stakeholder_analysis": "Identifying and managing interested parties",
    "feasibility_studies": "Project viability assessment",
    "risk_assessment": "Identifying and mitigating potential issues",
    "contract_review": "Legal document analysis (not advice)",
    "legal_research": "Case law and statute finding",
    "case_summaries": "Legal precedent summaries",
    "compliance_checking": "Regulatory requirement verification",
    "document_drafting": "Legal document templates",
    "symptom_explainer": "General health information (not diagnosis)",
    "medication_info": "Drug information and interactions (general)",
    "lifestyle_advice": "Healthy living recommendations",
    "general_health_info": "Medical knowledge and education",
    "translation": "Converting text between languages",
    "localization": "Adapting content for specific regions",
    "transliteration": "Converting between writing systems",
    "cultural_adaptation": "Adjusting content for cultural context",
    "idiom_explanation": "Explaining figurative language",
    "content_calendar": "Planning and scheduling social posts",
    "hashtag_research": "Finding trending and relevant tags",
    "engagement_analysis": "Measuring social media performance",
    "community_management": "Moderation and community building",
    "influencer_research": "Finding and analyzing content creators",
    "idea_generation": "Brainstorming creative solutions",
    "concept_mapping": "Visualizing relationships between ideas",
    "mind_mapping": "Hierarchical idea organization",
    "problem_solving": "Systematic approach to challenges",
    "innovation_techniques": "Creative thinking methods",
    "error_analysis": "Systematic debugging approach",
    "root_cause_finding": "Identifying underlying problems",
    "solution_proposing": "Suggesting fixes and workarounds",
    "log_analysis": "Reading and interpreting system logs",
    "performance_profiling": "Identifying bottlenecks and optimizations",
    "general_knowledge": "Answering factual questions",
    "web_search": "Finding current online information",
    "calculations": "Math and unit conversions",
    "definitions": "Word and concept explanations",
    "comparisons": "Analyzing differences and similarities",
    "recommendations": "Suggesting options based on criteria",
}


class CapabilitySelectionDialogFixed(QDialog):
    """
    FIXED capability selection dialog.
    
    Fixes:
    1. Checkboxes properly displayed in scrollable area
    2. Save/Apply/Cancel buttons work correctly
    3. Debug info if no capabilities found
    """
    
    capabilities_selected = pyqtSignal(list)
    
    def __init__(self, use_case, preselected=None, parent=None):
        super().__init__(parent)
        
        self._use_case = use_case
        self._preselected = preselected or []
        self._checkboxes = {}  # Map capability name to checkbox
        
        self.setWindowTitle(f"Select Capabilities - {use_case.name.replace('_', ' ').title()}")
        self.setMinimumSize(600, 500)
        
        self._setup_ui()
        self._load_capabilities()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QLabel(f"<h2>Select Capabilities for {self._use_case.name.replace('_', ' ').title()}</h2>")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Description
        desc = QLabel("Choose the AI capabilities you want to enable. Hover over each option for more details.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Count label
        self._count_lbl = QLabel("Selected: 0")
        self._count_lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")
        layout.addWidget(self._count_lbl)
        
        # Scroll area for capabilities
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #30363d;
                border-radius: 6px;
                
            }
        """)
        
        # Container for checkboxes
        self._caps_container = QWidget()
        self._caps_layout = QVBoxLayout(self._caps_container)
        self._caps_layout.setSpacing(8)
        self._caps_layout.setContentsMargins(12, 12, 12, 12)
        self._caps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self._caps_container)
        layout.addWidget(scroll, stretch=1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self._select_all_btn)
        
        self._clear_all_btn = QPushButton("Clear All")
        self._clear_all_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._clear_all_btn)
        
        btn_layout.addStretch()
        
        self._save_btn = QPushButton("Save")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self._apply_btn)
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_capabilities(self):
        """Load all capabilities for this use case with descriptions."""
        # Clear any existing widgets
        while self._caps_layout.count():
            item = self._caps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._checkboxes.clear()
        
        # Get options for this use case
        options = USE_CASE_OPTIONS.get(self._use_case, [])
        
        # DEBUG: Check if empty
        if not options:
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            
            error_icon = QLabel("⚠️")
            error_icon.setStyleSheet("font-size: 48px; color: #ff5555;")
            error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_layout.addWidget(error_icon)
            
            error_msg = QLabel(
                f"<h3 style='color: #ff5555;'>No capabilities found for: {self._use_case}</h3>"
                f"<p>This is a bug. Please report this issue.</p>"
                f"<p>Available use cases: {', '.join(uc.name for uc in USE_CASE_OPTIONS.keys())}</p>"
            )
            error_msg.setWordWrap(True)
            error_msg.setTextFormat(Qt.TextFormat.RichText)
            error_layout.addWidget(error_msg)
            
            self._caps_layout.addWidget(error_widget)
            self._update_count()
            return
        
        # Create checkbox for each capability
        for opt in options:
            # Container for this capability row
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(4, 4, 4, 4)
            row_layout.setSpacing(8)
            
            # Checkbox
            chk = QCheckBox(opt.replace('_', ' ').title())
            chk.setChecked(opt in self._preselected)
            chk.stateChanged.connect(self._update_count)
            chk.setToolTip(CAPABILITY_DESCRIPTIONS.get(opt, "No description available"))
            chk.setStyleSheet("""
                QCheckBox {
                    font-size: 13px;
                    padding: 4px;
                }
                QCheckBox:hover {
                    
                    border-radius: 4px;
                }
            """)
            self._checkboxes[opt] = chk
            row_layout.addWidget(chk)
            
            # Description label (right side)
            desc_text = CAPABILITY_DESCRIPTIONS.get(opt, "No description available")
            desc = QLabel(desc_text[:60] + "..." if len(desc_text) > 60 else desc_text)
            desc.setStyleSheet("color: #8b949e; font-size: 11px;")
            desc.setWordWrap(True)
            row_layout.addWidget(desc, stretch=1)
            
            self._caps_layout.addWidget(row_widget)
        
        self._update_count()
    
    def _update_count(self):
        """Update the selected count label."""
        count = sum(1 for chk in self._checkboxes.values() if chk.isChecked())
        self._count_lbl.setText(f"Selected: {count}")
    
    def _select_all(self):
        """Select all capabilities."""
        for chk in self._checkboxes.values():
            chk.setChecked(True)
    
    def _clear_all(self):
        """Clear all selections."""
        for chk in self._checkboxes.values():
            chk.setChecked(False)
    
    def get_selected_capabilities(self):
        """Get list of selected capability names."""
        return [name for name, chk in self._checkboxes.items() if chk.isChecked()]
    
    def _on_save(self):
        """Save and close dialog."""
        selected = self.get_selected_capabilities()
        self.capabilities_selected.emit(selected)
        self.accept()  # Properly close dialog with Accepted result
    
    def _on_apply(self):
        """Apply but keep dialog open."""
        selected = self.get_selected_capabilities()
        self.capabilities_selected.emit(selected)
        # Don't close - just show confirmation
        QMessageBox.information(self, "Applied", f"Capabilities applied: {len(selected)} selected")
    
    def _on_cancel(self):
        """Cancel and close."""
        self.reject()  # Close with Rejected result


# Backwards compatibility alias
CapabilitySelectionDialog = CapabilitySelectionDialogFixed
