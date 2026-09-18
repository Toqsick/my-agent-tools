---
name: azahar-harness
version: 0.1.0
author: Basti
license: MIT
description: "Use when 3DS-Homebrew im Azahar-Emulator (Citra-Fork) verifiziert werden soll („boot-test im Emulator“, „Azahar-Smoke-Test“, „emulator evidence“, „Save-Check“) — headless-Boot, Boot-Klassifikation, Save-CRC-Beweis, RPC-Zustandsleser. NOT for allgemeines GUI-Testing (computer-use), Build-Aufgaben ohne Emulator (linux-system) oder CI-Integration von Emulator-Runs (bewusst lokal, siehe Skill)."
metadata:
  hermes:
    tags: [azahar, citra, 3ds, homebrew, emulator, verification, testing]
    related_skills: [dev-loop, linux-system, desktop-window-reconnaissance]
---

# azahar-harness — Azahar als Verifikations-Orakel

Azahar (github.com/azahar-emu/azahar, C++/Qt6-Citra-Fork) bootet gebautes 3DS-Homebrew
(`.3dsx`/`.cia`) als **Beweis-Orakel**: nicht "sieht grün aus", sondern hart
klassifizierter Boot + neuer, gültiger Spielzustand. Goldstandard-Referenz ist
`pokerogue-3ds/tools/emu/` (boot.py, run.py, rpc.py, proc.py — Xvfb-basiert).

## Das Muster (5 Säulen)

1. **Headless-Boot unter Xvfb**: Azahar-Qt-Frontend mit ROM-Pfad als Positionsargument
   unter `Xvfb`/offscreen starten — kein Mensch, kein Fenster nötig.
2. **Boot-Klassifikation statt Log-Glauben**: `boot-ok | boot-warm | boot-error-screen |
   boot-timeout` — klassifiziert aus bewährten Signalen, nie aus "Prozess lebt".
3. **Save-File-CRC als primäres Beweissignal**: der stärkste Beweis ist ein **neu
   entstandener Save-File mit gültiger CRC** (pokerogue: 332 B, md5-geprüft) — nicht
   Pixel, nicht Log-Zeilen. Saves sind die ehrlichste Auskunft eines Spiels.
4. **RPC-Zustandsleser aus dem unmodifizierten Binary**: live game state (z. B.
   `g_run` an fester Adresse) über einen RPC-Weg lesen, den das **ausgelieferte**
   Binary bereitstellt. **Kein-Hook-Regel:** niemals Test-Hooks in den Spielcode
   bauen („kein Hook im Spielcode — das gemessene .3dsx ist das ausgelieferte";
   pokerogue hat seinen geplanten `POKEROGUE_3DS_TESTHOOK` aus gutem Grund verworfen).
5. **Lokal, nicht CI**: Emulator-Evidenz ist ein Session-Schritt / Gate-Checklisten-
   Punkt mit Screenshots/Reports in `docs/evidence/`. Vier Gründe (pokerogue-Kanon):
   Sysfont aus dem eigenen NAND-Dump (konsolen-individuell), llvmpipe-Timing auf
   Runnern, Runner-/Flatpak-Kosten, private Actions-Minuten. Was sehr wohl in CI
   gehört: reine Python-Decoder/Checks derselben Beweise (Save-Decode-Fixtures etc.).

## Ablauf eines Orakel-Laufs

1. Build bereitstellen (`.3dsx` frisch gebaut; Build-Konfig → references/azahar-facts.md)
2. Xvfb-Display aufspannen; Azahar mit ROM-Argument starten; Proc-Handling sauber
   kapseln (Prozess-Gruppe, NICHT auf SIGTERM vertrauen — siehe Gotchas)
3. Boot klassifizieren; bei `boot-ok`: auf Save-Entstehung warten, CRC/md5 prüfen
4. Falls Zustandsbeweis nötig: RPC lesen, Werte gegen Erwartung stellen
5. Evidenz nach `docs/evidence/` (Report + Hashes) und in die Gate-Checkliste verlinken

## Gotchas (hart erkauft, bitte nicht wiedererleben)

→ Details + Build-Rezept + CLI-Referenz: `references/azahar-facts.md`

- Azahar **verschluckt SIGTERM** — Beenden über Xvfb-Display-Abriss/Prozessgruppe
- `pgrep -f azahar` ist wertlos (matcht die eigene cmdline) — PID sauber führen
- Azahar beantwortet RPC **vor `main()`** — `wave_==0` ist ein Null-Muster, kein Beweis
- NVIDIA-modeset-Hang auf manchen Hosts → LD_PRELOAD-Shim + Mesa-Software-GL
  (Workaround aus pokerogue docs/evidence übernehmen)
- Touch-Eingabe ist unter Xvfb wirkungslos — Emulator prüft das **Zeichnen**, nicht
  das Antippen; Geometrie host-testbar machen (Bruchstellen-Muster 6 in
  plan-dev-loop)

## Einbettung in den dev-loop

- IMPL-Phase: Orakel-Lauf als Akzeptanzkriterium formulieren („Boot boot-ok + neuer
  Save mit CRC X"), nur wenn das Repo schon ein emu-Harness hat — sonst erst
  eines nach diesem Muster anlegen (Aufwand einkalkulieren, eigener Task)
- Milestone-Gates (G-A-Stil): zwei Kaltstarts sauber, Determinismus-Brücke gegen
  Host-Vektoren (z. B. run_state-Vergleich), je Beweis ein Mutationsbeleg
  („ein Loop auf einem Verify, der lügen kann, multipliziert die Lüge")

## Es läuft gut, wenn

- Jeder Orakel-Beweis aus Save-CRC/RPC-Werten besteht, nicht aus Screenshots allein
- Das gemessene Binary byte-identisch mit dem ausgelieferten ist (kein Hook!)
- Evidenz-Dateien existieren, bevor das Gate sie zitiert
