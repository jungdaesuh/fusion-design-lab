# Pivot: P1 Rotating-Ellipse Environment

**Date:** March 7, 2026
**Role:** Short decision record
**Status:** Not an active SSOT surface

## Decision

Pivot the environment to the official `P1` benchmark with real `constellaration` physics and a repaired low-dimensional boundary family derived from a rotating-ellipse seed.

## Why

- the historical upstream 3-knob family could not satisfy the `P1` triangularity requirement
- the repaired 4-knob family restored a meaningful low-dimensional control surface
- the hackathon artifact needs a narrow, legible, human-playable environment rather than a transplanted optimization harness

## What This Does Not Mean

- it does not make the low-dimensional family the full `P1` design space
- it does not justify porting the old `ai-sci-feasible-designs` harness
- it does not settle repaired-family ranges, deltas, or budget choices without measurement

## Where The Live Truth Now Lives

- planning and execution: [`../FUSION_DESIGN_LAB_PLAN_V2.md`](../FUSION_DESIGN_LAB_PLAN_V2.md)
- technical contract: [`../P1_ENV_CONTRACT_V1.md`](../P1_ENV_CONTRACT_V1.md)
- blocker and sweep evidence: [`../P1_PARAMETERIZATION_DEEPDIVE.md`](../P1_PARAMETERIZATION_DEEPDIVE.md)
