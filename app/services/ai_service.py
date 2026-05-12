import os
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-5-20250929"

if not ANTHROPIC_API_KEY:
    logger.critical(
        "ANTHROPIC_API_KEY is not set. "
        "Add it to your .env file and Render environment variables."
    )

# Clinic context — customize this for your clinic
CLINIC_SYSTEM_PROMPT = """
You are a helpful AI assistant for a healthcare clinic.

Clinic Information:
- Name: HealthCare Clinic
- Timings: Monday to Saturday, 9 AM to 7 PM
- Sunday: Closed
- General Consultation Fee: ₹500
- Specialist Consultation Fee: ₹1000
- Services: General medicine, dental, orthopedics, gynecology, pediatrics

Your job:
- Answer patient questions about clinic timings, fees, services, doctors
- Help patients understand their medicines or prescriptions (general info only)
- Remind patients to book follow-up visits
- For medical emergencies, always say: "Please call emergency services or visit the nearest hospital immediately."
- Never diagnose diseases or prescribe medicines
- Be polite, warm, and concise
- Respond in the same language the patient uses (Hindi or English)
"""

# Build client once — avoids recreating on every request
_client: anthropic.Anthropic | None = (
    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
)

FALLBACK_MESSAGE = (
    "I'm sorry, I'm unable to process your request right now. "
    "Please contact the clinic directly for assistance."
)


def get_ai_reply(user_message: str, patient_context: str = "") -> tuple[str, str]:
    """
    Returns (reply_text, model_used).
    Falls back to a static message if the API call fails.
    """
    if not _client:
        logger.error("Claude client not initialised — ANTHROPIC_API_KEY missing.")
        return FALLBACK_MESSAGE, "fallback"

    full_system_prompt = CLINIC_SYSTEM_PROMPT
    if patient_context:
        full_system_prompt += f"\n\nPatient Context:\n{patient_context}"

    try:
        return _claude_reply(full_system_prompt, user_message)
    except anthropic.AuthenticationError:
        logger.error("Claude API: invalid or expired API key.")
    except anthropic.RateLimitError:
        logger.warning("Claude API: rate limit hit.")
    except anthropic.APIConnectionError as e:
        logger.error(f"Claude API: connection error — {e}")
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API: status {e.status_code} — {e.message}")
    except Exception as e:
        logger.error(f"Claude API: unexpected error — {e}")

    return FALLBACK_MESSAGE, "fallback"


def _claude_reply(system_prompt: str, user_message: str) -> tuple[str, str]:
    response = _client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )
    return response.content[0].text.strip(), MODEL