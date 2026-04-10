"""
Hindsight memory service.
Wraps retain(), recall(), reflect() and set_bank_config().
Falls back to Gemini-only reasoning if Hindsight is unavailable.
"""
from config import hindsight, gemini_model
from typing import Optional


def _bank_id(child_id: str) -> str:
    return f"peds-child-{child_id}"


def setup_child_bank(child_id: str, child_name: str, conditions: list, allergies: list):
    """Called once when a child profile is created."""
    bank_id = _bank_id(child_id)
    allergy_str = ", ".join([f"{a['substance']} ({a['severity']})" for a in allergies]) or "none"
    condition_str = ", ".join(conditions) or "none"

    mission = (
        f"You are the dedicated health and parenting memory system for {child_name}. "
        f"Known conditions: {condition_str}. Known allergens: {allergy_str}. "
        f"Always surface allergy and condition context before any health or symptom reasoning."
    )
    directives = [
        "NEVER suggest wait-and-see for breathing symptoms if asthma is present.",
        "ALWAYS surface allergen context for food or symptom queries.",
        "NEVER use language implying a certain diagnosis. Use 'consistent with' or 'may indicate'.",
        "ALWAYS include escalation triggers (ER / Doctor) in symptom responses.",
    ]
    disposition = {
        "empathy": 0.8,
        "skepticism": 0.5,
        "literalism": 0.75,
    }

    if hindsight:
        try:
            hindsight.set_bank_config(
                bank_id=bank_id,
                mission=mission,
                directives=directives,
                disposition=disposition,
            )
            print(f"[Hindsight] Bank configured for child {child_id}")
        except Exception as e:
            print(f"[Hindsight] set_bank_config failed: {e}")


def retain_memory(child_id: str, content: str):
    """Store a fact/event/moment in the child's memory bank."""
    if hindsight:
        try:
            hindsight.retain(bank_id=_bank_id(child_id), content=content)
        except Exception as e:
            print(f"[Hindsight] retain failed: {e}")


def recall_memories(child_id: str, query: str) -> str:
    """Retrieve relevant memories for a query."""
    if hindsight:
        try:
            result = hindsight.recall(bank_id=_bank_id(child_id), query=query)
            return result.text if hasattr(result, "text") else str(result)
        except Exception as e:
            print(f"[Hindsight] recall failed: {e}")
    return ""


def reflect_on_query(child_id: str, query: str, context: Optional[str] = None) -> str:
    """
    Primary reasoning call: uses Hindsight reflect() which primes the
    child's mission/directives/disposition before answering.
    Falls back to raw Gemini if Hindsight unavailable.
    """
    if hindsight:
        try:
            result = hindsight.reflect(bank_id=_bank_id(child_id), query=query)
            return result.text if hasattr(result, "text") else str(result)
        except Exception as e:
            print(f"[Hindsight] reflect failed, falling back to Gemini: {e}")

    # Gemini fallback
    prompt = f"""You are a pediatric AI co-pilot. {context or ''}

Query: {query}

Provide a helpful, empathetic response. Always:
- Use hedged language ('consistent with', 'may indicate')
- Include when to see a doctor or go to the ER if health-related
- Add disclaimer: 'This is not a medical diagnosis.'"""
    response = gemini_model.generate_content(prompt)
    return response.text
