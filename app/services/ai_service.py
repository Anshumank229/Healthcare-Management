import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("sk-7de816cb015d4008b4877f7a65c9ec58")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")       # optional fallback
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")       # optional fallback

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


def get_ai_reply(user_message: str, patient_context: str = "") -> tuple[str, str]:
    """
    Returns (reply_text, model_used)
    Tries DeepSeek first, then Gemini, then OpenAI, then fallback message.
    """
    full_system_prompt = CLINIC_SYSTEM_PROMPT
    if patient_context:
        full_system_prompt += f"\n\nPatient Context:\n{patient_context}"

    # Primary: DeepSeek
    if DEEPSEEK_API_KEY:
        try:
            return _deepseek_reply(full_system_prompt, user_message)
        except Exception as e:
            logger.warning(f"DeepSeek failed: {e}. Trying next...")

    # Fallback 1: Gemini
    if GEMINI_API_KEY:
        try:
            return _gemini_reply(full_system_prompt, user_message)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}. Trying next...")

    # Fallback 2: OpenAI
    if OPENAI_API_KEY:
        try:
            return _openai_reply(full_system_prompt, user_message)
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")

    # Final fallback
    return (
        "I'm sorry, I'm unable to process your request right now. "
        "Please contact the clinic directly for assistance.",
        "fallback"
    )


def _deepseek_reply(system_prompt: str, user_message: str) -> tuple[str, str]:
    """DeepSeek uses OpenAI-compatible API — just different base_url and model."""
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip(), "deepseek-chat"


def _gemini_reply(system_prompt: str, user_message: str) -> tuple[str, str]:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"{system_prompt}\n\nPatient asks: {user_message}"
    )
    return response.text.strip(), "gemini-1.5-flash"


def _openai_reply(system_prompt: str, user_message: str) -> tuple[str, str]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip(), "gpt-3.5-turbo"