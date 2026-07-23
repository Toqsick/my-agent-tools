# Phase 3 — Exclusive-Pfade Commands

```bash
# Nur in Klon A
cd /pfad/zu/klonA
for f in $(git ls-files); do
  [ ! -f "/pfad/zu/klonB/$f" ] && echo "$f"
done | sort > /tmp/only-in-a.txt

# Nur in Klon B
cd /pfad/zu/klonB
for f in $(git ls-files); do
  [ ! -f "/pfad/zu/klonA/$f" ] && echo "$f"
done | sort > /tmp/only-in-b.txt

wc -l /tmp/only-in-a.txt /tmp/only-in-b.txt
```

**Gruppierung:**
- **Dokumentation** (`docs/`, `README.md`)
- **Exklusive Module** (Commit-Check: in welchem Branch entwickelt?)
- **Build-Artefakte** (fälschlich committed?)
- **CI/Agent-Konfiguration** (Branch-spezifisch)