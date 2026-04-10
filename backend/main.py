"""
Pēds — FastAPI Backend
Pediatric Co-Pilot API powering Health Vault, Symptom Guide,
Development Tracker, and Parenting Coach.
"""
import os
from datetime import date
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from config import supabase
from models import (
    ChildCreate, ChildUpdate,
    VaccineCreate, AllergyCreate, MedicationCreate, GrowthCreate,
    SymptomQuery,
    MilestoneCreate,
    ParentingMomentCreate, CoachQuery,
)
from memory import setup_child_bank, retain_memory, recall_memories, reflect_on_query
from triage import triage_symptom
from pdf_export import generate_visit_pdf

load_dotenv()

app = FastAPI(
    title="Pēds API",
    description="Pediatric Co-Pilot — Health Vault, Symptom Guide, Dev Tracker, Parenting Coach",
    version="1.0.0",
)

# CORS — allow frontend dev server
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8081").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {"status": "ok", "service": "Pēds API", "version": "1.0.0"}


# ═══════════════════════════════════════════════════════════════════════════════
# CHILDREN
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/children", status_code=201)
def create_child(payload: ChildCreate):
    """Create a child profile and initialize their Hindsight memory bank."""
    data = payload.dict()
    allergies = data.pop("allergies", [])

    result = supabase.table("children").insert({
        **data,
        "created_at": date.today().isoformat(),
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create child profile")

    child = result.data[0]
    child_id = child["id"]

    # Store allergies
    if allergies:
        allergy_records = [{"child_id": child_id, **a} for a in allergies]
        supabase.table("allergies").insert(allergy_records).execute()

    # Initialize Hindsight memory bank for this child
    setup_child_bank(
        child_id=child_id,
        child_name=payload.name,
        conditions=payload.conditions or [],
        allergies=allergies,
    )

    return {"child": child, "hindsight_bank": f"peds-child-{child_id}"}


@app.get("/children")
def list_children():
    result = supabase.table("children").select("*").execute()
    return result.data


@app.get("/children/{child_id}")
def get_child(child_id: str):
    result = supabase.table("children").select("*").eq("id", child_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Child not found")
    return result.data


@app.patch("/children/{child_id}")
def update_child(child_id: str, payload: ChildUpdate):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    result = supabase.table("children").update(updates).eq("id", child_id).execute()
    return result.data


@app.delete("/children/{child_id}", status_code=204)
def delete_child(child_id: str):
    supabase.table("children").delete().eq("id", child_id).execute()
    # Note: Hindsight bank deletion handled separately when Hindsight Cloud API supports it


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH VAULT — Vaccines
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/vaccines", status_code=201)
def add_vaccine(payload: VaccineCreate):
    result = supabase.table("vaccines").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to add vaccine")
    # Retain in Hindsight
    retain_memory(
        payload.child_id,
        f"Vaccine administered: {payload.name} on {payload.date_given or 'unknown date'}."
    )
    return result.data[0]


@app.get("/children/{child_id}/vaccines")
def get_vaccines(child_id: str):
    result = supabase.table("vaccines").select("*").eq("child_id", child_id).execute()
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH VAULT — Allergies
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/allergies", status_code=201)
def add_allergy(payload: AllergyCreate):
    result = supabase.table("allergies").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to add allergy")
    retain_memory(
        payload.child_id,
        f"Known allergy: {payload.substance} — severity: {payload.severity}. EpiPen: {'yes' if payload.epipen else 'no'}."
    )
    return result.data[0]


@app.get("/children/{child_id}/allergies")
def get_allergies(child_id: str):
    result = supabase.table("allergies").select("*").eq("child_id", child_id).execute()
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH VAULT — Medications
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/medications", status_code=201)
def add_medication(payload: MedicationCreate):
    result = supabase.table("medications").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to add medication")
    retain_memory(
        payload.child_id,
        f"Medication: {payload.name} {payload.dose}, {payload.frequency}. Last given: {payload.last_given or 'unknown'}."
    )
    return result.data[0]


@app.get("/children/{child_id}/medications")
def get_medications(child_id: str):
    result = supabase.table("medications").select("*").eq("child_id", child_id).execute()
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH VAULT — Growth
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/growth", status_code=201)
def log_growth(payload: GrowthCreate):
    result = supabase.table("growth_records").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log growth")
    retain_memory(
        payload.child_id,
        f"Growth measurement on {payload.date}: weight={payload.weight_kg}kg, height={payload.height_cm}cm."
    )
    return result.data[0]


@app.get("/children/{child_id}/growth")
def get_growth(child_id: str):
    result = supabase.table("growth_records").select("*").eq("child_id", child_id).order("date").execute()
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# SYMPTOM GUIDE
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/symptom/triage")
async def symptom_triage(payload: SymptomQuery):
    """
    Core triage endpoint.
    Fetches child context → calls Hindsight reflect() → returns structured triage.
    """
    # Fetch child
    child_result = supabase.table("children").select("*").eq("id", payload.child_id).single().execute()
    if not child_result.data:
        raise HTTPException(status_code=404, detail="Child not found")
    child = child_result.data

    # Fetch allergies
    allergies_result = supabase.table("allergies").select("*").eq("child_id", payload.child_id).execute()
    allergies = allergies_result.data or []

    child_context = {
        "conditions": child.get("conditions") or [],
        "allergies": allergies,
        "weight_kg": child.get("weight_kg"),
        "age_label": child.get("age_label", ""),
    }

    response = await triage_symptom(
        child_id=payload.child_id,
        child_name=child["name"],
        symptom_text=payload.symptom_text,
        child_context=child_context,
    )

    # Store symptom log in Supabase
    supabase.table("symptom_logs").insert({
        "child_id": payload.child_id,
        "symptom_text": payload.symptom_text,
        "response_narrative": response["narrative"],
        "date": date.today().isoformat(),
    }).execute()

    return response


@app.get("/children/{child_id}/symptoms")
def get_symptom_history(child_id: str):
    result = supabase.table("symptom_logs").select("*").eq("child_id", child_id).order("date", desc=True).execute()
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# DEVELOPMENT TRACKER
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/milestones", status_code=201)
def log_milestone(payload: MilestoneCreate):
    result = supabase.table("milestones").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log milestone")
    status_word = "achieved" if payload.achieved else "not yet achieved"
    retain_memory(
        payload.child_id,
        f"Developmental milestone — {payload.domain}: '{payload.label}' — {status_word} on {payload.date or 'today'}. Notes: {payload.notes or 'none'}."
    )
    return result.data[0]


@app.get("/children/{child_id}/milestones")
def get_milestones(child_id: str):
    result = supabase.table("milestones").select("*").eq("child_id", child_id).execute()
    return result.data


@app.get("/children/{child_id}/milestones/insights")
def get_milestone_insights(child_id: str):
    """Uses Hindsight reflect() to surface developmental patterns."""
    insight = reflect_on_query(
        child_id=child_id,
        query="Analyze developmental milestone patterns and flag any clusters worth discussing with a pediatrician.",
    )
    return {"insights": insight}


# ═══════════════════════════════════════════════════════════════════════════════
# PARENTING COACH
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/parenting/moment", status_code=201)
def log_parenting_moment(payload: ParentingMomentCreate):
    result = supabase.table("parenting_moments").insert(payload.dict()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to log moment")
    retain_memory(
        payload.child_id,
        f"Parenting moment on {payload.date or 'today'}: Situation='{payload.situation}', "
        f"Tried='{payload.tried}', Outcome={payload.outcome}. Notes: {payload.note or 'none'}."
    )
    return result.data[0]


@app.get("/children/{child_id}/parenting/moments")
def get_parenting_moments(child_id: str):
    result = supabase.table("parenting_moments").select("*").eq("child_id", child_id).order("date", desc=True).execute()
    return result.data


@app.post("/parenting/coach")
def coach_query(payload: CoachQuery):
    """Conversational parenting coach using Hindsight reflect() on experience + opinion bank."""
    response = reflect_on_query(
        child_id=payload.child_id,
        query=payload.question,
        context="You are an empathetic parenting coach. Draw from all logged parenting moments and outcomes."
    )
    return {"response": response}


@app.get("/children/{child_id}/parenting/playbook")
def get_playbook(child_id: str):
    """Monthly playbook: what works, what doesn't, patterns."""
    playbook = reflect_on_query(
        child_id=child_id,
        query=(
            "Generate a monthly parenting playbook. List: "
            "1) What consistently works, "
            "2) What backfires, "
            "3) Emerging patterns or tilt indicators."
        ),
    )
    return {"playbook": playbook}


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT — Doctor Visit PDF
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/children/{child_id}/export/pdf")
def export_visit_pdf(child_id: str):
    """Generate and return a doctor visit summary PDF using Hindsight recall()."""
    child_result = supabase.table("children").select("*").eq("id", child_id).single().execute()
    if not child_result.data:
        raise HTTPException(status_code=404, detail="Child not found")
    child = child_result.data
    child["id"] = child_id

    # Fetch all health data
    vaccines = supabase.table("vaccines").select("*").eq("child_id", child_id).execute().data or []
    allergies = supabase.table("allergies").select("*").eq("child_id", child_id).execute().data or []
    medications = supabase.table("medications").select("*").eq("child_id", child_id).execute().data or []

    pdf_bytes = generate_visit_pdf(
        child=child,
        health_data={"vaccines": vaccines, "allergies": allergies, "medications": medications},
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=peds-{child.get('name', 'child')}-visit-summary.pdf"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-PILLAR INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/children/{child_id}/insights")
def get_cross_pillar_insights(child_id: str):
    """
    The flagship Hindsight feature: cross-pillar synthesis.
    Finds correlations across health, development, and parenting data.
    """
    insights = reflect_on_query(
        child_id=child_id,
        query=(
            "Synthesize patterns across all domains: "
            "health history, symptom episodes, developmental milestones, and parenting moments. "
            "Identify any correlations — e.g. illness affecting behavior, "
            "developmental regressions coinciding with health events, "
            "or parenting strategies that correlate with outcomes."
        ),
    )
    return {"insights": insights}
