#!/usr/bin/env python3
"""
JWT Token Debug Script
Analyzes the tokens from the frontend request to identify SECRET_KEY issues
"""

import jwt
import json
from datetime import datetime

# Token from the request
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzYxZDk0MDktOGVkNS00ZWQzLWI1NjAtYjJlODQxNmQxMDAzIiwiZW1haWwiOiJhZG1pbkBuZW9hbGxvY2F0ZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3Njc0NTg4NDYsInR5cGUiOiJhY2Nlc3MifQ.4YeBsUlMAZBhfILyMAp4jOs9aTOJ_AHLJLiJ_vpdl_Q"

refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzYxZDk0MDktOGVkNS00ZWQzLWI1NjAtYjJlODQxNmQxMDAzIiwiZW1haWwiOiJhZG1pbkBuZW9hbGxvY2F0ZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjgwNjAwNDYsInR5cGUiOiJyZWZyZXNoIn0.7A3hjaiB97tXD1iPEldg5c_7DSkFuZFZX0FmepJeer8"

# Current SECRET_KEY in code
current_secret = "sk_prod_trainer_mgmt_2024_secure_key_32_chars_min"

print("🔍 JWT TOKEN ANALYSIS")
print("=" * 50)

# Decode without verification to see payload
try:
    access_payload = jwt.decode(access_token, options={"verify_signature": False})
    refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
    
    print("📋 ACCESS TOKEN PAYLOAD:")
    print(json.dumps(access_payload, indent=2))
    print()
    
    print("📋 REFRESH TOKEN PAYLOAD:")
    print(json.dumps(refresh_payload, indent=2))
    print()
    
    # Check expiration
    access_exp = datetime.fromtimestamp(access_payload['exp'])
    refresh_exp = datetime.fromtimestamp(refresh_payload['exp'])
    now = datetime.now()
    
    print(f"⏰ ACCESS TOKEN EXPIRES: {access_exp}")
    print(f"⏰ REFRESH TOKEN EXPIRES: {refresh_exp}")
    print(f"⏰ CURRENT TIME: {now}")
    print(f"✅ Access token valid: {access_exp > now}")
    print(f"✅ Refresh token valid: {refresh_exp > now}")
    print()
    
except Exception as e:
    print(f"❌ Error decoding payload: {e}")

# Try to verify with current secret
print("🔐 SIGNATURE VERIFICATION:")
print(f"Current SECRET_KEY: {current_secret}")

try:
    verified_access = jwt.decode(access_token, current_secret, algorithms=["HS256"])
    print("✅ ACCESS TOKEN: Signature valid with current secret")
except jwt.InvalidSignatureError:
    print("❌ ACCESS TOKEN: Invalid signature with current secret")
except jwt.ExpiredSignatureError:
    print("⏰ ACCESS TOKEN: Token expired")
except Exception as e:
    print(f"❌ ACCESS TOKEN: {e}")

try:
    verified_refresh = jwt.decode(refresh_token, current_secret, algorithms=["HS256"])
    print("✅ REFRESH TOKEN: Signature valid with current secret")
except jwt.InvalidSignatureError:
    print("❌ REFRESH TOKEN: Invalid signature with current secret")
except jwt.ExpiredSignatureError:
    print("⏰ REFRESH TOKEN: Token expired")
except Exception as e:
    print(f"❌ REFRESH TOKEN: {e}")

print()
print("🎯 DIAGNOSIS:")
print("If you see 'Invalid signature' errors above, it means:")
print("1. Tokens were created with a different SECRET_KEY")
print("2. Your production environment has a different SECRET_KEY")
print("3. You need to ensure SECRET_KEY consistency across environments")