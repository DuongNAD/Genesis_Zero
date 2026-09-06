# Project Plan — Genesis Zero

## Objective
Coordinate the full development lifecycle for Genesis Zero across R1 (Codebase Integrity & Bug Fixing), R2 (1-Command Setup & Launcher), and R3 (3D Visualizer & Compact Map Experience).

## Phase 0: Survey & Scoping
- Spawn 3 parallel Explorers:
  - Explorer 1: Deep dive into simulation core, referee, network/server/client, security/hostile probing, and existing test suite.
  - Explorer 2: Deep dive into environment setup, launcher scripts, preflight checks, dependency management (venv, cross-platform macOS/Linux/Windows), LLM backend adapters (mock/reflex, Ollama, llama.cpp, vLLM).
  - Explorer 3: Deep dive into web visualizer (`web/watch3d.html`), Three.js architecture, map grid/layers, 3-tier biome representation, organism morphology rendering, real-time Law Journal and law activation visualization.
- Synthesize survey into `PROJECT.md` (Architecture, Feature Inventory, Milestones, Code Layout, Interfaces) and `TEST_INFRA.md`.

## Phase 1: Dual Track Execution
- Track 1: Implementation Sub-Orchestrators
  - Milestone 1: Simulation core fixes, referee scoring accuracy, server/client protocols, hostile probe defense, full test coverage.
  - Milestone 2: 1-Command cross-platform launcher, auto-venv, smart preflight with auto-remediation, quickstart documentation (<3 mins).
  - Milestone 3: 3D Visualizer upgrade: compact map framing, 3-tier ecosystem visuals, trait-based 3D morphology, real-time Law Journal event animations.
- Track 2: E2E Testing Track
  - Design and build 4-tier requirement-driven opaque-box E2E test suite.
  - Deliver `TEST_READY.md`.

## Phase 2: Final Integration & Hardening
- Final Milestone Phase 1: Pass 100% of E2E Test Suite (Tiers 1-4).
- Final Milestone Phase 2: Tier 5 Adversarial Coverage Hardening with Challenger -> Worker -> Reviewer loop.

## Phase 3: Final Verification & Reporting
- Full verification of preflight, hostile probe defense, demo run, and quickstart documentation.
- Submit comprehensive completion report.
