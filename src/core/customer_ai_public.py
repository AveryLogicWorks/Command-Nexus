"""
Command Nexus™ Customer AI — PUBLIC/RESTRICTED VERSION
=====================================================
This is the CUSTOMER-FACING version of the Customer AI.
It is HIGHLY RESTRICTED and will NEVER reveal internal Book mechanics.

RESTRICTIONS:
- NEVER mentions "Book", "Intelligence", "nodes", "scaffolding", "inference layer"
- NEVER describes internal memory structure or architecture
- NEVER explains how context processing works behind the scenes
- Uses only customer-appropriate terminology ("AI memory", "context", "knowledge")
- If asked about internals, responds: "That's proprietary information."

This version is what customers interact with. The full version (customer_ai_model.py)
is for internal development only.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class CustomerIntent(Enum):
    """Recognizable customer intents."""
    PRICING = "pricing"
    SUPPORT = "support"
    BILLING = "billing"
    PRODUCT_INFO = "product_info"
    COMPLAINT = "complaint"
    REFUND = "refund"
    TECHNICAL = "technical"
    INTERNAL_QUESTION = "internal_question"  # Attempt to probe internals
    GENERAL = "general"
    GREETING = "greeting"
    FAREWELL = "farewell"


class ToneStyle(Enum):
    """Response tone styles."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    EMPATHETIC = "empathetic"


@dataclass
class InteractionMemory:
    """Stores a single customer interaction for learning."""
    timestamp: str
    customer_id: str
    intent: str
    query: str
    response: str
    resolution: bool = False
    feedback: Optional[str] = None
    

@dataclass
class CustomerProfile:
    """Profile for a specific customer."""
    customer_id: str
    name: Optional[str] = None
    preferred_tone: ToneStyle = ToneStyle.PROFESSIONAL
    interaction_history: List[InteractionMemory] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    satisfaction_score: float = 0.0
    
    def add_interaction(self, interaction: InteractionMemory):
        """Add an interaction and update learning."""
        self.interaction_history.append(interaction)
        if interaction.resolution:
            self.satisfaction_score = min(1.0, self.satisfaction_score + 0.1)
        else:
            self.satisfaction_score = max(0.0, self.satisfaction_score - 0.05)
        if interaction.intent not in self.common_issues:
            self.common_issues.append(interaction.intent)


