#!/usr/bin/env python3
"""
Simple script to test if the backend API is working correctly.
Run this after starting the backend to verify all endpoints respond.
"""

import requests
import json
from datetime import datetime

# Base URL - change if your backend runs on different port
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def test_endpoint(method, endpoint, data=None, name=None):
    """Test a single endpoint and print results"""
    url = f"{API_V1}{endpoint}"
    display_name = name or endpoint
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            print(f"❌ Unknown method: {method}")
            return False
            
        if response.status_code < 400:
            print(f"✅ {display_name}: {response.status_code}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ {display_name}: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {display_name}: Connection failed - is the backend running?")
        return False
    except Exception as e:
        print(f"❌ {display_name}: {type(e).__name__} - {e}")
        return False

def main():
    print("🧪 Testing Green Moment Backend API")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print(f"✅ Backend is running at {BASE_URL}")
            print(f"   Version: {response.json().get('version', 'Unknown')}")
        else:
            print(f"❌ Backend root endpoint returned {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure the backend is running:")
        print("   docker-compose up -d")
        return
    
    print("\n📋 Testing API Endpoints")
    print("-" * 50)
    
    # Test all endpoints
    endpoints = [
        # Auth endpoints
        ("POST", "/auth/anonymous", None, "Anonymous Auth"),
        ("POST", "/auth/google", {"token": "test"}, "Google Auth"),
        ("POST", "/auth/verify", {"token": "test"}, "Verify Token"),
        
        # User endpoints
        ("GET", "/users/profile", None, "Get User Profile"),
        ("PUT", "/users/username", {"username": "TestUser"}, "Update Username"),
        
        # Carbon endpoints
        ("GET", "/carbon/current", None, "Current Carbon Intensity"),
        ("GET", "/carbon/forecast", None, "Carbon Forecast"),
        ("GET", "/carbon/historical", None, "Historical Carbon Data"),
        
        # Chore endpoints
        ("POST", "/chores/estimate", {
            "appliance_id": "washing_machine",
            "duration_hours": 2,
            "start_time": datetime.now().isoformat()
        }, "Estimate Savings"),
        ("POST", "/chores/log", {
            "appliance_id": "washing_machine",
            "duration_hours": 2,
            "start_time": datetime.now().isoformat()
        }, "Log Chore"),
        ("GET", "/chores/history", None, "Chore History"),
        
        # Progress endpoints
        ("GET", "/progress/summary", None, "Progress Summary"),
        ("GET", "/progress/tasks", None, "Current Tasks"),
        ("GET", "/progress/league", None, "League Info"),
    ]
    
    passed = 0
    failed = 0
    
    for method, endpoint, data, name in endpoints:
        if test_endpoint(method, endpoint, data, name):
            passed += 1
        else:
            failed += 1
    
    print("\n📊 Test Summary")
    print("-" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All endpoints are responding!")
        print("   Note: Endpoints return placeholder data until fully implemented.")
    else:
        print("\n⚠️  Some endpoints are not working properly.")
        print("   Check the backend logs: docker-compose logs -f api")
    
    print("\n📚 API Documentation")
    print("-" * 50)
    print(f"Swagger UI: {API_V1}/docs")
    print(f"ReDoc: {API_V1}/redoc")

if __name__ == "__main__":
    main()