# Computer-System-Analyse (Cross-System-Vergleich)

Für eine vollständige, systemübergreifende Analyse ALLER Computer in der DB (Player + Router + Server) verwende das **9-Phasen-Modell** mit iterativen Python-Scripts:

- **Phase 0–1:** Schema Discovery + Population Scan (Tabellen, Row-Counts)
- **Phase 2:** Identity Verification — sind Router/Server Klone oder individuell? (5 JSON-Spalten, MD5-Hash-Check)
- **Phase 3:** Hardware-Klassenanalyse — Arm-CPU (Router, 0.25GHz) vs Generic (Server, 1.5-2.3GHz / Player, 1.0GHz), RAM-, HDD- und MB-Vergleich
- **Phase 4:** ConfigOS Deep Dive — Player (Mail/Bank/Ports) vs Router (WiFi/Forwarding) vs Server (Personas + account.db)
- **Phase 5:** NPC-Persona-Extraktion — Alle 23+ NPCs mit Alter/Gender/Intelligence/Mail/JobRole, Duplikat-Erkennung via `npc['ID']` über Host-Grenzen hinweg
- **Phase 6:** FileSystem-Baum-Analyse — Spanische Field-Names (`nombre`/`size`/`type`/`owner`/`permisos`), rekursiver Walker, Aggregate (dirs/files/total_size/max_depth)
- **Phase 7:** Prozess-Analyse — Leere Arrays bei GameOver=1, Player-Session hat kernel_task+Xorg (~32MB / 128MB)
- **Phase 8:** Player-Trace-Felder — PassiveTraces, TokenTrace (single UUID, NOT array!), TLCooldown (ISO-string), BankTraces, GuiLaunchCooldown (wall-clock)
- **Phase 9:** Report-Erstellung — 16-Sektionen-Markdown-Template mit Cross-Reference-Matrix

**Vollständige Methodik mit Python-Code, SQL-Queries, spanischer Field-Name-Tabelle und Pitfalls:** `references/greyhack-db-systems-analysis.md`.