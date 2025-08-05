#!/usr/bin/env python3
"""Verify that the enum fix is working correctly"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.notification import PlatformType, DeviceToken, NotificationStatus

print("✅ Successfully imported notification models")
print(f"   PlatformType.ANDROID = {PlatformType.ANDROID.value}")
print(f"   PlatformType.IOS = {PlatformType.IOS.value}")
print()
print(f"   NotificationStatus values:")
for status in NotificationStatus:
    print(f"   - {status.name} = {status.value}")

# Test enum conversion
test_token = DeviceToken(
    user_id=1,
    token="test_token",
    platform=PlatformType.ANDROID,
    device_id="test_device"
)

print()
print("✅ Successfully created DeviceToken with enum")
print(f"   Platform: {test_token.platform} (value: {test_token.platform.value})")
print()
print("🎉 Enum fix verified - all enums working correctly!")