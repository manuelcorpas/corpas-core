#!/usr/bin/env python3
"""CLI entry point for the Corpas-Core Constitution governance system.

Usage:
    python 08-cli.py validate
    python 08-cli.py govern "build HEIM validation framework"
    python 08-cli.py govern --draft "I hope this finds you well" "reply to collaborator"
    python 08-cli.py govern --source email "send reply to funder"
    python 08-cli.py ledger-read [--last N]

No side effects at module scope.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from importlib.util import spec_from_file_location, module_from_spec


def _load_sibling(name: str, filename: str):
    spec = spec_from_file_location(name, Path(__file__).parent / filename)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_validate(args: argparse.Namespace) -> int:
    constitution = _load_sibling("constitution", "01-constitution.py")
    try:
        config = constitution.load()
        version = config["meta"]["version"]
        print(f"Constitution valid (v{version})")
        print(f"  Rules: {len(config['decision_rules'])}")
        print(f"  Modes: {len(config['modes'])}")
        print(f"  Invariants: {len(config['invariants'])}")
        print(f"  Hash: {constitution.file_hash()[:16]}...")
        return 0
    except Exception as e:
        print(f"INVALID: {e}", file=sys.stderr)
        return 1


def cmd_govern(args: argparse.Namespace) -> int:
    govern_mod = _load_sibling("govern", "07-govern.py")

    context = {}
    if args.source:
        context["source"] = args.source
    if args.approved:
        context["principal_approved"] = True

    result = govern_mod.govern(
        action=args.action,
        context=context if context else None,
        draft_output=args.draft,
        log=not args.no_log,
    )

    output = {
        "allowed": result.allowed,
        "verdict": result.verdict.value,
        "mode": result.mode.value,
        "confidence": result.confidence,
        "is_high_stakes": result.is_high_stakes,
        "requires_principal_approval": result.requires_principal_approval,
        "rationale": result.rationale,
        "recommended_next_action": result.recommended_next_action,
    }

    if result.block_reason:
        output["block_reason"] = result.block_reason
    if result.manipulation_flags:
        output["manipulation_flags"] = result.manipulation_flags
    if result.critic_result:
        output["critic"] = {
            "passed": result.critic_result.passed,
            "score": result.critic_result.score,
            "violations": result.critic_result.violations,
        }

    output["rules"] = {
        rid: {"passed": r.passed, "rationale": r.rationale}
        for rid, r in result.rules_evaluated.items()
    }

    print(json.dumps(output, indent=2))
    return 0 if result.allowed else 1


def cmd_ledger_read(args: argparse.Namespace) -> int:
    ledger = _load_sibling("decision_ledger", "06-decision_ledger.py")
    entries = ledger.read_last(args.last)
    if not entries:
        print("No ledger entries found.")
        return 0
    for entry in entries:
        summary = {
            "timestamp": entry.timestamp,
            "verdict": entry.verdict.value,
            "mode": entry.mode_classification.value,
            "confidence": entry.confidence,
            "allowed": entry.allowed,
        }
        if entry.block_reason:
            summary["block_reason"] = entry.block_reason
        print(json.dumps(summary))
    print(f"\n{ledger.count()} total entries")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Corpas-Core Constitution Governance System"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("validate", help="Validate the constitution YAML")

    govern_p = sub.add_parser("govern", help="Run governance check on an action")
    govern_p.add_argument("action", help="Description of the action to evaluate")
    govern_p.add_argument("--draft", help="Optional draft output to critic-check")
    govern_p.add_argument("--source", help="Source context (email, attachment, etc.)")
    govern_p.add_argument("--approved", action="store_true", help="Principal has approved")
    govern_p.add_argument("--no-log", action="store_true", help="Skip ledger logging")

    ledger_p = sub.add_parser("ledger-read", help="Read recent ledger entries")
    ledger_p.add_argument("--last", type=int, default=10, help="Number of entries (default 10)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    commands = {
        "validate": cmd_validate,
        "govern": cmd_govern,
        "ledger-read": cmd_ledger_read,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
