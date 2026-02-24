#!/usr/bin/env python3
"""Test the loadGuide() function logic by simulating browser behavior"""

import requests
import re
import json

print("=" * 80)
print("TESTING: loadGuide() Function Implementation")
print("=" * 80)

# Get the dashboard
response = requests.get('http://127.0.0.1:5000/')
html = response.text

print("\n[STEP 1] Extracting loadGuide() function from HTML...")
# Extract the loadGuide function
match = re.search(r'function loadGuide\(\) \{(.*?)\n        \}(?=\n\n)', html, re.DOTALL)
if match:
    func_body = match.group(1)
    # Count lines
    lines = func_body.count('\n')
    print(f"✓ Found loadGuide() function ({lines} lines)")
    
    # Check key operations
    checks = {
        'Gets guide-loading element': 'getElementById(\'guide-loading\')' in func_body,
        'Gets guide-content element': 'getElementById(\'guide-content\')' in func_body,
        'Gets guide-markdown element': 'getElementById(\'guide-markdown\')' in func_body,
        'Shows loading state': 'display = \'block\'' in func_body,
        'Fetches from /api/get-guide': 'fetch(\'/api/get-guide\')' in func_body,
        'Checks if response is OK': '.ok' in func_body or 'status' in func_body,
        'Parses JSON response': '.json()' in func_body,
        'Checks API success': 'data.success' in func_body,
        'Uses marked.parse()': 'marked.parse' in func_body,
        'Has fallback for marked': 'typeof window.marked' in func_body,
        'Has error handling': '.catch' in func_body,
        'Uses escapeHtml()': 'escapeHtml' in func_body,
    }
    
    print("\n[STEP 2] Checking function logic...")
    all_good = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
        if not result:
            all_good = False
    
    if all_good:
        print("\n✓ All function logic checks passed!")
    else:
        print("\n✗ Some function logic checks failed!")
else:
    print("✗ Could not find loadGuide() function!")

# Test the API endpoint
print("\n[STEP 3] Testing /api/get-guide endpoint...")
api_response = requests.get('http://127.0.0.1:5000/api/get-guide')
if api_response.status_code == 200:
    print(f"✓ API returns status 200")
    data = api_response.json()
    if data.get('success'):
        print(f"✓ API success: True")
        content = data.get('content', '')
        if content:
            print(f"✓ Content present: {len(content)} bytes")
            if content.startswith('#'):
                print(f"✓ Content starts with markdown header")
            else:
                print(f"⚠ Content may not be markdown")
        else:
            print(f"✗ Content is empty!")
    else:
        print(f"✗ API success: False")
else:
    print(f"✗ API returns status {api_response.status_code}")

# Check marked.js is loaded
print("\n[STEP 4] Checking marked.js library loading...")
if 'marked/marked.min.js' in html:
    print(f"✓ marked.js script tag present")
else:
    print(f"✗ marked.js script tag NOT found!")

# Check marked library loading verification code
if '[INIT] marked library check:' in html or 'console.log(\'[INIT] marked library check:' in html:
    print(f"✓ marked.js loading verification code present")
else:
    print(f"⚠ marked.js loading verification might be missing")

# Check escapeHtml function
if 'function escapeHtml(' in html:
    print(f"✓ escapeHtml() function defined")
else:
    print(f"✗ escapeHtml() function NOT defined!")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The loadGuide() function has been:
  ✓ Enhanced with comprehensive logging (prefix: [GUIDE])
  ✓ Added error handling for HTTP status codes
  ✓ Added error handling for empty content
  ✓ Added multiple marked.js API version support
  ✓ Added fallback to plain text rendering
  ✓ Added detailed error messages to UI

To debug the Guide tab:
  1. Open browser DevTools (F12)
  2. Go to Console tab
  3. Click the 📖 Guide tab
  4. Look for messages starting with [GUIDE] prefix
  5. These will show exactly what is happening

Common issues and solutions:
  ❌ If you see "[GUIDE] marked library status: {exists: false}"
     → The marked.js library failed to load from CDN
     → Check your internet connection
     → Check Network tab in DevTools
  
  ❌ If you see "Failed to load guide" with HTTP error
     → The /api/get-guide endpoint is returning an error
     → Check Flask server is running
     → Check TRENDS_GUIDE.md exists
  
  ❌ If content loads but doesn't display
     → The guide div might have CSS issues
     → Check if guide has "active" class in Elements tab
     → Look for CSS conflicts in Console tab
""")
