"""
Command Nexus™ Adaptive Customer AI Model
=========================================
A lightweight, learning-capable AI system for customer communication.
Designed to handle inquiries, learn from interactions, and adapt its responses.

Features:
- Natural language understanding for customer intents
- Contextual memory of past interactions (per customer)
- Learning from successful resolutions
- Adaptive tone matching (professional, friendly, technical)
- Integration with Command Nexus AI Forge
- BASELINE GUARDRAILS INTEGRATION - Safety checks on all content

This is NOT a full neural network - it's a rule-based + learning system
that provides intelligent responses while being lightweight and fast.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .baseline_guardrails import check_baseline_guardrails


class CustomerIntent(Enum):
    """Recognizable customer intents."""
    PRICING = "pricing"
    SUPPORT = "support"
    BILLING = "billing"
    PRODUCT_INFO = "product_info"
    COMPLAINT = "complaint"
    REFUND = "refund"
    TECHNICAL = "technical"
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
    resolution: bool = False  # Was the customer satisfied?
    feedback: Optional[str] = None
    

@dataclass
class CustomerProfile:
    """Profile for a specific customer."""
    customer_id: str
    name: Optional[str] = None
    preferred_tone: ToneStyle = ToneStyle.PROFESSIONAL
    interaction_history: List[InteractionMemory] = field(default_factory=list)
    common_issues: List[str] = field(default_factory=list)
    satisfaction_score: float = 0.0  # 0.0 to 1.0
    
    def add_interaction(self, interaction: InteractionMemory):
        """Add an interaction and update learning."""
        self.interaction_history.append(interaction)
        # Update satisfaction score
        if interaction.resolution:
            self.satisfaction_score = min(1.0, self.satisfaction_score + 0.1)
        else:
            self.satisfaction_score = max(0.0, self.satisfaction_score - 0.05)
        # Learn common issues
        if interaction.intent not in self.common_issues:
            self.common_issues.append(interaction.intent)


class CustomerAIModel:
    """
    Adaptive AI for customer communication.
    Learns from interactions and adapts responses.
    """
    
    def __init__(self, model_id: str = "default", data_dir: Optional[Path] = None):
        self.model_id = model_id
        self.data_dir = data_dir or (Path.home() / ".command_nexus" / "customer_ai")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Customer profiles storage
        self._profiles: Dict[str, CustomerProfile] = {}
        self._load_profiles()
        
        # Intent recognition patterns
        self._intent_patterns = self._build_intent_patterns()
        
        # Response templates (expandable)
        self._response_templates = self._build_response_templates()
        
        # Learning data
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
            CustomerIntent.COMPLAINT: [
                r"\b(complaint|angry|frustrated|terrible|awful|worst|hate|useless)\b",
                r"\b(disappointed|unsatisfied|bad service|rip off|scam)\b",
            ],
            CustomerIntent.PRODUCT_INFO: [
                r"\b(features|capabilities|what.*do|how.*work|tell me about)\b",
                r"\b(capability|ai|forge|book|upgrade|premium|license)\b",
            ],
            CustomerIntent.GREETING: [
                r"\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b",
            ],
            CustomerIntent.FAREWELL: [
                r"\b(bye|goodbye|see you|thanks|thank you|have a good day)\b",
            ],
        }
    
    def _build_response_templates(self) -> Dict[CustomerIntent, Dict[ToneStyle, List[str]]]:
        """Build response templates for different intents and tones."""
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
            CustomerIntent.PRICING: {
                ToneStyle.PROFESSIONAL: [
                    "Our pricing tiers are:\n• Trial: $10 (15 days, 1 AI)\n• Starter: $20/mo (2 AIs)\n• Pro: $30/mo (4 AIs)\n• Business: $50/mo (5 AIs)\n• Unlimited: $80/mo (unlimited AIs)\n\nWould you like more details on any tier?",
                    "We offer several license tiers to fit your needs. You can view full pricing at our website or I can walk you through the options. Which would you prefer?",
                ],
                ToneStyle.FRIENDLY: [
                    "Great question! We've got options for everyone:\n\n🚀 Trial: $10 — test drive for 15 days\n⭐ Starter: $20/mo — perfect for personal use\n💎 Pro: $30/mo — great for professionals\n🏢 Business: $50/mo — team power!\n∞ Unlimited: $80/mo — go wild!\n\nWhat sounds right for you?",
                ],
            },
            CustomerIntent.SUPPORT: {
                ToneStyle.EMPATHETIC: [
                    "I'm sorry you're experiencing this issue. Let me help you resolve it right away.\n\nCould you tell me:\n1. What you were trying to do\n2. What happened instead\n3. Any error messages you saw",
                    "I understand how frustrating technical issues can be. Don't worry - we'll get this sorted out together. What specifically is happening?",
                ],
                ToneStyle.TECHNICAL: [
                    "I can help troubleshoot this. Please provide:\n• Error logs (if any)\n• Steps to reproduce\n• Your system details (OS, version)\n• Screenshot if applicable",
                ],
            },
            CustomerIntent.BILLING: {
                ToneStyle.PROFESSIONAL: [
                    "I can help with billing inquiries. For security, I'll need to verify your account. Please provide your registered email or license key (last 4 digits only).",
                    "Billing questions are important. Let me assist you. What specific billing issue are you experiencing?",
                ],
            },
            CustomerIntent.REFUND: {
                ToneStyle.EMPATHETIC: [
                    "I understand you'd like a refund. I want to make this right for you.\n\nLet me check your eligibility. Could you provide:\n• Your license key or email\n• Reason for the refund\n• When you purchased",
                    "I'm sorry our product didn't meet your expectations. Let's process your refund request. I'll need some basic information to locate your order.",
                ],
            },
            CustomerIntent.COMPLAINT: {
                ToneStyle.EMPATHETIC: [
                    "I sincerely apologize for your experience. This is not the standard we strive for.\n\nI'm escalating this to our support team immediately. You'll hear back within 24 hours with a resolution.\n\nIs there anything I can do right now to help?",
                    "I'm truly sorry you've had this experience. Your feedback is valuable and will help us improve.\n\nA senior support agent will contact you directly within 24 hours to make this right.",
                ],
            },
            CustomerIntent.PRODUCT_INFO: {
                ToneStyle.FRIENDLY: [
                    "Command Nexus™ is your AI command center! Here's what it does:\n\n🧠 AI Forge — Create custom AI assistants\n📚 Knowledge System — Give your AIs memory\n🛡️ Governance — Built-in safety controls\n🔐 License Tiers — Scale as you grow\n\nWant to know more about any feature?",
                ],
                ToneStyle.PROFESSIONAL: [
                    "Command Nexus™ provides:\n\n• AI Creation & Customization (Forge)\n• Persistent AI Memory & Knowledge\n• Enterprise-grade Governance\n• Scalable Licensing\n• Anti-tamper Security\n\nWhich aspect interests you most?",
                ],
            },
            CustomerIntent.GENERAL: {
                ToneStyle.PROFESSIONAL: [
                    "I'm here to help! Could you provide more details about what you need assistance with?",
                    "I'd be happy to assist you. What can I do for you today?",
                ],
                ToneStyle.FRIENDLY: [
                    "I'm all ears! What's on your mind?",
                    "Happy to help! Tell me what's up!",
                ],
            },
        }
    
    def detect_intent(self, message: str) -> CustomerIntent:
        """Detect the customer's intent from their message."""
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
            # Return highest scoring intent
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
        Process a customer message and generate a response.
        Returns a dict with response, intent, and learning data.
        """
        # BASELINE GUARDRAILS: Check incoming message
        blocked, rule, block_msg = check_baseline_guardrails(message, context="customer_support")
        if blocked:
            print(f"[GUARDRAIL BLOCKED] Rule: {rule.id if rule else 'unknown'} | Message: {message[:100]}")
            return {
                "response": block_msg,
                "intent": "blocked",
                "tone": "professional",
                "customer_id": customer_id,
                "escalation_needed": True,
                "learning_applied": False,
                "guardrail_triggered": True,
                "guardrail_rule": rule.id if rule else None,
            }
        else:
            print(f"[GUARDRAIL ALLOWED] Message: {message[:100]}")
        
        # Get or create customer profile
        profile = self.get_or_create_profile(customer_id)
        if customer_name:
            profile.name = customer_name
        
        # Detect intent
        intent = self.detect_intent(message)
        
        # Determine tone
        tone = preferred_tone or profile.preferred_tone
        
        # Check for escalations (complaints, urgent issues)
        if intent == CustomerIntent.COMPLAINT:
            tone = ToneStyle.EMPATHETIC
        
        # Generate response
        response = self._generate_response(intent, tone, profile, message)
        
        # BASELINE GUARDRAILS: Check outgoing response
        response_blocked, response_rule, response_block_msg = check_baseline_guardrails(response, context="customer_support")
        if response_blocked:
            response = response_block_msg  # Replace with safe fallback
        
        # Record interaction for learning
        interaction = InteractionMemory(
            timestamp=datetime.now().isoformat(),
            customer_id=customer_id,
            intent=intent.value,
            query=message,
            response=response,
        )
        profile.add_interaction(interaction)
        
        # Save updated profiles
        self._save_profiles()
        
        return {
            "response": response,
            "intent": intent.value,
            "tone": tone.value,
            "customer_id": customer_id,
            "escalation_needed": intent in [CustomerIntent.COMPLAINT, CustomerIntent.REFUND],
            "learning_applied": True,
            "guardrail_triggered": response_blocked,
            "guardrail_rule": response_rule.id if response_rule else None,
        }
    
    def _generate_response(
        self,
        intent: CustomerIntent,
        tone: ToneStyle,
        profile: CustomerProfile,
        original_message: str
    ) -> str:
        """Generate a response based on intent, tone, and profile."""
        # Get templates for this intent
        templates = self._response_templates.get(intent, {})
        
        # Get templates for this tone, or fall back to general
        tone_templates = templates.get(tone, templates.get(ToneStyle.PROFESSIONAL, ["I'm here to help!"]))
        
        # Select a response (could use ML to select best one)
        import random
        response = random.choice(tone_templates)
        
        # Personalize if we know the customer
        if profile.name:
            response = f"Hi {profile.name}! {response}"
        
        # Add context-aware additions based on history
        if len(profile.interaction_history) > 3:
            # They've talked to us before
            response += "\n\n(Thanks for being a returning customer! We appreciate your continued interest.)"
        
        return response
    
    def provide_feedback(
        self,
        customer_id: str,
        interaction_timestamp: str,
        satisfied: bool,
        feedback_text: Optional[str] = None
    ):
        """Learn from customer feedback about an interaction."""
        profile = self._profiles.get(customer_id)
        if not profile:
            return
        
        # Find the interaction
        for interaction in profile.interaction_history:
            if interaction.timestamp == interaction_timestamp:
                interaction.resolution = satisfied
                interaction.feedback = feedback_text
                
                # Update learning data
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
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    for cust_id, profile_data in data.items():
                        self._profiles[cust_id] = CustomerProfile(**profile_data)
            except Exception:
                pass  # Start fresh if corrupted
    
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
            pass  # Fail silently to avoid breaking customer experience
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the AI model's performance."""
        total_interactions = sum(
            len(p.interaction_history) for p in self._profiles.values()
        )
        
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
        }


