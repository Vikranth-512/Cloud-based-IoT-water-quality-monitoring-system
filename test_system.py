#!/usr/bin/env python3
"""
Test script for Water Quality Monitoring System
"""

import requests
import json
import time
from datetime import datetime, timezone

API_BASE = "http://localhost:8000/api"

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{API_BASE.replace('/api', '')}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_ingest():
    """Test data ingestion"""
    test_data = {
        "device_id": "test_unit_001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": 25.5,
        "ec": 1.2,
        "tds": 600.0,
        "wqi": 85.5,
        "irrigation_index": "Moderate"
    }
    
    try:
        response = requests.post(f"{API_BASE}/ingest", json=test_data)
        if response.status_code == 200:
            print("✓ Data ingestion successful")
            return True
        else:
            print(f"✗ Data ingestion failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Data ingestion error: {e}")
        return False

def test_latest():
    """Test latest reading endpoint"""
    try:
        response = requests.get(f"{API_BASE}/latest")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Latest reading: {data['temperature']}°C, EC: {data['ec']} mS/cm")
            return True
        elif response.status_code == 404:
            print("✓ Latest reading endpoint working (no data yet)")
            return True
        else:
            print(f"✗ Latest reading failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Latest reading error: {e}")
        return False

def test_history():
    """Test history endpoint"""
    try:
        response = requests.get(f"{API_BASE}/history?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ History endpoint returned {len(data)} records")
            return True
        else:
            print(f"✗ History endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ History endpoint error: {e}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    try:
        response = requests.get(f"{API_BASE}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Metrics: {data['total_records']} records, Avg WQI: {data['avg_wqi']}")
            return True
        else:
            print(f"✗ Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Metrics endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Water Quality Monitoring System")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Data Ingestion", test_ingest),
        ("Latest Reading", test_latest),
        ("History", test_history),
        ("Metrics", test_metrics)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        if test_func():
            passed += 1
        time.sleep(0.5)  # Small delay between tests
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
