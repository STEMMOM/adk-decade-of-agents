# Institutional Makefile v1 — Constitutional Definition

## Status
Active

## Scope
Repository-wide institutional enforcement

## Purpose

This Makefile defines the **mandatory institutional gates** of the repository.

It is not a convenience script.
It is the executable entrance to the system’s constitutional order.

Any change to the system that bypasses these gates is considered
**institutionally invalid**, regardless of whether the code runs.

---

## Core Principle

> Protocols are the highest law.
> 
> Code must prove compliance before progress is allowed.

This repository does not treat specifications as documentation.
Protocols are enforceable contracts, and tests are their execution.

---

## Institutional Role of the Makefile

The Makefile serves as:

- The **canonical entry point** for institutional verification
- The **only sanctioned shortcut** for critical checks
- A **non-optional ritual** before system evolution

Human developers, AI agents, and automation bots are all subject to the same gates.

---

## Defined Gates

### 1. `make protocol-check`

**Role:** Highest Law Verification

This gate verifies that all declared protocol contracts still hold.

Specifically, it enforces:
- JSON schema validity
- Invariant correctness
- Canonicalization determinism
- Hash and replay stability

If this gate fails, **no further action is legitimate**.

---

### 2. `make institution-check`

**Role:** Constitutional Admission Gate

This is the umbrella gate for all mandatory institutional checks.

At v1, it aliases `protocol-check`.

In future versions, it may include:
- Replay verification
- Governance rules
- Release intent validation

Scripts, CI systems, and bots MUST use this target
instead of calling underlying tools directly.

---

### 3. `make clean`

**Role:** Hygiene Utility

This target has no institutional meaning.
It exists only to remove local execution noise.

---

## Prohibited Practices

The following are explicitly disallowed:

- Running protocol tests ad-hoc while skipping `make protocol-check`
- Adding new mandatory checks outside the Makefile
- Treating the Makefile as a developer convenience rather than a gate
- Bypassing the Makefile in automation or CI

---

## Evolution Rule

Changes to this Makefile are **constitutional changes**.

They MUST:
- Be intentional
- Be reviewed with the same rigor as protocol changes
- Preserve backward institutional meaning unless explicitly versioned

---

## One-Line Summary

> The Makefile is not how the system is built.
> 
> It is how the system proves it deserves to continue.
