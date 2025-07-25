from better_profanity import profanity
import re

# Initialize profanity filter
profanity.load_censor_words()

# Add Chinese profanity words (basic set - Traditional Chinese)
chinese_profanity = [
    "傻逼", "白痴", "笨蛋", "混蛋", "王八蛋", "操", "他媽的", "去死", "滾", "靠",
    "幹", "屌", "雞掰", "北七", "智障", "低能", "垃圾", "廢物", "狗屎", "死",
    "殺", "三小", "靠北", "媽的", "他奶奶的", "機掰", "87", "盤子", "智能不足",
    "幹你", "幹妳", "干", "干你", "干妳"  # Additional variants
]
profanity.add_censor_words(chinese_profanity)


def is_username_clean(username: str) -> bool:
    """Check if username contains profanity"""
    if not username or len(username.strip()) == 0:
        return False
    
    print(f"🔍 Checking username profanity: '{username}'")
    
    # Check for profanity using better-profanity library
    if profanity.contains_profanity(username):
        print(f"❌ better-profanity detected: {username}")
        return False
    
    # Manual check for Chinese profanity (more reliable)
    for bad_word in chinese_profanity:
        if bad_word in username:
            print(f"❌ Chinese profanity detected: '{bad_word}' in '{username}'")
            return False
    
    # Additional checks for inappropriate patterns (but allow some system words for auto-generated usernames)
    username_lower = username.lower()
    
    # Check for reserved/inappropriate patterns
    inappropriate_patterns = [
        r'^admin$',  # Only exact match
        r'^root$',   # Only exact match
        r'^system$', # Only exact match
        r'fuck',
        r'shit',
        r'damn',
        r'hell',
        r'bitch',
        r'ass',
        r'sex'
    ]
    
    # Skip pattern check for auto-generated usernames (User_, GreenUser, EcoUser)
    if not (username_lower.startswith('user_') or 
            username_lower.startswith('greenuser') or 
            username_lower.startswith('ecouser')):
        for pattern in inappropriate_patterns:
            if re.search(pattern, username_lower):
                print(f"❌ Pattern detected: '{pattern}' in '{username}'")
                return False
    
    print(f"✅ Username clean: '{username}'")
    return True


def clean_username(username: str) -> str:
    """Clean username by removing inappropriate content"""
    if not username:
        return ""
    
    # Remove extra whitespace
    cleaned = username.strip()
    
    # Censor profanity
    cleaned = profanity.censor(cleaned)
    
    return cleaned