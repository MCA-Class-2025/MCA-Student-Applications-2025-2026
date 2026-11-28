"""
NutriMate Reusable API Client
=============================
Provides a robust, failure-safe client interface for Streamlit to communicate
with all 6 NutriMate FastAPI backend services.

Guarantees:
- API timeouts (default 30s)
- Comprehensive try-except error catching (never crashes caller)
- Normalized response structures
"""

import requests
import json
import urllib.parse
from typing import Optional, List, Dict, Any

API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 30  # seconds


class NutriMateAPIClient:
    """Central API client wrapping all 7 NutriMate FastAPI backend services."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_health(self) -> bool:
        """Check if FastAPI server is reachable."""
        try:
            r = requests.get(f"{self.base_url}/docs", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ── 1. NUTRITION ANALYSIS API ──────────────────────────────────────
    def analyze_nutrition(
        self,
        food_name: str,
        recipe_text: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
        serving_size: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """POST /api/nutrition/analyze"""
        url = f"{self.base_url}/api/nutrition/analyze"
        payload = {
            "food_name": food_name,
            "recipe_text": recipe_text,
            "ingredients": ingredients or [],
            "serving_size": serving_size
        }
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"[APIClient] analyze_nutrition HTTP {r.status_code}: {r.text}")
        except Exception as exc:
            print(f"[APIClient] analyze_nutrition exception: {exc}")
        return None

    # ── 2. NUTRITION DATABASE API ──────────────────────────────────────
    def get_foods(
        self,
        diet_type: Optional[str] = None,
        meal_type: Optional[str] = None,
        goal: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """GET /api/foods"""
        url = f"{self.base_url}/api/foods"
        params = {}
        if diet_type:
            params["diet_type"] = diet_type
        if meal_type:
            params["meal_type"] = meal_type
        if goal:
            params["goal"] = goal
        if search:
            params["search"] = search
        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_foods exception: {exc}")
        return []

    def get_food_by_name(self, food_name: str) -> Optional[Dict[str, Any]]:
        """GET /api/foods/{food_name}"""
        encoded_name = urllib.parse.quote(food_name)
        url = f"{self.base_url}/api/foods/{encoded_name}"
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_food_by_name exception: {exc}")
        return None

    def save_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/foods"""
        url = f"{self.base_url}/api/foods"
        try:
            r = requests.post(url, json=food_data, timeout=self.timeout)
            if r.status_code in (201, 200):
                return {"success": True, "data": r.json()}
            elif r.status_code == 409:
                return {"success": False, "error": "duplicate", "detail": r.json().get("detail", "Food item already exists.")}
            else:
                return {"success": False, "error": "http_error", "detail": r.json().get("detail", r.text)}
        except Exception as exc:
            print(f"[APIClient] save_food exception: {exc}")
            return {"success": False, "error": "exception", "detail": str(exc)}

    # ── 3. FOOD RECOGNITION API ────────────────────────────────────────
    def recognize_food(self, image_bytes: bytes, filename: str = "food.jpg") -> Optional[Dict[str, Any]]:
        """POST /api/foods/recognize"""
        url = f"{self.base_url}/api/foods/recognize"
        files = {"file": (filename, image_bytes, "image/jpeg")}
        try:
            r = requests.post(url, files=files, timeout=60)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"[APIClient] recognize_food HTTP {r.status_code}: {r.text}")
        except Exception as exc:
            print(f"[APIClient] recognize_food exception: {exc}")
        return None

    # ── 4. ALLERGEN DETECTION API ──────────────────────────────────────
    def detect_allergens(
        self,
        food_name: str,
        ingredients: Optional[List[str]] = None,
        recipe_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """POST /api/foods/allergens"""
        url = f"{self.base_url}/api/foods/allergens"
        payload = {
            "food_name": food_name,
            "ingredients": ingredients or [],
            "recipe_text": recipe_text
        }
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] detect_allergens exception: {exc}")
        return None

    # ── 5. HEALTHY SUBSTITUTION API ────────────────────────────────────
    def get_substitutions(
        self,
        food_name: str,
        ingredients: Optional[List[str]] = None,
        recipe_text: Optional[str] = None,
        goal: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """POST /api/foods/substitutions"""
        url = f"{self.base_url}/api/foods/substitutions"
        payload = {
            "food_name": food_name,
            "ingredients": ingredients or [],
            "recipe_text": recipe_text,
            "goal": goal
        }
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_substitutions exception: {exc}")
        return None

    # ── 6. FOOD COMPARISON API ─────────────────────────────────────────
    def compare_foods(
        self,
        food_1: str,
        food_2: str,
        goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """POST /api/foods/compare"""
        url = f"{self.base_url}/api/foods/compare"
        payload = {
            "food_1": food_1,
            "food_2": food_2,
            "goal": goal or "maintenance"
        }
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            elif r.status_code == 404:
                return {"success": False, "error": "not_found", "detail": r.json().get("detail", "Food item not found")}
            else:
                return {"success": False, "error": "http_error", "detail": r.json().get("detail", r.text)}
        except Exception as exc:
            print(f"[APIClient] compare_foods exception: {exc}")
            return {"success": False, "error": "exception", "detail": str(exc)}

    # ── 7. CHEAT MEAL IMPACT API ───────────────────────────────────────
    def cheat_meal_impact(
        self,
        food_name: str,
        calories: Optional[float] = None,
        sugar_g: Optional[float] = None,
        fat_g: Optional[float] = None,
        daily_calorie_target: float = 2000.0,
        daily_sugar_target: float = 50.0,
        daily_fat_target: float = 65.0,
        goal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/foods/cheat-meal-impact"""
        url = f"{self.base_url}/api/foods/cheat-meal-impact"
        payload: Dict[str, Any] = {
            "food_name": food_name,
            "daily_calorie_target": daily_calorie_target,
            "daily_sugar_target": daily_sugar_target,
            "daily_fat_target": daily_fat_target,
        }
        if calories is not None:
            payload["calories"] = calories
        if sugar_g is not None:
            payload["sugar_g"] = sugar_g
        if fat_g is not None:
            payload["fat_g"] = fat_g
        if goal:
            payload["goal"] = goal
        try:
            r = requests.post(url, json=payload, timeout=120)  # LLM estimation may take time
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            elif r.status_code == 422:
                return {"success": False, "error": "validation", "detail": r.json().get("detail", r.text)}
            else:
                return {"success": False, "error": "http_error", "detail": r.json().get("detail", r.text)}
        except Exception as exc:
            print(f"[APIClient] cheat_meal_impact exception: {exc}")
            return {"success": False, "error": "exception", "detail": str(exc)}

    # ── 8. PROGRESS TRACKING API ───────────────────────────────────────
    def log_progress(self, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/progress/log"""
        url = f"{self.base_url}/api/progress/log"
        try:
            r = requests.post(url, json=progress_data, timeout=self.timeout)
            if r.status_code == 201:
                return {"success": True, "data": r.json()}
            elif r.status_code == 409:
                return {"success": False, "error": "duplicate", "detail": r.json().get("detail", "Log already exists for this date.")}
            else:
                return {"success": False, "error": "http_error", "detail": r.json().get("detail", r.text)}
        except Exception as exc:
            print(f"[APIClient] log_progress exception: {exc}")
            return {"success": False, "error": "exception", "detail": str(exc)}

    def get_progress(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        goal: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """GET /api/progress"""
        url = f"{self.base_url}/api/progress"
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if goal:
            params["goal"] = goal
        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_progress exception: {exc}")
        return []

    def get_progress_summary(self) -> Optional[Dict[str, Any]]:
        """GET /api/progress/summary"""
        url = f"{self.base_url}/api/progress/summary"
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_progress_summary exception: {exc}")
        return None

    # ── 9. HYDRATION TRACKING API ───────────────────────────────────────
    def log_hydration(self, hydration_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST /api/hydration/log"""
        url = f"{self.base_url}/api/hydration/log"
        try:
            r = requests.post(url, json=hydration_data, timeout=self.timeout)
            if r.status_code == 201:
                return {"success": True, "data": r.json()}
            else:
                return {"success": False, "error": "http_error", "detail": r.json().get("detail", r.text)}
        except Exception as exc:
            print(f"[APIClient] log_hydration exception: {exc}")
            return {"success": False, "error": "exception", "detail": str(exc)}

    def get_hydration_today(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """GET /api/hydration/today"""
        url = f"{self.base_url}/api/hydration/today"
        params = {}
        if date:
            params["date"] = date
        try:
            r = requests.get(url, params=params, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_hydration_today exception: {exc}")
        return None

    def get_hydration_summary(self) -> Optional[Dict[str, Any]]:
        """GET /api/hydration/summary"""
        url = f"{self.base_url}/api/hydration/summary"
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            print(f"[APIClient] get_hydration_summary exception: {exc}")
        return None


