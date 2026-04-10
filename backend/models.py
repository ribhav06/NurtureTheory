from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


# ── Child ────────────────────────────────────────────────────────────────────

class AllergyIn(BaseModel):
    substance: str
    severity: str          # anaphylactic | moderate | mild
    reaction_type: Optional[str] = None
    epipen: bool = False

class ChildCreate(BaseModel):
    name: str
    dob: str               # ISO date e.g. 2022-03-15
    blood_type: Optional[str] = None
    conditions: Optional[List[str]] = []
    allergies: Optional[List[AllergyIn]] = []

class ChildUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    blood_type: Optional[str] = None
    conditions: Optional[List[str]] = None


# ── Health Vault ─────────────────────────────────────────────────────────────

class VaccineCreate(BaseModel):
    child_id: str
    name: str
    date_given: Optional[str] = None
    status: str = "done"   # done | overdue | due-soon

class AllergyCreate(BaseModel):
    child_id: str
    substance: str
    severity: str
    reaction_type: Optional[str] = None
    epipen: bool = False

class MedicationCreate(BaseModel):
    child_id: str
    name: str
    dose: str
    frequency: str
    last_given: Optional[str] = None
    notes: Optional[str] = None

class GrowthCreate(BaseModel):
    child_id: str
    date: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    head_cm: Optional[float] = None


# ── Symptom Guide ─────────────────────────────────────────────────────────────

class SymptomQuery(BaseModel):
    child_id: str
    symptom_text: str

class SymptomResponse(BaseModel):
    narrative: str
    home_care: List[str]
    escalation_er: List[str]
    escalation_doctor: List[str]
    dosing: Optional[List[dict]] = None
    disclaimer: str = "This is not a medical diagnosis. Call your pediatrician when in doubt."


# ── Development Tracker ───────────────────────────────────────────────────────

class MilestoneCreate(BaseModel):
    child_id: str
    domain: str            # motor | language | cognitive | social-emotional
    label: str
    achieved: bool = False
    date: Optional[str] = None
    notes: Optional[str] = None


# ── Parenting Coach ───────────────────────────────────────────────────────────

class ParentingMomentCreate(BaseModel):
    child_id: str
    situation: str
    tried: str
    outcome: str           # worked | mixed | backfired
    note: Optional[str] = None
    date: Optional[str] = None

class CoachQuery(BaseModel):
    child_id: str
    question: str
