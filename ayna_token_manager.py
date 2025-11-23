#!/usr/bin/env python3
"""
AynaOTT token auto-login + auto-refresh manager.

Requirements:
    pip install requests

How it works:
 - Uses your provided login payload to POST /api/authorization/login
 - Saves token info to token.json with absolute expiry timestamp
 - Tries to refresh using /api/authorization/refresh with refresh_token
 - If refresh fails, falls back to login()
 - Use get_auth_headers() to attach Authorization header for other requests
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta

BASE = "https://web.aynaott.com"
LOGIN_URL = f"{BASE}/api/authorization/login"
REFRESH_URL = f"{BASE}/api/authorization/refresh"
TOKEN_FILE = "token.json"

# ---- PUT the login payload you provided ----
LOGIN_PAYLOAD = {
    "client": "browser",
    "density": 3.0000001192092896,
    "device_id": "582CC788D250CFADCA1B694D868288A7",
    "language": "en",
    "login": "monirulislamshakib007@gmail.com",
    "operator_id": "1fb1b4c7-dbd9-469e-88a2-c207dc195869",
    "os": "ios",
    "password": "@Monirul2010",
    "platform": "mobile"
}
# -------------------------------------------

# Timeout for requests
REQUEST_TIMEOUT = 15

def save_token_file(data: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)  # restrict file permissions (unix)

def load_token_file():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def login():
    """Perform login and save tokens."""
    print("[*] Performing login...")
    try:
        resp = requests.post(LOGIN_URL, json=LOGIN_PAYLOAD, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print("[!] Login request error:", e)
        return None

    if resp.status_code != 200:
        print("[!] Login failed, status:", resp.status_code, resp.text[:200])
        return None

    j = resp.json()
    # defensive access based on your response example
    try:
        token_obj = j["content"]["token"]
        access = token_obj.get("access_token")
        refresh = token_obj.get("refresh_token")
        expires_in = token_obj.get("expires_in", 0)  # seconds
    except Exception as e:
        print("[!] Unexpected login response format:", e)
        print("Response JSON:", j)
        return None

    expires_at = int(time.time()) + int(expires_in)
    token_data = {
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": expires_in,
        "expires_at": expires_at,
        "saved_at": int(time.time())
    }
    save_token_file(token_data)
    print("[+] Login successful. Token saved. Expires in:", expires_in, "seconds")
    return token_data

def try_refresh(refresh_token: str):
    """
    Try refresh endpoint. Many APIs expect {"refresh_token": "..."}.
    If your API expects headers, we can try that too as fallback.
    """
    print("[*] Trying refresh...")
    # attempt 1: JSON body
    try:
        resp = requests.post(REFRESH_URL, json={"refresh_token": refresh_token}, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print("[!] Refresh request error (json body):", e)
        resp = None

    if resp and resp.status_code == 200:
        try:
            j = resp.json()
            token_obj = j["content"]["token"]
            access = token_obj.get("access_token")
            refresh_new = token_obj.get("refresh_token")
            expires_in = token_obj.get("expires_in", 0)
            expires_at = int(time.time()) + int(expires_in)
            token_data = {
                "access_token": access,
                "refresh_token": refresh_new or refresh_token,
                "expires_in": expires_in,
                "expires_at": expires_at,
                "saved_at": int(time.time())
            }
            save_token_file(token_data)
            print("[+] Refresh successful. New token saved. Expires in:", expires_in)
            return token_data
        except Exception as e:
            print("[!] Unexpected refresh response format:", e)
            print("Response JSON:", resp.text[:300])

    # attempt 2: Authorization header with refresh token (less common)
    try:
        headers = {"Authorization": f"Bearer {refresh_token}", "Content-Type": "application/json"}
        resp2 = requests.post(REFRESH_URL, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp2.status_code == 200:
            j = resp2.json()
            token_obj = j["content"]["token"]
            access = token_obj.get("access_token")
            refresh_new = token_obj.get("refresh_token")
            expires_in = token_obj.get("expires_in", 0)
            expires_at = int(time.time()) + int(expires_in)
            token_data = {
                "access_token": access,
                "refresh_token": refresh_new or refresh_token,
                "expires_in": expires_in,
                "expires_at": expires_at,
                "saved_at": int(time.time())
            }
            save_token_file(token_data)
            print("[+] Refresh (auth header) successful.")
            return token_data
    except Exception as e:
        print("[!] Refresh attempt 2 error:", e)

    print("[!] Refresh failed (both attempts).")
    return None

def get_token(force_refresh=False):
    """
    Return valid token_data (loads from file or logs-in / refreshes as needed).
    If force_refresh True -> try to refresh immediately.
    """
    data = load_token_file()
    now = int(time.time())

    if data is None:
        return login()

    # check expiry
    expires_at = data.get("expires_at", 0)
    # refresh margin: if token expires within next 300 seconds, refresh it
    REFRESH_MARGIN = 300
    if force_refresh or (expires_at - now) <= REFRESH_MARGIN:
        refreshed = try_refresh(data.get("refresh_token"))
        if refreshed:
            return refreshed
        # refresh failed -> fallback to login
        return login()

    # still valid
    return data

def get_auth_headers():
    token_data = get_token()
    if not token_data:
        raise RuntimeError("No token available")
    return {"Authorization": f"Bearer {token_data['access_token']}", "Content-Type": "application/json"}

# Example usage: periodically ensure token validity
def run_daemon(check_interval_seconds=600):
    """
    Run a simple loop that ensures token remains fresh.
    This does not daemonize; run it under Supervisor/systemd or GitHub Actions cron.
    """
    print("[*] Starting token manager daemon. Ctrl+C to stop.")
    try:
        while True:
            td = get_token()
            if td:
                exp = datetime.fromtimestamp(td["expires_at"]).isoformat()
                print(f"[i] Token valid until {exp}")
            else:
                print("[!] No token obtained.")
            time.sleep(check_interval_seconds)
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")

if __name__ == "__main__":
    # quick test: ensure token file exists and token valid
    token_data = get_token()
    if token_data:
        print("[OK] Access token:", token_data["access_token"][:40], "...")
        print("[OK] Refresh token:", token_data["refresh_token"][:40], "...")
    else:
        print("[FAIL] Could not obtain token. Check credentials or network.")
