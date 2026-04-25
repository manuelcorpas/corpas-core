# Corpas-Core: Constitutional Governance Gateway

Source code for the governance system described in:

> Corpas, M. (2026). Corpas-Core: A Constitutional Architecture for Personal Agentic AI Systems. Preprint.

## Overview

A single enforceable governance gateway (`govern()`) through which every agent must pass before acting. Layer 0 is fully deterministic: no LLM calls, auditable, validated by 72 tests.

## Quick Start

```bash
# Validate the constitution
python3 08-cli.py validate

# Score an action
python3 08-cli.py govern "Build HEIM genomic equity benchmark framework"

# Score with draft output (critic check)
python3 08-cli.py govern --draft "I hope this finds you well" "Write reply to collaborator"

# Read decision ledger
python3 08-cli.py ledger-read --last 5

# Run tests
python3 -m pytest TESTS/ -v
```

## Requirements

- Python 3.11+
- pydantic >= 2.0
- PyYAML >= 6.0
- pytest (for tests)

## Files

| File | Purpose |
|------|---------|
| `00-constitution.yaml` | Machine-readable constitution (v0.2.0) |
| `00-models.py` | Pydantic schemas (GovernResult, CriticOutput, LedgerEntry) |
| `01-constitution.py` | YAML parser with validation and caching |
| `02-invariants.py` | Hard invariant checks (run first, block immediately) |
| `03-router.py` | Mode classification via keyword matching |
| `04-strategy_aligner.py` | R1-R5 rule evaluation |
| `05-critic.py` | Draft output quality scoring |
| `06-decision_ledger.py` | Append-only JSONL writer/reader |
| `07-govern.py` | The governance gateway: `govern()` public API |
| `08-cli.py` | CLI wrapper |

## Governance Pipeline

```
govern(action, context, draft_output) -> GovernResult

1. Load + validate constitution (cached)
2. Manipulation detection (always runs)
3. Hard invariant check (violations block immediately)
4. High-stakes detection
5. Route into mode
6. Score against R1-R5
7. Confidence scoring
8. Abstention check
9. Critic (if draft provided)
10. Log to decision ledger (append-only JSONL with SHA-256 hashes)
```

## Tests

72 tests covering:
- Model validation (6)
- Constitution parsing (8)
- Invariant enforcement (8)
- Mode routing (7)
- Strategy alignment (12)
- Output criticism (8)
- Decision ledger (4)
- End-to-end governance (10)
- Prompt injection / adversarial inputs (13)

## Licence

MIT

## Citation

```
Corpas, M. (2026). Corpas-Core: A Constitutional Architecture for Personal
Agentic AI Systems. Preprint. https://github.com/manuelcorpas/corpas-core
```
