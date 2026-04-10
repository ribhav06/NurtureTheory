"""
Symptom triage logic using Hindsight reflect() + Gemini for structured output.
Hard-coded escalation triggers per PRD Section 6 & Appendix B.
"""
from config import gemini_model
from memory import reflect_on_query, retain_memory
import json
import re


# ── Hard-coded escalation triggers (PRD Appendix B) ────────────────────────

ER_TRIGGERS = [
    "Breathing difficulty or severe respiratory distress",
    "Cyanosis (blue lips or fingernails)",
    "Altered consciousness or unresponsive",
    "Febrile seizure",
    "Suspected anaphylaxis (child has known anaphylactic allergy)",
]

DOCTOR_TODAY_TRIGGERS = [
    "Fever in child under 3 months",
    "Fever above 39.5°C lasting more than 48 hours",
    "Rash with fever",
    "Ear pain with fever",
    "Symptoms not improving after 48 hours of home care",
]


def get_asthma_override(conditions: list) -> str:
    if any("asthma" in c.lower() for c in conditions):
        return "⚠️ Asthma override: Any wheeze or respiratory distress defaults to 'Go to doctor today' minimum. No home-care-only option."
    return ""


def calculate_dosing(weight_kg: float) -> list:
    if not weight_kg:
        return []
    para_dose = round(weight_kg * 15)
    ibu_dose = round(weight_kg * 10)
    return [
        {"med": "Paracetamol", "dose": f"{para_dose}mg ({weight_kg}kg × 15mg/kg) every 6 hours as needed"},
        {"med": "Ibuprofen", "dose": f"{ibu_dose}mg ({weight_kg}kg × 10mg/kg) every 8 hours with food"},
    ]


async def triage_symptom(
    child_id: str,
    child_name: str,
    symptom_text: str,
    child_context: dict,
) -> dict:
    """
    Main triage function.
    1. Builds child-aware prompt
    2. Calls Hindsight reflect() (which primes bank mission + directives)
    3. Structured output via Gemini
    4. Appends hard-coded escalation triggers
    5. Retains episode to Hindsight memory bank
    """
    conditions = child_context.get("conditions", [])
    allergies = child_context.get("allergies", [])
    weight = child_context.get("weight_kg")
    age_label = child_context.get("age_label", "")

    allergy_str = ", ".join([f"{a['substance']} ({a['severity']})" for a in allergies]) if allergies else "none"
    condition_str = ", ".join(conditions) if conditions else "none"
    asthma_note = get_asthma_override(conditions)

    # Hindsight reflect() — primed with child mission, directives, disposition
    hindsight_context = reflect_on_query(
        child_id=child_id,
        query=f"Symptom query for {child_name}: {symptom_text}",
        context=f"Child: {child_name}, Age: {age_label}, Conditions: {condition_str}, Allergies: {allergy_str}"
    )

    # Structured output from Gemini
    prompt = f"""You are a pediatric triage AI. Provide a structured triage response.

Child: {child_name} ({age_label})
Conditions: {condition_str}
Known Allergies: {allergy_str}
{asthma_note}

Symptom: {symptom_text}

Hindsight memory context:
{hindsight_context}

Respond in valid JSON with this exact structure:
{{
  "narrative": "2-3 sentence empathetic summary using hedged language like 'consistent with' or 'may indicate'",
  "home_care": ["step 1", "step 2", "step 3"],
  "past_episode_note": "mention if similar episode occurred before (or empty string)"
}}

IMPORTANT: Never say 'definitely' or 'you have'. Always use 'consistent with', 'may indicate', 'most likely'.
Do NOT include escalation triggers — those are added separately."""

    response = gemini_model.generate_content(prompt)
    
    # Parse JSON from response
    try:
        raw = response.text.strip()
        # Extract JSON block if wrapped in markdown
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = {"narrative": raw, "home_care": [], "past_episode_note": ""}
    except Exception:
        data = {
            "narrative": response.text,
            "home_care": ["Keep child comfortable", "Ensure adequate hydration", "Monitor symptoms closely"],
            "past_episode_note": ""
        }

    # Auto-retain this episode to Hindsight
    retain_memory(
        child_id=child_id,
        content=f"Symptom episode: {symptom_text}. Assessment: {data.get('narrative', '')}. Date: today."
    )

    # Build final response with hard-coded safety always appended
    return {
        "narrative": data.get("narrative", ""),
        "home_care": data.get("home_care", []),
        "past_episode_note": data.get("past_episode_note", ""),
        "escalation_er": ER_TRIGGERS,
        "escalation_doctor": DOCTOR_TODAY_TRIGGERS + (
            ["Any wheeze or respiratory distress (asthma override: go to doctor minimum)"] if asthma_note else []
        ),
        "dosing": calculate_dosing(weight) if weight else [],
        "disclaimer": "This is not a medical diagnosis. Call your pediatrician when in doubt.",
    }
