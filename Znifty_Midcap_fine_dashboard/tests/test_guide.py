#!/usr/bin/env python3
"""Test script to verify Guide tab implementation"""

import requests
import json

def test_api():
    print("=" * 60)
    print("TEST 1: Testing /api/get-guide endpoint")
    print("=" * 60)
    
    try:
        response = requests.get('http://127.0.0.1:8000/api/get-guide')
        print(f"✓ Status Code: {response.status_code}")
        
        data = response.json()
        print(f"✓ Success: {data['success']}")
        print(f"✓ Content length: {len(data.get('content', ''))} bytes")
        
        if len(data.get('content', '')) > 0:
            print(f"✓ First 100 chars: {data['content'][:100]}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_dashboard():
    print("\n" + "=" * 60)
    print("TEST 2: Checking dashboard HTML")
    print("=" * 60)
    
    try:
        response = requests.get('http://127.0.0.1:8000/')
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ HTML size: {len(response.text)} bytes")
        
        checks = {
            "'Guide' tab button": 'onclick="switchTab(\'guide\')"' in response.text,
            "'id=\"guide\"' container": 'id="guide"' in response.text,
            "'loadGuide()' function": 'function loadGuide()' in response.text,
            "'marked.min.js' library": 'marked/marked.min.js' in response.text,
            "'.tab-content' CSS": '.tab-content' in response.text,
            "'.tab-content.active' CSS": '.tab-content.active' in response.text,
        }
        
        all_pass = True
        for check_name, result in checks.items():
            status = "✓" if result else "✗"
            print(f"{status} Contains {check_name}: {result}")
            if not result:
                all_pass = False
        
        return all_pass
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_marked_lib():
    print("\n" + "=" * 60)
    print("TEST 3: Checking marked.js CDN availability")
    print("=" * 60)
    
    try:
        response = requests.get('https://cdn.jsdelivr.net/npm/marked/marked.min.js', timeout=5)
        print(f"✓ CDN Status Code: {response.status_code}")
        print(f"✓ Library size: {len(response.text)} bytes")
        return True
    except Exception as e:
        print(f"✗ Error accessing CDN: {e}")
        return False

if __name__ == '__main__':
    results = []
    results.append(('API Endpoint', test_api()))
    results.append(('Dashboard HTML', test_dashboard()))
    results.append(('marked.js CDN', test_marked_lib()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_pass = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_pass else "Some tests failed!"))
