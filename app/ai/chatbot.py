from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.ai_service import get_ai_reply
from app.models.patient import Patient
from app.models.prescription import Prescription
import json

router = APIRouter(prefix="/ai", tags=["AI Chatbot"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
def chat_with_bot(
        body: ChatMessage,
        db: Session = Depends(get_db)
):
    """
    Public chatbot endpoint.
    Patients can ask about clinic timings, fees, medicines, follow-ups.
    If patient_id is provided, AI gets patient context (name, disease, medicines).
    """
    patient_context = ""

    if body.patient_id:
        patient = db.query(Patient).filter(Patient.id == body.patient_id).first()
        if patient:
            context_parts = [
                f"Patient Name: {patient.full_name}",
                f"Phone: {patient.phone}",
            ]
            if hasattr(patient, "disease") and patient.disease:
                context_parts.append(f"Disease/Problem: {patient.disease}")
            if hasattr(patient, "medical_history") and patient.medical_history:
                context_parts.append(f"Medical History: {patient.medical_history}")

            # Get latest prescription
            latest_prescription = db.query(Prescription).filter(
                Prescription.patient_id == body.patient_id
            ).order_by(Prescription.created_at.desc()).first()

            if latest_prescription:
                try:
                    medicines = json.loads(latest_prescription.medicines)
                    med_list = ", ".join(
                        [f"{m['name']} ({m['dose']}, {m['frequency']})" for m in medicines]
                    )
                    context_parts.append(f"Current Medicines: {med_list}")
                    if latest_prescription.next_visit_date:
                        context_parts.append(
                            f"Next Visit Date: {latest_prescription.next_visit_date}"
                        )
                except Exception:
                    pass

            patient_context = "\n".join(context_parts)

    reply, model_used = get_ai_reply(body.message, patient_context)
    return ChatResponse(reply=reply, model_used=model_used)


@router.post("/summarize-notes")
def summarize_doctor_notes(
        body: dict,
        db: Session = Depends(get_db)
):
    """
    Doctor enters raw notes → AI returns a clean structured summary.
    Body: { "notes": "patient came with fever 102..." }
    """
    raw_notes = body.get("notes", "").strip()
    if not raw_notes:
        raise HTTPException(status_code=400, detail="Notes cannot be empty")

    prompt = f"""
You are a medical assistant. A doctor has written the following raw consultation notes.
Please convert them into a clean, structured summary with these sections:
- Chief Complaint
- Symptoms
- Diagnosis (if mentioned)
- Medicines Prescribed (if mentioned)
- Advice Given
- Follow-up

Doctor's notes:
{raw_notes}
"""
    reply, model_used = get_ai_reply(prompt)
    return {"summary": reply, "model_used": model_used}


@router.post("/lead-score")
def score_lead(
        body: dict,
        db: Session = Depends(get_db)
):
    """
    AI predicts if a lead is likely to convert.
    Body: { "name": "...", "problem": "...", "source": "...", "days_since_inquiry": 3 }
    """
    lead_info = body

    prompt = f"""
You are a healthcare CRM analyst. Analyze this patient lead and predict conversion probability.

Lead Details:
- Name: {lead_info.get('name', 'Unknown')}
- Problem: {lead_info.get('problem', 'Not specified')}
- Source: {lead_info.get('source', 'Unknown')}
- Days Since Inquiry: {lead_info.get('days_since_inquiry', 0)}
- Notes: {lead_info.get('notes', 'None')}

Respond in this exact JSON format:
{{
  "conversion_probability": <number 0-100>,
  "risk_level": "<low|medium|high>",
  "recommended_action": "<what staff should do next>",
  "reasoning": "<brief explanation>"
}}
"""
    reply, model_used = get_ai_reply(prompt)

    # Try to parse JSON from AI response
    try:
        import re
        json_match = re.search(r'\{.*\}', reply, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result["model_used"] = model_used
            return result
    except Exception:
        pass

    return {"raw_response": reply, "model_used": model_used}