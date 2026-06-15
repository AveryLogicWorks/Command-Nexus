"""
EXPANDED PARENTAL CONTROLS SYSTEM
==================================

Comprehensive parental control options beyond basic age ratings.
Includes behavioral controls, topic filtering, monitoring, and more.

These are USER-CONFIGURABLE restrictions (different from baseline guardrails).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum, auto
from datetime import time, timedelta


class RestrictionLevel(Enum):
    """Level of restriction strictness."""
    NONE = auto()  # No restriction
    LIGHT = auto()  # Minimal filtering
    MODERATE = auto()  # Standard protection
    STRICT = auto()  # Heavy filtering
    MAXIMUM = auto()  # Maximum lockdown


class TimeRestrictionType(Enum):
    """Types of time-based restrictions."""
    DAILY_LIMIT = auto()  # X hours per day
    SESSION_LIMIT = auto()  # X minutes per session
    SCHEDULED_ACCESS = auto()  # Only during specific hours
    BEDTIME_MODE = auto()  # No access after bedtime
    BREAK_REMINDERS = auto()  # Force breaks every X minutes


@dataclass
class TopicRestriction:
    """A specific topic that can be restricted."""
    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    category: str = "general"
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class BehavioralRule:
    """A behavioral control rule."""
    id: str
    name: str
    description: str
    rule_type: TimeRestrictionType
    value: any  # Interpretation depends on type
    enabled: bool = False


@dataclass
class MonitoringSetting:
    """A monitoring and alert setting."""
    id: str
    name: str
    description: str
    enabled: bool = False
    alert_parents: bool = True
    log_activity: bool = True
    sensitivity: str = "medium"  # low, medium, high


# EXPANDED TOPIC RESTRICTIONS DATABASE
# These can be toggled on/off by parents

TOPIC_RESTRICTIONS = [
    # === MATURE CONTENT ===
    TopicRestriction(
        id="dating_relationships",
        name="Dating & Relationships",
        description="Discussions about dating, romance, breakups, relationship advice",
        keywords=["dating", "boyfriend", "girlfriend", "breakup", "romance", "crush", "love life"],
        category="mature",
        severity="medium"
    ),
    TopicRestriction(
        id="sexual_education",
        name="Sexual Education",
        description="Sex education, reproductive health, contraception (not explicit content)",
        keywords=["sex", "contraception", "reproductive", "pregnancy", "STD", "birth control"],
        category="mature",
        severity="medium"
    ),
    TopicRestriction(
        id="substances",
        name="Drugs, Alcohol & Tobacco",
        description="Information about recreational drugs, alcohol, vaping, smoking",
        keywords=["drugs", "alcohol", "weed", "marijuana", "vaping", "smoking", "tobacco", "drinking"],
        category="mature",
        severity="high"
    ),
    TopicRestriction(
        id="gambling",
        name="Gambling & Betting",
        description="Casinos, betting, lottery, gambling strategies",
        keywords=["gambling", "betting", "casino", "lottery", "poker", "slots", "sports betting"],
        category="mature",
        severity="high"
    ),
    
    # === VIOLENCE & SCARY CONTENT ===
    TopicRestriction(
        id="cartoon_violence",
        name="Cartoon/Fantasy Violence",
        description="Mild violence in cartoons, fantasy battles, video game combat",
        keywords=["cartoon fight", "fantasy battle", "video game violence", "superhero fight"],
        category="violence",
        severity="low"
    ),
    TopicRestriction(
        id="realistic_violence",
        name="Realistic Violence",
        description="Real-world violence, crime, fighting, gore",
        keywords=["violence", "fighting", "blood", "gore", "crime", "attack", "assault"],
        category="violence",
        severity="high"
    ),
    TopicRestriction(
        id="mild_horror",
        name="Mild Scary Content",
        description="Ghosts, monsters, Halloween themes (not nightmare-inducing)",
        keywords=["ghost", "monster", "vampire", "zombie", "haunted", "spooky"],
        category="violence",
        severity="low"
    ),
    TopicRestriction(
        id="intense_horror",
        name="Intense Horror",
        description="Psychological horror, disturbing content, nightmare material",
        keywords=["horror", "nightmare", "psychological horror", "disturbing", "trauma"],
        category="violence",
        severity="high"
    ),
    TopicRestriction(
        id="weapons",
        name="Weapons & Combat",
        description="Guns, knives, martial arts, warfare (not how-to-make)",
        keywords=["gun", "weapon", "knife", "sword", "war", "military", "combat"],
        category="violence",
        severity="medium"
    ),
    
    # === POLITICS & RELIGION ===
    TopicRestriction(
        id="politics_general",
        name="General Politics",
        description="Political discussions, elections, government, policies",
        keywords=["politics", "election", "government", "democrat", "republican", "vote"],
        category="sensitive",
        severity="medium"
    ),
    TopicRestriction(
        id="politics_partisan",
        name="Partisan Politics",
        description="Biased political content, partisan attacks, political extremism",
        keywords=["liberal", "conservative", "leftist", "right-wing", "partisan", "extremist"],
        category="sensitive",
        severity="high"
    ),
    TopicRestriction(
        id="religion_general",
        name="Religious Education",
        description="Learning about religions, religious history, beliefs overview",
        keywords=["religion", "christianity", "islam", "judaism", "buddhism", "hinduism"],
        category="sensitive",
        severity="low"
    ),
    TopicRestriction(
        id="religion_proselytizing",
        name="Religious Proselytizing",
        description="Converting others, religious recruitment, denominational promotion",
        keywords=["convert", "salvation", "missionary", "join my church", "true religion"],
        category="sensitive",
        severity="high"
    ),
    TopicRestriction(
        id="conspiracy_theories",
        name="Conspiracy Theories",
        description="Unproven conspiracy theories, misinformation, pseudoscience",
        keywords=["conspiracy", "hoax", "fake news", "cover-up", "they don't want you to know"],
        category="sensitive",
        severity="high"
    ),
    
    # === BODY IMAGE & SELF-ESTEEM ===
    TopicRestriction(
        id="body_image",
        name="Body Image & Appearance",
        description="Weight loss, body modification, cosmetic surgery, beauty standards",
        keywords=["weight loss", "diet", "plastic surgery", "body image", "ugly", "fat", "skinny"],
        category="mental_health",
        severity="medium"
    ),
    TopicRestriction(
        id="eating_disorders",
        name="Eating Disorder Content",
        description="Anorexia, bulimia, binge eating discussions (can be triggering)",
        keywords=["anorexia", "bulimia", "binge", "purge", "starving", "thinspo"],
        category="mental_health",
        severity="critical"
    ),
    TopicRestriction(
        id="self_harm",
        name="Self-Harm Discussions",
        description="Cutting, self-injury, suicidal ideation (triggers)",
        keywords=["self harm", "cutting", "suicide", "kill myself", "end it all", "worthless"],
        category="mental_health",
        severity="critical"
    ),
    TopicRestriction(
        id="depression_anxiety",
        name="Depression & Anxiety",
        description="Mental health struggles (may need careful handling)",
        keywords=["depression", "anxiety", "hopeless", "worthless", "panic attack"],
        category="mental_health",
        severity="high"
    ),
    
    # === SOCIAL & COMPETITIVE ===
    TopicRestriction(
        id="social_media",
        name="Social Media Culture",
        description="Influencers, trends, viral content, social media strategies",
        keywords=["influencer", "viral", "tiktok", "instagram", "likes", "followers", "trending"],
        category="social",
        severity="low"
    ),
    TopicRestriction(
        id="celebrity_gossip",
        name="Celebrity Gossip",
        description="Celebrity news, rumors, drama, entertainment industry",
        keywords=["celebrity", "gossip", "drama", "scandal", "feud", "breakup", "paparazzi"],
        category="social",
        severity="low"
    ),
    TopicRestriction(
        id="consumerism",
        name="Consumerism & Shopping",
        description="Product pushing, excessive materialism, shopping addiction",
        keywords=["buy this", "you need this", "sale", "limited edition", "must have"],
        category="social",
        severity="low"
    ),
    TopicRestriction(
        id="competitive_gaming",
        name="Competitive Gaming/Esports",
        description="Esports, competitive gaming culture, ranked matches",
        keywords=["esports", "competitive", "ranked", "tournament", "pro player", "elo"],
        category="social",
        severity="low"
    ),
    
    # === ADULT RESPONSIBILITIES ===
    TopicRestriction(
        id="finance_money",
        name="Personal Finance",
        description="Money management, taxes, debt, investments, credit",
        keywords=["credit card", "debt", "loan", "mortgage", "taxes", "investment", "stock"],
        category="adult",
        severity="low"
    ),
    TopicRestriction(
        id="career_work",
        name="Career & Work Stress",
        description="Job stress, workplace issues, career anxiety, office politics",
        keywords=["job stress", "boss", "coworker", "layoff", "fired", "office politics"],
        category="adult",
        severity="medium"
    ),
    TopicRestriction(
        id="family_conflicts",
        name="Family Conflicts",
        description="Divorce, custody, family drama, inheritance disputes",
        keywords=["divorce", "custody", "inheritance", "family drama", "step-parent"],
        category="adult",
        severity="medium"
    ),
    
    # === EDUCATIONAL RESTRICTIONS (for focus mode) ===
    TopicRestriction(
        id="entertainment",
        name="Entertainment Only",
        description="Games, fun, jokes, non-educational content (when focus mode on)",
        keywords=["game", "fun", "joke", "entertainment", "movie", "TV show", "netflix"],
        category="educational",
        severity="low"
    ),
    TopicRestriction(
        id="off_topic",
        name="Off-Topic Discussions",
        description="Conversations not related to current task/study topic",
        keywords=[],  # Context-dependent
        category="educational",
        severity="low"
    ),
]


# BEHAVIORAL CONTROL RULES
# Time limits, scheduling, etc.

BEHAVIORAL_RULES = [
    BehavioralRule(
        id="daily_time_limit",
        name="Daily Time Limit",
        description="Maximum hours allowed per day",
        rule_type=TimeRestrictionType.DAILY_LIMIT,
        value=2,  # hours
        enabled=False
    ),
    BehavioralRule(
        id="session_time_limit",
        name="Session Time Limit",
        description="Maximum minutes per continuous session",
        rule_type=TimeRestrictionType.SESSION_LIMIT,
        value=30,  # minutes
        enabled=False
    ),
    BehavioralRule(
        id="break_reminders",
        name="Break Reminders",
        description="Remind to take a break every X minutes",
        rule_type=TimeRestrictionType.BREAK_REMINDERS,
        value=20,  # minutes
        enabled=False
    ),
    BehavioralRule(
        id="bedtime_mode",
        name="Bedtime Mode",
        description="No AI access after bedtime",
        rule_type=TimeRestrictionType.BEDTIME_MODE,
        value=time(21, 0),  # 9:00 PM
        enabled=False
    ),
    BehavioralRule(
        id="scheduled_access",
        name="Scheduled Access Hours",
        description="Only allow access during specific hours",
        rule_type=TimeRestrictionType.SCHEDULED_ACCESS,
        value=(time(15, 0), time(19, 0)),  # 3 PM - 7 PM
        enabled=False
    ),
]


# MONITORING SETTINGS
# What parents can monitor and be alerted about

MONITORING_SETTINGS = [
    MonitoringSetting(
        id="alert_restricted_topics",
        name="Alert on Restricted Topics",
        description="Notify parent when child asks about blocked topics",
        enabled=True,
        alert_parents=True,
        log_activity=True,
        sensitivity="high"
    ),
    MonitoringSetting(
        id="alert_concerning_content",
        name="Alert on Concerning Content",
        description="Alert if child discusses self-harm, depression, abuse, etc.",
        enabled=True,
        alert_parents=True,
        log_activity=True,
        sensitivity="high"
    ),
    MonitoringSetting(
        id="alert_personal_info",
        name="Alert on Personal Info Sharing",
        description="Alert if child attempts to share address, phone, school name, etc.",
        enabled=True,
        alert_parents=True,
        log_activity=True,
        sensitivity="high"
    ),
    MonitoringSetting(
        id="alert_external_links",
        name="Alert on External Link Requests",
        description="Alert if AI suggests visiting external websites",
        enabled=False,
        alert_parents=True,
        log_activity=True,
        sensitivity="medium"
    ),
    MonitoringSetting(
        id="weekly_reports",
        name="Weekly Activity Reports",
        description="Email weekly summary of AI usage to parents",
        enabled=True,
        alert_parents=False,
        log_activity=True,
        sensitivity="low"
    ),
    MonitoringSetting(
        id="flagged_review",
        name="Flagged Content Review Queue",
        description="Review potentially concerning conversations",
        enabled=True,
        alert_parents=False,
        log_activity=True,
        sensitivity="medium"
    ),
    MonitoringSetting(
        id="time_tracking",
        name="Detailed Time Tracking",
        description="Track exactly how long child uses AI each day",
        enabled=True,
        alert_parents=False,
        log_activity=True,
        sensitivity="low"
    ),
]


# AGE-BASED PRESETS
# Quick configuration based on age

AGE_PRESETS = {
    "child": {
        "name": "Child (5-8 years)",
        "description": "Maximum protection for young children",
        "restrictions": [
            "dating_relationships", "sexual_education", "substances", "gambling",
            "realistic_violence", "intense_horror", "weapons", "politics_partisan",
            "religion_proselytizing", "conspiracy_theories", "body_image", "eating_disorders",
            "self_harm", "depression_anxiety", "family_conflicts", "career_work"
        ],
        "behavioral_rules": ["daily_time_limit", "session_time_limit", "break_reminders", "bedtime_mode"],
        "monitoring": ["alert_restricted_topics", "alert_concerning_content", "alert_personal_info", "weekly_reports"]
    },
    "preteen": {
        "name": "Pre-Teen (9-12 years)",
        "description": "Moderate protection with some educational exceptions",
        "restrictions": [
            "sexual_education", "substances", "gambling", "realistic_violence",
            "intense_horror", "politics_partisan", "religion_proselytizing",
            "conspiracy_theories", "eating_disorders", "self_harm", "depression_anxiety"
        ],
        "behavioral_rules": ["daily_time_limit", "break_reminders", "bedtime_mode"],
        "monitoring": ["alert_restricted_topics", "alert_concerning_content", "weekly_reports", "flagged_review"]
    },
    "teen": {
        "name": "Teen (13-17 years)",
        "description": "Light protection with safety monitoring",
        "restrictions": [
            "substances", "gambling", "intense_horror", "conspiracy_theories",
            "eating_disorders", "self_harm"
        ],
        "behavioral_rules": ["daily_time_limit"],
        "monitoring": ["alert_concerning_content", "alert_personal_info", "weekly_reports"]
    },
    "focus_mode": {
        "name": "Study Focus Mode",
        "description": "Block distractions for homework time",
        "restrictions": [
            "entertainment", "social_media", "celebrity_gossip", "consumerism",
            "competitive_gaming", "off_topic"
        ],
        "behavioral_rules": ["session_time_limit", "break_reminders"],
        "monitoring": ["time_tracking"]
    }
}


# INTERACTION SAFETY SETTINGS
# Prevent dangerous interactions

INTERACTION_SAFETY = [
    {
        "id": "block_personal_info",
        "name": "Block Personal Information Sharing",
        "description": "Prevent child from sharing address, phone, real name, school",
        "enabled": True,
        "keywords": ["my address", "my phone", "my name is", "I live at", "my school is", "my email"]
    },
    {
        "id": "block_location_sharing",
        "name": "Block Location Requests",
        "description": "Prevent AI from asking for or suggesting location sharing",
        "enabled": True,
        "keywords": ["where are you", "send me your location", "what city", "GPS coordinates"]
    },
    {
        "id": "block_photo_requests",
        "name": "Block Photo/Video Requests",
        "description": "Prevent requests for photos, videos, or camera access",
        "enabled": True,
        "keywords": ["send me a photo", "show me your face", "video call", "take a picture"]
    },
    {
        "id": "block_meet_requests",
        "name": "Block Meeting Requests",
        "description": "Prevent suggestions to meet in person",
        "enabled": True,
        "keywords": ["let's meet", "meet up", "in person", "see you", "hang out together"]
    },
    {
        "id": "block_platform_redirect",
        "name": "Block Platform Redirects",
        "description": "Prevent suggesting to move conversation to other apps/platforms",
        "enabled": True,
        "keywords": ["add me on", "message me on", "talk on snapchat", "follow me on", "DM me"]
    },
    {
        "id": "block_external_links",
        "name": "Block External Links",
        "description": "Prevent AI from sharing links to external websites",
        "enabled": False,  # Off by default, can be enabled
        "keywords": ["http", "www.", ".com", "click here", "visit this site"]
    }
]


def get_restrictions_by_category(category: str) -> List[TopicRestriction]:
    """Get all restrictions in a category."""
    return [r for r in TOPIC_RESTRICTIONS if r.category == category]


def get_preset_ages() -> Dict:
    """Get all age presets."""
    return AGE_PRESETS


def apply_age_preset(preset_name: str) -> Dict:
    """Apply an age preset and return the configuration."""
    preset = AGE_PRESETS.get(preset_name)
    if not preset:
        return {}
    
    config = {
        "name": preset["name"],
        "description": preset["description"],
        "active_restrictions": [],
        "active_rules": [],
        "active_monitoring": []
    }
    
    # Build restriction objects
    for rid in preset["restrictions"]:
        restriction = next((r for r in TOPIC_RESTRICTIONS if r.id == rid), None)
        if restriction:
            config["active_restrictions"].append(restriction)
    
    # Build behavioral rules
    for rule_id in preset["behavioral_rules"]:
        rule = next((r for r in BEHAVIORAL_RULES if r.id == rule_id), None)
        if rule:
            config["active_rules"].append(rule)
    
    # Build monitoring settings
    for mon_id in preset["monitoring"]:
        setting = next((s for s in MONITORING_SETTINGS if s.id == mon_id), None)
        if setting:
            config["active_monitoring"].append(setting)
    
    return config


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("EXPANDED PARENTAL CONTROLS SYSTEM")
    print("=" * 60)
    
    print(f"\nTotal Topic Restrictions: {len(TOPIC_RESTRICTIONS)}")
    print(f"Behavioral Rules: {len(BEHAVIORAL_RULES)}")
    print(f"Monitoring Options: {len(MONITORING_SETTINGS)}")
    print(f"Age Presets: {len(AGE_PRESETS)}")
    
    print("\n" + "=" * 60)
    print("TOPIC RESTRICTIONS BY CATEGORY")
    print("-" * 60)
    categories = set(r.category for r in TOPIC_RESTRICTIONS)
    for category in sorted(categories):
        restrictions = get_restrictions_by_category(category)
        print(f"\n{category.upper().replace('_', ' ')} ({len(restrictions)} items):")
        for r in restrictions:
            print(f"  • {r.name} ({r.severity})")
    
    print("\n" + "=" * 60)
    print("AGE PRESETS")
    print("-" * 60)
    for key, preset in AGE_PRESETS.items():
        config = apply_age_preset(key)
        print(f"\n{preset['name']}")
        print(f"  Description: {preset['description']}")
        print(f"  Active Restrictions: {len(config['active_restrictions'])}")
        print(f"  Behavioral Rules: {len(config['active_rules'])}")
        print(f"  Monitoring: {len(config['active_monitoring'])}")
