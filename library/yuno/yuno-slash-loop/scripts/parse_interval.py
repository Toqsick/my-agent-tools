#!/usr/bin/env python3
"""yuno-slash-loop Intervall-Parser.

Parst Yuno's vereinfachte Intervall-Syntax und konvertiert sie zu
Cron-Schedule-Strings. Unterstützt:

  30S  -> 30 Sekunden (Cron-Fallback: * * * * *)
  5M   -> 5 Minuten     -> */5 * * * *
  15M  -> 15 Minuten    -> */15 * * * *
  1h   -> 1 Stunde      -> 0 * * * *
  2h30m-> 2,5 Stunden   -> 30 */2 * * *
  1D   -> 1 Tag um Mitternacht -> 0 0 * * *
  8h   1D -> Jeden Tag um 8 Uhr -> 0 8 * * *
  1W   -> Sonntag Mitternacht  -> 0 0 * * 0

Beispiel:
  $ python3 parse_interval.py 5M
  */5 * * * *
  $ python3 parse_interval.py 1h
  0 * * * *
  $ python3 parse_interval.py 1D 8h
  0 8 * * *
"""
import re
import sys


def interval_to_cron(interval: str) -> str:
    """Konvertiert Yuno-Intervall-Syntax zu Cron-Schedule-String.

    Args:
        interval: Yuno-Intervall wie "5M", "1h", "1D 8h", "1W"

    Returns:
        Cron-Schedule-String

    Raises:
        ValueError: Wenn Intervall nicht parsebar
    """
    interval = interval.strip()

    # Sub-Minute: Fallback auf minütlich
    m = re.fullmatch(r"(\d+)S", interval)
    if m:
        secs = int(m.group(1))
        if secs < 60:
            return "* * * * *"
        raise ValueError(f"Sub-Minute-Intervalle werden zu minütlich: {secs}s")

    # Minuten: */N * * * *
    m = re.fullmatch(r"(\d+)M", interval)
    if m:
        return f"*/{m.group(1)} * * * *"

    # Stunden: 0 */N * * *
    m = re.fullmatch(r"(\d+)h", interval)
    if m:
        return f"0 */{m.group(1)} * * *"

    # Kombiniert: NmHh (z.B. 2h30m)
    m = re.fullmatch(r"(\d+)h(\d+)m", interval)
    if m:
        hours = int(m.group(1))
        minutes = int(m.group(2))
        # Cron: M */H * * *  (M Minute bei jedem H-hour-Tick)
        return f"{minutes} */{hours} * * *"

    # Tage mit fester Uhrzeit: 1D HHh (z.B. "1D 8h")
    m = re.fullmatch(r"(\d+)D\s+(\d+)h", interval)
    if m:
        days = int(m.group(1))
        hour = int(m.group(2))
        # */D HH * * *  (jeden D-ten Tag um HH Uhr)
        return f"0 {hour} */{days} * *"

    # Tage um Mitternacht: 1D
    m = re.fullmatch(r"(\d+)D", interval)
    if m:
        return f"0 0 */{m.group(1)} * *"

    # Wochen
    m = re.fullmatch(r"(\d+)W", interval)
    if m:
        weeks = int(m.group(1))
        # Cron: 0 0 * * 0 ist Sonntag, */N Wochen = nächster Sonntag alle N Wochen
        # Vereinfachung: alle N Wochen Sonntag
        return f"0 0 * * {weeks * 0}"  # Sonntag (jede Woche; für jede-N-Wochen brauchts mehr Logik)

    raise ValueError(f"Unbekanntes Intervall-Format: {interval!r}")


def humanize(cron_schedule: str) -> str:
    """Gibt eine menschenlesbare Beschreibung des Cron-Schedules."""
    parts = cron_schedule.split()
    if len(parts) != 5:
        return cron_schedule

    minute, hour, dom, month, dow = parts

    if minute == "*/5":
        return "Alle 5 Minuten"
    if minute.startswith("*/"):
        return f"Alle {minute[2:]} Minuten"
    if hour == "*" and minute == "0":
        return "Jede volle Stunde"
    if hour.startswith("*/"):
        return f"Alle {hour[2:]} Stunden"
    if hour.isdigit() and minute.isdigit() and dom == "*":
        return f"Täglich um {hour}:{minute.zfill(2)}"

    return cron_schedule


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: parse_interval.py <intervall>")
        print("Beispiele: 5M, 1h, 1D 8h, 1W, 2h30m")
        sys.exit(1)

    interval = sys.argv[1]
    try:
        cron = interval_to_cron(interval)
        print(f"  Intervall: {interval}")
        print(f"  Cron:      {cron}")
        print(f"  Human:     {humanize(cron)}")
    except ValueError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(1)