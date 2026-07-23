#!/usr/bin/env python3
"""audit-secret-spread.py — Forensischer Secret-Audit für Hermes-Sessions

Liest read-only aus ~/.hermes/state.db (Tabelle messages, session = SID) und
prüft für jeden Wert aus jedem .env im Projekt-Tree, wie oft der Wert dort in
content oder tool_calls auftaucht. Ausgabe: NUR Prefix, Länge, Hit-Count,
Schweregrad — niemals der Klartext.

Verwendung:
  python3 audit-secret-spread.py <session_id> <repo_root>

Honoring Bastis Vorliebe (2026-07-13 Audit):
- read-only (SQLite mode=ro via URI)
- keine Auto-Rotation, nur Diagnose
- Secret-Values erscheinen ausschließlich als Prefix + Länge in der Ausgabe
- Schweregrad-Mapping für Klärungs-Workflow mit dem User

Pitfalls sind inline dokumentiert; siehe auch system-security-audit SKILL.md
Sektion 'Forensischer Secret-Audit für Cloud-Coding-Agenten'.
"""
import sqlite3
import sys
import re
from pathlib import Path

SECRET_LINE = re.compile(
    r"^[A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)(?:\s|$)", re.IGNORECASE
)
MIN_LEN = 16


def collect_secrets(repo: Path) -> dict[str, list[tuple[str, str, int]]]:
    """Sammelt (env_file, prefix, length) Tupel. NIEMALS den Klartext nach außen geben.

    Returns: dict mit Variable-Name als Key, Liste der (file, prefix, len) Tupel.
    """
    found: dict[str, list[tuple[str, str, int]]] = {}
    env_files = (
        [repo / ".env", repo / "backend" / ".env"]
        + [p for p in repo.rglob(".env") if p.is_file()]
    )
    # Deduplizieren
    seen = set()
    for env_file in env_files:
        if not env_file.exists() or env_file.resolve() in seen:
            continue
        seen.add(env_file.resolve())
        try:
            text = env_file.read_text(errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            value = value.strip().strip("'\"")
            if not SECRET_LINE.match(name + " "):
                continue
            if not value or len(value) < MIN_LEN:
                continue
            # Mindestens 3 verschiedene Zeichen in Position 4-7.
            # Vermeidet False-Positives auf Test-Fixtures wie
            # `KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA`.
            if len(set(value[4:8])) < 3:
                continue
            prefix = value[:4]
            length = len(value)
            found.setdefault(name, []).append((str(env_file), prefix, length))
    return found


def secret_value_in_db(repo: Path, var_name: str) -> str | None:
    """Lädt NUR für die Secret-Suche den vollen Wert; gibt ihn nie aus."""
    for env_file in [repo / ".env", repo / "backend" / ".env"]:
        if not env_file.exists():
            continue
        for line in env_file.read_text(errors="ignore").splitlines():
            if line.startswith(f"{var_name}="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return None


def grade(hits_in_messages: int) -> tuple[str, str]:
    """Mapping: (Schwere, Aktion)."""
    if hits_in_messages == 0:
        return ("🟢", "kein Leak-Pfad über Inferenz; File-Perm prüfen (sollte 600)")
    if hits_in_messages >= 1:
        return ("🔴", "OFFENGELT — Rotation sofort freigeben lassen (NICHT auto-fixen)")
    return ("🟡", "manuell prüfen")


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "Verwendung: python3 audit-secret-spread.py <session_id> <repo_root>",
            file=sys.stderr,
        )
        return 2
    sid = sys.argv[1]
    repo = Path(sys.argv[2]).resolve()
    if not repo.is_dir():
        print(f"Repo-Root existiert nicht: {repo}", file=sys.stderr)
        return 2

    db = Path.home() / ".hermes" / "state.db"
    if not db.exists():
        print(f"state.db nicht gefunden: {db}", file=sys.stderr)
        return 2

    secrets = collect_secrets(repo)
    if not secrets:
        print(f"Keine .env-Werte in {repo} gefunden (oder keine >= {MIN_LEN} chars).")
        return 0

    # Read-only Connection via URI
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.OperationalError as e:
        print(f"SQLite open fehlgeschlagen: {e}", file=sys.stderr)
        return 2

    rows = con.execute(
        "SELECT id, content, tool_calls FROM messages "
        "WHERE session_id=? ORDER BY id",
        (sid,),
    ).fetchall()
    con.close()

    print(f"Session: {sid}")
    print(f"Repo:    {repo}")
    print(f"DB:      {db} (read-only)")
    print(f"Messages: {len(rows)} | Secrets: {len(secrets)}")
    print()

    n_open = 0
    for var_name, occurrences in sorted(secrets.items()):
        value = secret_value_in_db(repo, var_name)
        if not value:
            continue
        hits_content = 0
        hits_toolcalls = 0
        for _id, content, tool_calls in rows:
            if content and value in content:
                hits_content += content.count(value)
            if tool_calls and value in tool_calls:
                hits_toolcalls += tool_calls.count(value)
        total = hits_content + hits_toolcalls
        sev, action = grade(total)
        for env_file, prefix, length in occurrences:
            location = Path(env_file).relative_to(repo) if Path(env_file).is_relative_to(repo) else env_file
            print(
                f"  {sev} {var_name:<20} prefix={prefix!r:<10} len={length:<4} "
                f"msgs={hits_content:<3} tools={hits_toolcalls:<3} → {action}"
            )
            print(f"    file={location}")
        if total:
            n_open += 1

    print()
    print(f"Analyse: {n_open}/{len(secrets)} Schlüssel in Modellkontext nachweisbar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
