"""
api_client.py
─────────────
Handles all HTTP communication with the Django REST API.
All functions return Python dicts or None on failure.
"""

import requests

# ── Base URL of your Django backend ──────────────────────
BASE_URL = "http://127.0.0.1:8000/api"

HEADERS = {"Content-Type": "application/json"}


# ─────────────────────────────────────────────────────────
#  COMPLAINTS
# ─────────────────────────────────────────────────────────

def create_complaint(title: str, description: str, department_id: int, created_by: str) -> dict | None:
    """
    POST /api/complaints/create/
    Registers a new complaint and returns the response dict.
    """
    payload = {
        "title"      : title,
        "description": description,
        "department" : department_id,
        "created_by" : created_by,
    }
    try:
        res = requests.post(f"{BASE_URL}/complaints/create/", json=payload, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] create_complaint: {e}")
        return None


def get_complaint(complaint_id: int) -> dict | None:
    """
    GET /api/complaints/<id>/
    Fetches a single complaint by ID.
    """
    try:
        res = requests.get(f"{BASE_URL}/complaints/{complaint_id}/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] get_complaint: {e}")
        return None


def get_open_complaints() -> list:
    """
    GET /api/complaints/?status=Open
    Returns a list of all open complaints.
    """
    try:
        res = requests.get(f"{BASE_URL}/complaints/", params={"status": "Open"}, timeout=10)
        res.raise_for_status()
        data = res.json()
        # DRF pagination returns results inside 'results' key
        return data.get("results", data) if isinstance(data, dict) else data
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] get_open_complaints: {e}")
        return []


def get_complaint_track(complaint_id: int) -> dict | None:
    """
    GET /api/complaints/<id>/track/
    Returns timeline tracking info for a complaint.
    """
    try:
        res = requests.get(f"{BASE_URL}/complaints/{complaint_id}/track/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] get_complaint_track: {e}")
        return None


def get_departments() -> list:
    """
    GET /api/departments/
    Returns all departments — used to map names to IDs.
    """
    try:
        res = requests.get(f"{BASE_URL}/departments/", timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("results", data) if isinstance(data, dict) else data
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] get_departments: {e}")
        return []


def get_stats() -> dict | None:
    """
    GET /api/stats/
    Returns dashboard statistics.
    """
    try:
        res = requests.get(f"{BASE_URL}/stats/", timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"[API ERROR] get_stats: {e}")
        return None