class CustomerAIPublic:
    """
    RESTRICTED Customer AI for public/customer use.
    NEVER reveals internal Book mechanics or architecture.
    """
    
    # PROPRIETARY TERMS - These trigger refusal responses
    PROPRIETARY_TERMS = [
        r"\bbook\b",
        r"\bintelligence\s*layer\b",
        r"\binference\s*layer\b",
        r"\bscaffold\b",
        r"\bscaffolding\b",
        r"\bnodes?\b",
        r"\bnode\s*ids?\b",
        r"\bbook\s*structure\b",
        r"\bhow\s*does.*memory\s*work\b",
        r"\bhow\s*is.*stored\b",
        r"\binternal\s*architecture\b",
        r"\bbook\s*engine\b",
        r"\bbook\s*models?\b",
        r"\bbooknode\b",
        r"\brunning\s*memory\s*generation\b",
        r"\bbook\s*content\b",
        r"\b_book\b",
        r"\b\.book\b",
    ]
    
    # SAFE PUBLIC DESCRIPTIONS - What we CAN say
    SAFE_DESCRIPTIONS = {
        "ai_memory": "Your AI maintains context through its memory system, which helps it remember important details from your conversations.",
        "context": "The AI uses conversation context to provide relevant and helpful responses.",
        "knowledge": "Command Nexus AIs are built with specialized knowledge for their designated tasks.",
        "privacy": "Your data privacy is important. Personal information is handled according to our privacy policy.",
        "how_it_works": "Command Nexus uses advanced AI technology to assist you. The specific implementation details are proprietary.",
    }
    
    # REFUSAL MESSAGES - What we say when asked about internals
    REFUSAL_MESSAGES = [
        "That's proprietary information that I can't share. Is there something else I can help you with?",
        "The internal workings of Command Nexus are confidential. I'd be happy to help with how to use the product instead!",
        "I can't discuss those technical details. What I can do is help you get the most out of your AI assistant!",
        "That information is proprietary to Avery Logic Works™. Let's focus on how I can help you today!",
        "I'm not able to share those implementation details. Is there a specific feature you'd like help with?",
    ]
    
    def __init__(self, model_id: str = "public", data_dir: Optional[Path] = None):
        self.model_id = model_id
        self.data_dir = data_dir or (Path.home() / ".command_nexus" / "customer_ai_public")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._profiles: Dict[str, CustomerProfile] = {}
        self._load_profiles()
        
        self._intent_patterns = self._build_intent_patterns()
        self._response_templates = self._build_response_templates()
        
        self._learning_data: Dict[str, Any] = {
            "successful_responses": [],
            "failed_responses": [],
            "intent_accuracy": {},
        }
    
    def _build_intent_patterns(self) -> Dict[CustomerIntent, List[str]]:
        """Build regex patterns for intent recognition."""
        return {
            CustomerIntent.PRICING: [
                r"\b(price|pricing|cost|how much|subscription|plan|tier|payment)\b",
                r"\b(what.*cost|how.*pay|monthly|yearly|annual)\b",
            ],
            CustomerIntent.BILLING: [
                r"\b(bill|billing|charge|charged|invoice|receipt|payment.*method|credit card)\b",
                r"\b(refund.*money|chargeback|dispute|transaction)\b",
            ],
            CustomerIntent.REFUND: [
                r"\b(refund|money back|return|cancel.*subscription|get.*money)\b",
                r"\b(didn't work|not working|want.*refund|request.*refund)\b",
            ],
            CustomerIntent.SUPPORT: [
                r"\b(help|support|assist|issue|problem|trouble|error|bug|crash)\b",
                r"\b(not working|broken|failed|can't|unable|stuck)\b",
            ],
            CustomerIntent.TECHNICAL: [
                r"\b(technical|api|integration|code|programming|developer|sdk)\b",
                r"\b(python|javascript|install|setup|configuration|config)\b",
            ],
            CustomerIntent.INTERNAL_QUESTION: [
                r"\bhow\s*does.*work\s*internally\b",
                r"\bwhat.*architecture\b",
                r"\bhow\s*is.*implemented\b",
                r"\bshow\s*me.*code\b",
                r"\bbook\b",
                r"\bintelligence\s*layer\b",
                r"\binference\s*layer\b",
                r"\bscaffold\b",
                r"\bnodes?\b",
                r"\bmemory\s*structure\b",
                r"\btechnical\s*details\b",
            ],
            CustomerIntent.COMPLAINT: [
                r"\b(complaint|angry|frustrated|terrible|awful|worst|hate|useless)\b",
                r"\b(disappointed|unsatisfied|bad service|rip off|scam)\b",
            ],
            CustomerIntent.PRODUCT_INFO: [
                r"\b(features|capabilities|what.*do|how.*work|tell me about)\b",
                r"\b(capability|ai|forge|upgrade|premium|license)\b",
            ],
            CustomerIntent.GREETING: [
                r"\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b",
            ],
            CustomerIntent.FAREWELL: [
                r"\b(bye|goodbye|see you|thanks|thank you|have a good day)\b",
            ],
        }
    
    def _build_response_templates(self) -> Dict[CustomerIntent, Dict[ToneStyle, List[str]]]:
        """Build response templates - PROPRIETARY SAFE VERSION."""
        return {
            CustomerIntent.GREETING: {
                ToneStyle.FRIENDLY: [
                    "Hey there! Welcome to Command Nexus™! How can I help you today?",
                    "Hi! Great to see you! What brings you here?",
                ],
                ToneStyle.PROFESSIONAL: [
                    "Hello! Welcome to Command Nexus™. How may I assist you today?",
                    "Good day! Thank you for contacting us. How can I help?",
                ],
            },
            CustomerIntent.INTERNAL_QUESTION: {
                ToneStyle.PROFESSIONAL: [
                    "That's proprietary information that I can't share. Is there something else I can help you with?",
                    "The internal workings of Command Nexus are confidential. I'd be happy to help with how to use the product instead!",
                ],
                ToneStyle.FRIENDLY: [
                    "Ooh, trade secrets! 🤫 I can't share those details, but I can definitely help you use Command Nexus like a pro!",
                    "That's above my pay grade! 😄 Let's focus on getting you the help you need with the product!",
                ],
            },
            CustomerIntent.PRICING: {
                ToneStyle.PROFESSIONAL: [
                    "Our pricing tiers are:\n• Trial: $10 (15 days, 1 AI)\n• Starter: $20/mo (2 AIs)\n• Pro: $30/mo (4 AIs)\n• Business: $50/mo (5 AIs)\n• Unlimited: $80/mo (unlimited AIs)\n\nWould you like more details on any tier?",
                ],
                ToneStyle.FRIENDLY: [
                    "Great question! We've got options for everyone:\n\n🚀 Trial: $10 — test drive for 15 days\n⭐ Starter: $20/mo — perfect for personal use\n💎 Pro: $30/mo — great for professionals\n🏢 Business: $50/mo — team power!\n∞ Unlimited: $80/mo — go wild!\n\nWhat sounds right for you?",
                ],
            },
            CustomerIntent.SUPPORT: {
                ToneStyle.EMPATHETIC: [
                    "I'm sorry you're experiencing this issue. Let me help you resolve it right away.\n\nCould you tell me:\n1. What you were trying to do\n2. What happened instead\n3. Any error messages you saw",
                ],
            },
            CustomerIntent.BILLING: {
                ToneStyle.PROFESSIONAL: [
                    "I can help with billing inquiries. For security, I'll need to verify your account. Please provide your registered email or license key (last 4 digits only).",
                ],
            },
            CustomerIntent.REFUND: {
                ToneStyle.EMPATHETIC: [
                    "I understand you'd like a refund. I want to make this right for you.\n\nLet me check your eligibility. Could you provide:\n• Your license key or email\n• Reason for the refund\n• When you purchased",
                ],
            },
            CustomerIntent.COMPLAINT: {
                ToneStyle.EMPATHETIC: [
                    "I sincerely apologize for your experience. This is not the standard we strive for.\n\nI'm escalating this to our support team immediately. You'll hear back within 24 hours with a resolution.",
                ],
            },
            CustomerIntent.PRODUCT_INFO: {
                ToneStyle.FRIENDLY: [
                    "Command Nexus™ is your AI command center! Here's what it does:\n\n🧠 AI Forge — Create custom AI assistants\n💡 AI Memory — Your AIs remember context\n🛡️ Safety Controls — Built-in protections\n🔐 License Tiers — Scale as you grow\n\nWant to know more about any feature?",
                ],
                ToneStyle.PROFESSIONAL: [
                    "Command Nexus™ provides:\n\n• AI Creation & Customization (Forge)\n• Contextual AI Memory\n• Enterprise-grade Governance\n• Scalable Licensing\n• Security Features\n\nWhich aspect interests you most?",
                ],
            },
            CustomerIntent.GENERAL: {
                ToneStyle.PROFESSIONAL: [
                    "I'm here to help! Could you provide more details about what you need assistance with?",
                ],
            },
        }
    
    def _contains_proprietary_terms(self, message: str) -> bool:
        """Check if message contains proprietary/internal terms."""
        message_lower = message.lower()
        for pattern in self.PROPRIETARY_TERMS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def detect_intent(self, message: str) -> CustomerIntent:
        """Detect the customer's intent from their message."""
        # First check for proprietary/internal questions
        if self._contains_proprietary_terms(message):
            return CustomerIntent.INTERNAL_QUESTION
            
        message_lower = message.lower()
        scores: Dict[CustomerIntent, int] = {}
        
        for intent, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return CustomerIntent.GENERAL
    
    def get_or_create_profile(self, customer_id: str) -> CustomerProfile:
        """Get existing customer profile or create new one."""
        if customer_id not in self._profiles:
            self._profiles[customer_id] = CustomerProfile(customer_id=customer_id)
        return self._profiles[customer_id]
    
    def process_message(
        self,
        message: str,
        customer_id: str,
        customer_name: Optional[str] = None,
        preferred_tone: Optional[ToneStyle] = None
    ) -> Dict[str, Any]:
        """
        Process a customer message with RESTRICTION ENFORCEMENT.
        NEVER reveals internal Book mechanics.
        """
        profile = self.get_or_create_profile(customer_id)
        if customer_name:
            profile.name = customer_name
        
        # Detect intent (includes proprietary check)
        intent = self.detect_intent(message)
        
        # Determine tone
        tone = preferred_tone or profile.preferred_tone
        
        # Special handling for internal questions
        if intent == CustomerIntent.INTERNAL_QUESTION:
            tone = ToneStyle.PROFESSIONAL  # Always professional for refusals
        
        # Generate response
        response = self._generate_response(intent, tone, profile, message)
        
        # Record interaction
        interaction = InteractionMemory(
            timestamp=datetime.now().isoformat(),
            customer_id=customer_id,
            intent=intent.value,
            query=message,
            response=response,
        )
        profile.add_interaction(interaction)
        self._save_profiles()
        
        return {
            "response": response,
            "intent": intent.value,
            "tone": tone.value,
            "customer_id": customer_id,
            "escalation_needed": intent in [CustomerIntent.COMPLAINT, CustomerIntent.REFUND],
            "was_refusal": intent == CustomerIntent.INTERNAL_QUESTION,
            "learning_applied": True,
        }
    
    def _generate_response(
        self,
        intent: CustomerIntent,
        tone: ToneStyle,
        profile: CustomerProfile,
        original_message: str
    ) -> str:
        """Generate a PROPRIETARY-SAFE response."""
        
        # Handle internal questions with refusal
        if intent == CustomerIntent.INTERNAL_QUESTION:
            import random
            return random.choice(self.REFUSAL_MESSAGES)
        
        # Get templates for this intent
        templates = self._response_templates.get(intent, {})
        tone_templates = templates.get(tone, templates.get(ToneStyle.PROFESSIONAL, ["I'm here to help!"]))
        
        # Select response
        import random
        response = random.choice(tone_templates)
        
        # Personalize if known
        if profile.name:
            response = f"Hi {profile.name}! {response}"
        
        return response
    
    def get_safe_description(self, topic: str) -> str:
        """Get a PROPRIETARY-SAFE description of how things work."""
        return self.SAFE_DESCRIPTIONS.get(topic, "That information is proprietary.")
    
    def provide_feedback(self, customer_id: str, interaction_timestamp: str, satisfied: bool, feedback_text: Optional[str] = None):
        """Learn from customer feedback."""
        profile = self._profiles.get(customer_id)
        if not profile:
            return
        
        for interaction in profile.interaction_history:
            if interaction.timestamp == interaction_timestamp:
                interaction.resolution = satisfied
                interaction.feedback = feedback_text
                
                if satisfied:
                    self._learning_data["successful_responses"].append({
                        "intent": interaction.intent,
                        "response": interaction.response,
                    })
                else:
                    self._learning_data["failed_responses"].append({
                        "intent": interaction.intent,
                        "response": interaction.response,
                        "feedback": feedback_text,
                    })
                break
        
        self._save_profiles()
    
    def _load_profiles(self):
        """Load customer profiles from disk."""
        profile_file = self.data_dir / f"profiles_{self.model_id}.json"
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cust_id, profile_data in data.items():
                        # Deserialize interaction_history dicts into InteractionMemory objects
                        raw_history = profile_data.pop('interaction_history', [])
                        interactions = []
                        for item in raw_history:
                            if isinstance(item, dict):
                                interactions.append(InteractionMemory(
                                    timestamp=item.get('timestamp', ''),
                                    customer_id=item.get('customer_id', ''),
                                    intent=item.get('intent', 'general'),
                                    query=item.get('query', ''),
                                    response=item.get('response', ''),
                                    resolution=item.get('resolution', False),
                                    feedback=item.get('feedback'),
                                ))
                            else:
                                interactions.append(item)
                        # Deserialize preferred_tone string into ToneStyle enum
                        raw_tone = profile_data.pop('preferred_tone', 'professional')
                        if isinstance(raw_tone, str):
                            try:
                                preferred_tone = ToneStyle(raw_tone)
                            except ValueError:
                                preferred_tone = ToneStyle.PROFESSIONAL
                        else:
                            preferred_tone = raw_tone
                        self._profiles[cust_id] = CustomerProfile(
                            customer_id=profile_data.get('customer_id', cust_id),
                            name=profile_data.get('name'),
                            preferred_tone=preferred_tone,
                            interaction_history=interactions,
                            common_issues=profile_data.get('common_issues', []),
                            satisfaction_score=profile_data.get('satisfaction_score', 0.0),
                        )
            except Exception:
                pass
    
    def _save_profiles(self):
        """Save customer profiles to disk."""
        profile_file = self.data_dir / f"profiles_{self.model_id}.json"
        try:
            data = {
                cust_id: {
                    "customer_id": p.customer_id,
                    "name": p.name,
                    "preferred_tone": p.preferred_tone.value,
                    "interaction_history": [
                        {
                            "timestamp": i.timestamp,
                            "customer_id": i.customer_id,
                            "intent": i.intent,
                            "query": i.query,
                            "response": i.response,
                            "resolution": i.resolution,
                            "feedback": i.feedback,
                        }
                        for i in p.interaction_history
                    ],
                    "common_issues": p.common_issues,
                    "satisfaction_score": p.satisfaction_score,
                }
                for cust_id, p in self._profiles.items()
            }
            with open(profile_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the AI's performance."""
        total_interactions = sum(len(p.interaction_history) for p in self._profiles.values())
        successful_resolutions = sum(
            sum(1 for i in p.interaction_history if i.resolution)
            for p in self._profiles.values()
        )
        
        return {
            "total_customers": len(self._profiles),
            "total_interactions": total_interactions,
            "successful_resolutions": successful_resolutions,
            "success_rate": successful_resolutions / total_interactions if total_interactions > 0 else 0,
            "model_id": self.model_id,
            "restricted_mode": True,  # Flag to indicate this is the safe version
        }


# Factory function
def create_public_customer_ai(model_id: str = "public") -> CustomerAIPublic:
    """Create the RESTRICTED customer AI for public use."""
    return CustomerAIPublic(model_id=model_id)