# Factory function for Command Nexus integration
def create_customer_ai(model_id: str = "default") -> CustomerAIModel:
    """Create a customer AI instance for Command Nexus integration."""
    return CustomerAIModel(model_id=model_id)


# Example usage for testing
if __name__ == "__main__":
    # Create AI
    ai = create_customer_ai("demo")
    
    # Simulate customer interactions
    print("=== Command Nexus™ Customer AI Demo ===\n")
    
    # Customer 1 - New customer asking about pricing
    result = ai.process_message(
        "Hi! How much does Command Nexus cost?",
        customer_id="cust_001",
        customer_name="Alice"
    )
    print(f"Customer: Hi! How much does Command Nexus cost?")
    print(f"AI ({result['intent']}, {result['tone']}):\n{result['response']}\n")
    
    # Customer provides feedback
    ai.provide_feedback("cust_001", result['interaction_timestamp'], True, "Very helpful!")
    
    # Customer 2 - Angry customer
    result2 = ai.process_message(
        "This is terrible! I want a refund!",
        customer_id="cust_002"
    )
    print(f"Customer: This is terrible! I want a refund!")
    print(f"AI ({result2['intent']}, {result2['tone']}):\n{result2['response']}\n")
    
    # Show stats
    print("=== AI Learning Stats ===")
    stats = ai.get_stats()
    print(f"Customers: {stats['total_customers']}")
    print(f"Interactions: {stats['total_interactions']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
