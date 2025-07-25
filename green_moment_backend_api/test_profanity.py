#!/usr/bin/env python3

from app.utils.profanity import is_username_clean

# Test cases
test_usernames = [
    "幹你",
    "幹",
    "操",
    "他媽的",
    "fuck",
    "test",
    "hello",
    "測試用戶",
    "admin",
    "User_123"
]

print("Testing profanity filter:")
print("=" * 50)

for username in test_usernames:
    result = is_username_clean(username)
    status = "✅ CLEAN" if result else "❌ BLOCKED"
    print(f"{username:<10} -> {status}")

print("=" * 50)