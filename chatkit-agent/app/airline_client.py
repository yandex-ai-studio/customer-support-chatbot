import logging
import os

import httpx
from agents.mcp import MCPServerSse, MCPServer

AIRLINE_API_URL = os.environ.get("AIRLINE_API_URL")
API_KEY = os.environ.get("API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_customer_profile(profile_id: str) -> dict:
    """Fetch customer profile from airline-api service."""
    async with httpx.AsyncClient(base_url=AIRLINE_API_URL, timeout=10.0,
                                 headers={"Authorization": f"Api-Key {API_KEY}"}) as client:
        response = await client.get(f"/profile/{profile_id}")
        response.raise_for_status()
        result = response.json()
        return result["profile"]


def format_customer_context(profile: dict) -> str:
    """Format customer profile data for agent context."""
    segments = []
    for segment in profile.get("segments", []):
        segments.append(
            f"- {segment['flight_number']} {segment['origin']}->{segment['destination']}"
            f" on {segment['date']} seat {segment['seat']} ({segment['status']})"
        )
    summary = "\n".join(segments)
    timeline = profile.get("timeline", [])[:3]
    recent = "\n".join(f"  * {entry['entry']} ({entry['timestamp']})" for entry in timeline)
    return (
        "Customer Profile\n"
        f"ID: {profile['customer_id']}\n"
        f"Name: {profile['name']} ({profile['loyalty_status']})\n"
        f"Loyalty ID: {profile['loyalty_id']}\n"
        f"Contact: {profile['email']}, {profile['phone']}\n"
        f"Checked Bags: {profile['bags_checked']}\n"
        f"Meal Preference: {profile.get('meal_preference') or 'Not set'}\n"
        f"Special Assistance: {profile.get('special_assistance') or 'None'}\n"
        "Upcoming Segments:\n"
        f"{summary}\n"
        "Recent Service Timeline:\n"
        f"{recent or '  * No service actions recorded yet.'}"
    )


async def get_customer_profile(profile_id):
    try:
        profile = await fetch_customer_profile(profile_id)
        context_prompt = format_customer_context(profile)
    except Exception as e:
        logger.info(f"Warning: Could not fetch customer profile: {e}")
        context_prompt = "Customer profile unavailable."
    return context_prompt
