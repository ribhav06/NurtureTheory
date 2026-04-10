-- Pēds Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Children ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS children (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    dob DATE NOT NULL,
    blood_type TEXT,
    weight_kg NUMERIC(5,2),
    height_cm NUMERIC(5,1),
    conditions TEXT[] DEFAULT '{}',
    age_label TEXT,
    created_at DATE DEFAULT CURRENT_DATE,
    parent_id UUID  -- for future auth integration
);

-- ─── Allergies ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    substance TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('anaphylactic', 'moderate', 'mild')),
    reaction_type TEXT,
    epipen BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Vaccines ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vaccines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    date_given DATE,
    status TEXT NOT NULL DEFAULT 'done' CHECK (status IN ('done', 'overdue', 'due-soon')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Medications ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    dose TEXT NOT NULL,
    frequency TEXT NOT NULL,
    last_given DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Growth Records ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS growth_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    weight_kg NUMERIC(5,2),
    height_cm NUMERIC(5,1),
    head_cm NUMERIC(4,1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Symptom Logs ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS symptom_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    symptom_text TEXT NOT NULL,
    response_narrative TEXT,
    escalated BOOLEAN DEFAULT FALSE,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Milestones ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    domain TEXT NOT NULL CHECK (domain IN ('motor', 'language', 'cognitive', 'social-emotional', 'social')),
    label TEXT NOT NULL,
    achieved BOOLEAN DEFAULT FALSE,
    date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Parenting Moments ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parenting_moments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    situation TEXT NOT NULL,
    tried TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('worked', 'mixed', 'backfired')),
    note TEXT,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Row Level Security (enable but allow all for now) ────────────────────────
ALTER TABLE children ENABLE ROW LEVEL SECURITY;
ALTER TABLE allergies ENABLE ROW LEVEL SECURITY;
ALTER TABLE vaccines ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE growth_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE symptom_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE parenting_moments ENABLE ROW LEVEL SECURITY;

-- Temporary open policies for development (tighten with auth in prod)
CREATE POLICY "Allow all" ON children FOR ALL USING (true);
CREATE POLICY "Allow all" ON allergies FOR ALL USING (true);
CREATE POLICY "Allow all" ON vaccines FOR ALL USING (true);
CREATE POLICY "Allow all" ON medications FOR ALL USING (true);
CREATE POLICY "Allow all" ON growth_records FOR ALL USING (true);
CREATE POLICY "Allow all" ON symptom_logs FOR ALL USING (true);
CREATE POLICY "Allow all" ON milestones FOR ALL USING (true);
CREATE POLICY "Allow all" ON parenting_moments FOR ALL USING (true);
