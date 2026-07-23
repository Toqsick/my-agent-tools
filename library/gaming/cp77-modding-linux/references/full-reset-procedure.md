# Full Reset (Vanilla Restore)

**Wann nötig:**
- RT-Toggles bleiben ausgegraut trotz korrektem Proton-Wechsel (VKD3D-Proton-Update) + UserSettings-Edit → Reset beweist ob Mods oder nackter Treiber/Proton das Problem ist
- Mod-Framework soll komplett weg für Bug-Hunting oder Neuanfang
- REDlauncher-Bypass hinterlässt inkonsistenten Wine-Prefix-Zustand (DLC-Authorization-Probleme)
- Game-Root durch Modloader auf >85 GB aufgebläht

**Kern-Erkenntnis aus der Praxis:** Ein Full Reset der CP77-Modding-Komponenten (REDlauncher + RED4ext + CET + XL-Plugins + UserSettings.json) alleine **heilt keine RT-Toggles** — wenn VKD3D-Proton die GPU nicht kennt, bringt auch der sauberste Zustand nichts. Reset ist aber der **ultimative Differenzial-Diagnose-Schritt**: wenn RT auch nach Reset grau bleibt, ist das Problem **garantiert nicht mod-bedingt**.

## Vorgehen (6 Phasen):

1. **Backup** → Saves (bleiben erhalten, trotzdem sichern), Modloader, REDlauncher, UserSettings.json
2. **Modloader entfernen** → `red4ext/`, CET (.asi + Daten), REDlauncher-MSI
3. **REDlauncher aus Wine-Prefix löschen** → 870 MB `Programs/CD Projekt Red/REDlauncher/`
4. **Mod-Verzeichnisse leeren** → `archive/pc/mod/`, `archive/pc/ep1/mod/`
5. **UserSettings.json löschen** → CP77 generiert sie beim Start neu mit korrekter Capability-Detection
6. **Verifikation** → Smoke-Check (kein red4ext/, leere plugins/, leere mod/)

**Danach:** Steam Repair laufen lassen (10-30 min) + Game starten → REDlauncher wird frisch installiert.

**Nach Reset:** Game-Root schrumpft von ~92 GB auf ~66 GB, Disk-Space gewinnt ~23 GB zurück.

**Wiederherstellung möglich** via Backup — alle Original-Dateien bleiben erhalten.