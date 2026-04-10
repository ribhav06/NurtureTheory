# Pēds - Phase 1 MVP Implementation Plan

This plan outlines the architecture setup and initial development steps for Phase 1 (MVP) of Pēds: Pediatric Co-Pilot, based on your PRD. The goal is to scaffold the foundational systems and build out the **Health Vault** and **Symptom Guide** pillars.

## User Review Required

> [!IMPORTANT]
> Please review the infrastructure choices and phased layout below. Let me know if you are ready to begin the **Project Initialization** phase, or if you'd like to adjust the tech stack or MVP scope first.

## Proposed Architecture & Setup

We will organize the `NurtureTheory` repository into a monorepo structure with two main directories: `mobile` and `backend`.

### 1. Mobile Client setup (`/mobile`)
- **Framework**: Expo (React Native) targeting iOS and Android.
- **Languages**: TypeScript for type safety.
- **Key Libraries**: 
  - `@supabase/supabase-js` for Auth & Database integration.
  - `expo-router` for navigation.
  - UI framework (e.g., Nativewind or Tamagui for styling, depending on your preference).

### 2. Backend API setup (`/backend`)
- **Framework**: FastAPI (Python 3.11+).
- **Core Dependencies**:
  - `supabase` client for server-side operations.
  - `httpx` or dedicated Anthropic SDK for Claude LLM integration.
  - `vectorize-io/hindsight` integration for the agent memory bank.
- **Orchestration**: Docker & Docker Compose for easy local development.

### 3. Database & Auth (Supabase)
- Set up the Supabase project.
- **Schema Mapping**:
  - `users` / `profiles` (Parents)
  - `children` (Profiles per child)
  - `health_records` (Vaccines, allergies, medications, growth tracking)
  - `symptom_logs` (History of symptom sessions and escalations)

## Development Phases

### Phase 1.1: Project Initialization
1. Create Expo frontend in `NurtureTheory/mobile`.
2. Create FastAPI backend in `NurtureTheory/backend`.
3. Set up pre-commit hooks, linting, and basic Dockerization for the backend.
4. Define the Supabase database migrations (schema tables).

### Phase 1.2: Core Integration & App Onboarding
1. Implement Supabase Authentication (Email/Password & SSO stubs).
2. Build the Child Profile Onboarding flow on the mobile app.
3. Configure the Hindsight agent setup endpoint for a newly created child (`set_bank_config`).

### Phase 1.3: Health Vault Pillar
1. Implement CRUD operations in FastAPI for vaccination, allergens, and medications.
2. Build the UI for the Health Vault (screens, forms, lists).
3. Implement the Doctor Visit PDF export generation.

### Phase 1.4: Symptom Guide Pillar
1. Build natural language chat UI (text + voice-to-text integration).
2. Implement the `reflect()` API via Hindsight & Claude for triage.
3. **Safety Guardrails**: Implement hard-coded structured escalations (Go to ER / Go to Doctor).

## Open Questions

> [!WARNING]
> 1. **Supabase Setup**: Do you already have a Supabase project created, or should we use local Supabase for development?
> 2. **Hindsight Usage**: Do you have the Hindsight Docker / API keys ready for integration?
> 3. **Anthropic Key**: We will need an Anthropic API key to securely call Claude from the backend. Are we setting this up now?
> 4. **UI Styling**: Do you have a preferred styling framework for the Expo app (e.g., NativeWind/Tailwind, standard StyleSheet, Tamagui)?

## Verification Plan

### Automated Tests
- Pytest for FastAPI routing and backend logic constraints (e.g., ensuring escalations always trigger properly).
- Jest for React Native component rendering.

### Manual Verification
- Testing the Expo app locally using an iOS Simulator or Android Emulator.
- Verifying that Hindsight accurately maintains context across sessions.
- Validating the safety guidelines and 'Go to ER' hard triggers.
