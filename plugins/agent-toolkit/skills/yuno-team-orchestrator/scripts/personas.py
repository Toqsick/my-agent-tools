#!/usr/bin/env python3
"""
Yuno Team Orchestrator — Routing Engine
========================================

Liest personas.yaml und matcht eine User-Anfrage gegen die Routing-Tabelle.
Gibt aus: Persona-Name, Trigger, Toolset-Hints, fertigen Subagent-Briefing-Preamble.

Usage:
    python3 personas.py route "build me a Python CLI that summarizes CSVs"
    python3 personas.py route "what's the latest in vector databases?"
    python3 personas.py list                     # alle Personas anzeigen
    python3 personas.py preamble engineer       # roher System-Prompt
    python3 personas.py match "fix the login bug in auth.py"

Author: Yuno (Hermes)
Built: 2026-07-07
"""
from __future__ import annotations
import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML fehlt. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


SKILL_DIR = Path(__file__).resolve().parent.parent
PERSONAS_FILE = SKILL_DIR / "personas.yaml"


def load_registry() -> dict[str, Any]:
    """Lade die personas.yaml und validiere Struktur."""
    if not PERSONAS_FILE.exists():
        print(f"ERROR: {PERSONAS_FILE} nicht gefunden.", file=sys.stderr)
        sys.exit(2)
    with open(PERSONAS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "personas" not in data or "routing_table" not in data:
        print("ERROR: personas.yaml unvollständig.", file=sys.stderr)
        sys.exit(2)
    return data


def match_persona(task: str, registry: dict[str, Any]) -> list[tuple[str, list[str]]]:
    """
    Matche eine Task-Beschreibung gegen alle Persona-Trigger.
    Returns: List of (persona_key, matched_triggers), sortiert nach Match-Count desc.
    """
    task_lower = task.lower()
    matches: list[tuple[str, list[str], int]] = []

    for persona_key, route in registry["routing_table"].items():
        persona = registry["personas"].get(persona_key)
        if not persona:
            continue
        # Trigger-Match: Wort-Boundary + Lowercase
        matched = []
        for trigger in route["triggers"]:
            trigger_lower = trigger.lower()
            pattern = r"\b" + re.escape(trigger_lower) + r"\b"
            if re.search(pattern, task_lower):
                matched.append(trigger)
                continue
            # Multi-Word-Trigger: Fallback auf "any word in trigger present"
            # (z.B. "write a doc" matched auch "write doc" oder "write the doc")
            words = [w for w in trigger_lower.split() if len(w) > 2 and w not in {"the", "a", "an", "is", "me"}]
            if words and all(re.search(r"\b" + re.escape(w) + r"\b", task_lower) for w in words):
                matched.append(trigger)
        if matched:
            matches.append((persona_key, matched, len(matched)))

    # Sortier-Logik:
    # 1. Wenn Verifier mit Gate-Phrase matched (audit/verify/check/is this done),
    #    dominiert Verifier (Gate-Priorität).
    # 2. Sonst: Match-Count desc.
    verifier_gate_match = any(
        p == "verifier" and any(
            t in {"verify", "audit", "is this done", "check this", "validate", "qa", "review", "gate"}
            for t in triggers
        )
        for p, triggers, _ in matches
    )
    if verifier_gate_match:
        # Verifier nach vorne, Rest nach Match-Count
        matches.sort(key=lambda x: (0 if x[0] == "verifier" else 1, -x[2]))
    else:
        matches.sort(key=lambda x: -x[2])
    return [(p, t) for p, t, _ in matches]


def build_preamble(persona_key: str, registry: dict[str, Any]) -> str:
    """Baut den fertigen Subagent-Context-Preamble (System-Prompt + Rolle)."""
    persona = registry["personas"].get(persona_key)
    if not persona:
        return f"# Unknown persona: {persona_key}"
    return textwrap.dedent(f"""\
        # ═══════════════════════════════════════════════════
        #  PERSONA: {persona['name']} ({persona['role']})
        #  Specialty: {persona['specialty']}
        #  Color: {persona.get('color', 'n/a')}
        # ═══════════════════════════════════════════════════

        {persona['system_prompt'].strip()}

        # ────────────────────────────────────────────────────
        #  Working contract for this run:
        #  - You are an isolated subagent. The parent (Yuno) is waiting.
        #  - Deliver: a clear, structured result the parent can synthesize.
        #  - If blocked: name the EXACT missing piece. Do NOT guess.
        #  - When done: report file:line references, test outputs, risks.
        # ────────────────────────────────────────────────────
    """)


def detect_multi_domain(matches: list[tuple[str, list[str]]], task: str) -> bool:
    """
    Multi-Domain-Detection:
    - 2+ Personas aus verschiedenen Domänen matchen, ODER
    - Verifier-Co-Flag in Task (Gate-Phrasen)
    """
    if len(matches) >= 2:
        # Wenn Verifier dabei ist: das ist ein Review-Gate, nicht Multi-Domain-Bau
        non_verifier = [m for m in matches if m[0] != "verifier"]
        if len(non_verifier) >= 2:
            return True
    return False


def cmd_route(task: str) -> int:
    """Hauptfunktion: route einen Task."""
    registry = load_registry()
    matches = match_persona(task, registry)

    if not matches:
        print("⚠️  Kein Persona-Trigger matched.")
        print(f"   Task: {task!r}")
        print()
        print("Verfügbare Trigger:")
        for p, route in registry["routing_table"].items():
            print(f"  {p}: {', '.join(route['triggers'][:5])}…")
        return 1

    print(f"📥 Task: {task!r}\n")

    multi = detect_multi_domain(matches, task)
    if multi:
        print("🔀 MULTI-DOMAIN DETECTED\n")
        print("Decomposition-Plan:")
        print("  1. Dispatch jede matchende Persona als isolierten Subagent")
        print("  2. Yuno (parent) synthetisiert die Ergebnisse")
        print("  3. Verifier wird als finales Gate gefeuert\n")
        print("Matches (sortiert nach Match-Score):")
    else:
        print("🎯 Single-Domain Route:")

    for persona_key, triggers in matches:
        persona = registry["personas"][persona_key]
        route = registry["routing_table"][persona_key]
        print(f"  → {persona['name']:12s} ({persona['role']:8s}) | matched: {triggers}")
        print(f"    Toolsets: {', '.join(route['toolset_hints'])}")
        print()

    if not multi:
        # Top-Match → zeige Preamble-Header
        top = matches[0][0]
        persona = registry["personas"][top]
        print(f"📋 Recommended dispatch:")
        print(f"   delegate_task(")
        print(f"       goal=<kurze Task-Beschreibung>,")
        print(f"       context=<siehe unten>,")
        print(f"       toolsets={registry['routing_table'][top]['toolset_hints']!r}")
        print(f"   )")
        print()
        print(f"─── PREAMBLE (für `context`-Feld) ───")
        print(build_preamble(top, registry))
    return 0


def cmd_match(task: str) -> int:
    """Nur Trigger-Match-Output, ohne Preamble."""
    registry = load_registry()
    matches = match_persona(task, registry)
    if not matches:
        print("NO_MATCH")
        return 1
    print(",".join(f"{p}:{'+'.join(t)}" for p, t in matches))
    return 0


def cmd_preamble(persona_key: str) -> int:
    """Zeige den vollen System-Prompt einer Persona."""
    registry = load_registry()
    print(build_preamble(persona_key, registry))
    return 0


def cmd_list() -> int:
    """Liste alle Personas auf."""
    registry = load_registry()
    print(f"Yuno's Team — {len(registry['personas'])} Personas")
    print(f"Built: {registry.get('built', '?')}  Source: {registry.get('source', '?')}\n")
    for key, persona in registry["personas"].items():
        route = registry["routing_table"][key]
        print(f"  ▸ {persona['name']:12s} ({persona['role']:8s}) — {persona['specialty']}")
        print(f"    Color: {persona.get('color', 'n/a')}  Toolsets: {', '.join(route['toolset_hints'])}")
        print(f"    Top-Triggers: {', '.join(route['triggers'][:5])}")
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="personas.py",
        description="Yuno Team Orchestrator — Routing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s route "build me a Python CLI that summarizes CSVs"
              %(prog)s route "what's the latest in vector databases?"
              %(prog)s match "fix the login bug"
              %(prog)s preamble engineer
              %(prog)s list
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_route = sub.add_parser("route", help="Route eine Task-Beschreibung")
    p_route.add_argument("task", help="Task-Beschreibung")

    p_match = sub.add_parser("match", help="Nur Trigger-Match")
    p_match.add_argument("task", help="Task-Beschreibung")

    p_preamble = sub.add_parser("preamble", help="Zeige Persona-System-Prompt")
    p_preamble.add_argument("persona", help="Persona-Key (engineer, researcher, ...)")

    sub.add_parser("list", help="Liste alle Personas")

    args = parser.parse_args()

    if args.command == "route":
        return cmd_route(args.task)
    if args.command == "match":
        return cmd_match(args.task)
    if args.command == "preamble":
        return cmd_preamble(args.persona)
    if args.command == "list":
        return cmd_list()
    return 2


if __name__ == "__main__":
    sys.exit(main())