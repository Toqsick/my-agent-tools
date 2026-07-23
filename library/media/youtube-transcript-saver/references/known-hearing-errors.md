# Bekannte Auto-Caption-Hörfehler (Such-Matrix)

Erweitert aus der Heuristik-Liste (5c) für die Post-Merger-Verifikation.
Jeder Eintrag enthält: Regex-Suchmuster, Ersetzung, und ob es ein Compound-Word-Variant-Risiko gibt.

## Regex-Such-Matrix für Post-Merger-Check

```python
# Kopierfertig: nach dem Stufe-3-Merge laufen lassen
import re

POST_MERGE_PATTERNS = [
    # === Claude Code / Anthropic-Familie (häufigste Fehler) ===
    (r"Cloud Code",              "Claude Code",         "Compound: CloudC|Clouds|Cloud's auch checken"),
    (r"\bClord\b",               "Claude",              "Seltene Verhunzung: ASR rastet auf 'Clord' ein statt 'Claude' (Session k2p6WprtzFI, gefunden im Post-Merge-Check)"),
    (r"Cloudcode",               "Claude Code",         "Ein-Wort-Variante, ASR klebt zusammen"),
    (r"Cloudnutzung",            "Claude-Nutzung",      "Hörfehler: ASR hört 'Cloud-Nutzung' statt 'Claude-Nutzung'"),
    (r"Cloudspeicher",           "Cloudspeicher",       "⚠ AMBIGUOUS — prüfen ob Claude Subscription (→ Claude-Kontingent) oder Cloud-Storage (→ korrekt). Im Kontext von Kontingent/Token-Verbrauch → Claude-Kontingent."),
    (r"\bClot\b",                "Claude",              "Einzelwort, selten"),
    (r"\bClud\b(?![\\w])",       "Claude",              "Ohne o-Laut, truncation"),
    (r"\bClod\s+Chat\b",        "Claude Chat",         "'Clod' statt 'Claude' — ganzer Name verhunzt"),
    (r"\bClaud\b(?!(?:\s+Code|\s+Cowork|ian\b))", "Claude", "Eigenständiges 'Claud' ohne 'e'-Ende"),
    (r"\bCloud\b(?![\\s-])(?=.*(?:Code|MD|Instanz))", "Claude", "Nur wenn Cloud im Tech-Kontext"),

    # === CLAUDE.md (viele Varianten durch Hörfehler) ===
    (r"Cloud MDatei",            "CLAUDE.md",           "Häufigste Fehlform"),
    (r"Cloud MD Datei",          "CLAUDE.md",           "Space-Variante: 'Cloud MD Datei' → 'CLAUDE.md' (ASR setzt Space zwischen MD und Datei)"),
    (r"Cloud MDien",             "CLAUDE-Dateien",      "Plural"),
    (r"Cloud MDI",               "CLAUDE.md",           "Einzahl-Variante"),
    (r"Cloud MDEI",              "CLAUDE.md",           "Auto-Caption-Verhunzung"),
    (r"Cloud im DDatei",         "CLAUDE.md",           "ASR-Dehnungsvariante: Cloud + 'im' + DDatei"),
    (r"Cloud im DD Datei",       "CLAUDE.md",           "Space-Variante von Cloud im DDatei"),
    (r"Cloud MDD(ei)?",         "CLAUDE.md",           "Doppel-D-Variante"),
    (r"Cloudmdatei",             "CLAUDE.md",           "Zusammenschreibung"),
    (r"Cloud im(L?)Dien",        "CLAUDE-Dateien",      "Regex-Fang"),
    (r"Cloud Instanz",           "Claude-Instanz",      "Gemeint ist die laufende Claude-Session"),
    (r"Cloud Batei",             "CLAUDE.md",           "Auto-Caption-Verhunzung"),
    # === CLAUDE.md — Standalone-Abkürzung (nicht nur als Dateiname) ===
    (r"Cloud MD (?:Management|Plugin|File|Datei|Manager)",  "CLAUDE.md",  "P0 — 'Cloud MD' als Standalone-Abkürzung für 'CLAUDE.md' (ASR verliert Punkt+Endung)"),

    # === Agent-Terminologie ===
    (r"Superagent(en)?",          r"Subagent\1",        "Plural erhalten"),
    (r"\bSupagent(en)?",          r"Subagent\1",        "Ohne 'er'-Silbe"),
    (r"SuperAgent",              "Subagent",            "CamelCase"),
    (r"Hauptgagent",             "Hauptagent",          "Doppel-g durch Hörfehler"),
    (r"Hauptgagenten",           "Hauptagenten",        "Plural mit Doppel-g"),

    # === Company Names ===
    (r"Anthopic",                "Anthropic",           "Fehlendes 'r'"),
    (r"\bAntiravity\b",          "Antigravity",         "Coding-Agent-Plattform"),
    (r"\bAntigravity\b",         "Antigravity",         "Bereits korrekt — nicht patchen"),

    # === Model Names ===
    (r"\bHighq\b",               "Haiku",               "Klein geschrieben"),
    (r"\bHighQ\b",               "Haiku",               "CamelCase"),
    (r"\bSon\b(?!net\b)",        "Sonnet",              "Einzelstehendes 'Son' (nicht 'Sonnet')"),
    (r"Sonell",                  "Sonnet",              "Auto-Caption-Verhunzung"),

    # === Tool Names ===
    (r"Quen Code",               "Qwen Code",           "Alibaba Coding-Agent"),
    (r"Excalid Draw",            "Excalidraw",          "Mit Space"),
    (r"Excaly Draw",             "Excalidraw",          "Auto-Caption-Verhunzung"),
    (r"Excalyra",                "Excalidraw",          "ASR-Endsilben-Kollaps: Excalidraw → Excalyra"),
    (r"Excalidraw",              "Excalidraw",          "Bereits korrekt"),
    (r"\bExcalid\s+Drop\b",      "Excalidraw Plugin",   "'Drop' statt 'Draw' — mit Plugin-Kontext"),
    (r"\bExcalidrawrop\b",       "Excalidraw",          "Zusammengezogen: Excalidraw + Drop-Aussprache"),
    (r"\bExcaly\s+Drawrop\b",    "Excalidraw",          "Doppelte Verhunzung: Excaly + Drawrop erst zu einem Wort"),

    # === Slash-Commands (Claude Code / Codex / OpenClaw) ===
    # Hörfehler-Pattern: meist "SL" + verhunzte Buchstaben, oder "Slash" als Ein-Wort
    (r"@AGs",                    "/AGs",                "Bei-Token statt Slash"),
    (r"SLCCtext",                "/compact",            "Buchstaben-vertauscht"),
    (r"SLCClear",                "/clear",              "Buchstaben-vertauscht"),
    (r"SLCRessume",              "/resume",             "Buchstaben-vertauscht"),
    (r"SLclear",                 "/clear",              "Auto-Caption-Variante: SL + clear (kürzer als SLCClear)"),
    (r"SLGal",                   "/goal",               "P0 — SL + Gal (falsche Silbentrennung); Julian Remote-Control-Video (pvhphecd70Y)"),
    (r"SlashLOP",                "/loop",               "P0 — Slash + LOP (Endsilben-Verschiebung)"),
    (r"SlashLop",                "/loop",               "P1 — Lowercase-Variante von SlashLOP"),
    (r"Slashloop",               "/loop",               "P0 — Slashloop als Ein-Wort-Verhunzung (Julian)"),
    (r"Slashgal",                "/loop",               "P1 — Slash + gal (vermutlich /loop oder /goal — Kontext pruefen, Julian)"),
    (r"Slashgoal",               "/goal",               "P1 — Slashgoal als Ein-Wort"),
    (r"Slash Goal",              "/goal",               "P0 — mit Space statt Bindestrich (Julian, pvhphecd70Y)"),
    (r"Slash Loop",              "/loop",               "P0 — mit Space statt Bindestrich (Julian, pvhphecd70Y)"),
    (r"slash goal",              "/goal",               "Lowercase-Variante"),
    (r"slash loop",              "/loop",               "Lowercase-Variante"),
    (r"slash compact",           "/compact",            "Lowercase-Variante"),
    (r"Slashgoal Feature",       "/goal-Feature",       "Slashgoal als Compound mit 'Feature' dahinter"),
    # Session 2026-07-09 (Remote-Control pvhphecd70Y Stufe-3 Run, Worker 3 Faktencheck-Findings)
    # Auto-Caption hat sich vertan — 'SLRemote' statt '/remote Control' (Slash-Command)
    (r"\bSLRemote\b",            "/remote Control",     "P1 — 'SLRemote Control' statt '/remote Control' (Worker 3, Session 2026-07-09)"),
    # 'slem Control' ist eine Variante von 'Remote Control'/'/remote Control' (phonetisch kollabiert)
    (r"\bslem Control\b",        "/remote Control",     "P1 — 'slem Control' statt 'Remote Control'/'/remote Control' (Worker 3, Session 2026-07-09)"),
    # 'SlashG' (ohne 'oal') statt '/goal' — Endsilben-Kollaps
    (r"\bSlashG\b",              "/goal",               "P1 — 'SlashG' statt '/goal' (Endsilben-Kollaps; Worker 3, Session 2026-07-09)"),
    # 'Slash Clear' (ausgeschriebene Form) statt '/clear'
    (r"\bSlash Clear\b",         "/clear",              "P2 — 'Slash Clear' ausgeschrieben statt '/clear' (Worker 3, Session 2026-07-09, Julian pvhphecd70Y)"),
    # 'Rustinger' statt 'Hostinger' — Endsilben-Vertauschung
    (r"\bRustinger\b",           "Hostinger",           "P1 — 'Rustinger' statt 'Hostinger' (Endsilben-Vertauschung; Worker 3, Session 2026-07-09)"),
    # 'Hey Claud'/'Hey Clud'/'Clode'/'Clot'/'Cludier'/'closed starten' — Claude-Verhunzungen (NICHT standalone Cloud)
    (r"\bHey Claud\b",           "Hey Claude",          "P0 — Eigenname-Anrede verhunzt: 'Hey Claud' statt 'Hey Claude' (Worker 3, Session 2026-07-09)"),
    (r"\bHey Clud\b",            "Hey Claude",          "P0 — Eigenname-Anrede verhunzt: 'Hey Clud' statt 'Hey Claude'"),
    (r"\bClode\b",               "Claude",              "P0 — 'Clode' statt 'Claude' (Eigenname verhunzt)"),
    (r"\bCludier\b",             "Claude",              "P1 — 'Cludier' statt 'Claude' (Worker 3, Session 2026-07-09)"),
    (r"\bClot(?!\w)",            "Claude",              "P0 — 'Clot' als Eigenname statt 'Claude' (nicht 'Blood clot' — auf Tech-Kontext pruefen)"),
    (r"\bclosed starten\b",      "claude starten",      "P0 — 'closed starten' statt 'claude starten' (Kommandozeile; Worker 3, Session 2026-07-09)"),
    # Sprachliche Hoerfehler (Worker 1 Inhalt-Fixes uebernommen)
    (r"\bAnmoldeformular\b",     "Anmeldeformular",     "P1 — 'Anmolde-' statt 'Anmelde-' (Formular-Fehler; Worker 1, Session 2026-07-09)"),
    (r"\bzüllen\b",              "füllen",              "P1 — 'züllen' statt 'füllen' (Worker 1, Session 2026-07-09)"),
    (r"\berknüpfen\b",           "verknüpfen",          "P1 — 'erknüpfen' statt 'verknüpfen' (ver-Prefix fehlt; Worker 1, Session 2026-07-09)"),
    (r"\bdebugen\b",             "debuggen",            "P1 — 'debugen' statt 'debuggen' (korrekte Schreibweise mit -gg-; Worker 1, Session 2026-07-09)"),
    (r"\bImpressummatte\b",      "Impressumsmaske",     "P1 — 'Impressummatte' statt 'Impressumsmaske' (Worker 3, Session 2026-07-09)"),

    # === CLI-Tools / Linux-Befehle (Hörfehler bei Tech-Tutorials) ===
    # tmux ist der häufigste Kandidat in Server-/Workflow-Videos
    (r"\bTmax\b",                "tmux",                "P0 — Terminal-Multiplexer: 'Tmax' statt 'tmux' (9x im Julian Remote-Control-Video pvhphecd70Y)"),
    (r"\bTMAX\b",                "tmux",                "P0 — tmux in Grossbuchstaben (Befehlslisten-Erkennung)"),
    (r"\btm UCKS?\b",            "tmux",                "P1 — 'tm UX' / 'tm UCKS' mit Space"),
    (r"\bteamux\b",              "tmux",                "P2 — 'teamux' statt 'tmux' (seltene Variante)"),

    # === Format / Syntax ===
    (r"Yammel",                  "YAML",                "Frontmatter-Header"),
    (r"Yammel Front Met",        "YAML Frontmatter",    "Vollständige Verhunzung"),
    (r"Kontext Rod",             "Context Rot",         "Deutsch-Englisch-Mix"),
    (r"Areal ",                  "Arial ",              "Schriftart mit Space"),

    # === Englisch bent → korrekt ===
    (r"Thorally",                "Thoroughly",          "Englisch: gruendlich"),
    (r"Thoraly",                 "Thoroughly",          "Kurzform"),

    # === MCP (Compound-Word-Risiko) ===
    (r"MCPS(?:\s|-)?Server",     "MCP-Server",          "Compound: MCPS + Server"),
    (r"\bMCPS\b(?![\\s-]?S)",     "MCP",                 "Standalone MCPS"),
    (r"MCP Server",              "MCP-Server",          "Fehlender Bindestrich"),

    # === OpenClaw-Familie (Tool-Name, häufig bis zu "Claw" amputiert) ===
    # Längste/vollständigere Patterns zuerst — Reihenfolge wichtig!
    (r"OpenClaufgaben",          "OpenClaw Aufgaben",   "Zwei Wörter zusammengeklebt"),
    (r"\bOpen Claw\b",           "OpenClaw",            "Mit Space getrennt — vor kürzeren ausführen"),
    (r"\bOpen Cla\b",            "OpenClaw",            "Mit Space + amputiert — vor OpenCla ohne Space ausführen"),
    (r"OpenClore",               "OpenClaw",            "Falscher Tool-Loader-Name"),
    (r"OpenCla(?![uw])",         "OpenClaw",            "Fehlendes w am Ende — häufigster Fehler (ohne Space)"),
    (r"\bOpenCl\b(?!aw)",        "OpenClaw",            "Komplett ohne Endung, Wortabbruch"),
    (r"\bChore\b",               "Claw",                "Phonetischer Hörfehler, isoliert"),
    (r"\bclar\b(?!.*[ei])",      "Claw",                "Phonetisch ähnlich, aus Kontext prüfen"),
    (r"\bclau\b",                "Claw",                "Autocaption-Bruchstück, auf Tool-Kontext prüfen"),
    (r"\bclaw\b",                "Claw",                "Lowercase Tool-Name — großschreiben, nur wenn Kontext = Tool"),

    # === Claude Modell-Namen-Varianten (Opus / Sonnet) ===
    (r"Cloud Opos 4\.6",         "Claude Opus 4.6",     "Hörfehler: Opos → Opus"),
    (r"Cloud Opus 4\.6",         "Claude Opus 4.6",     "Fehlender Claude-Präfix"),
    (r"Cloudsonet 4\.5",         "Claude Sonnet 4.5",   "Zusammengezogen: Cloud+Sonnet"),
    (r"Cloud Sonnet 4\.5",       "Claude Sonnet 4.5",   "Zwei Woerter mit Space — nicht Cloudsonet"),
    (r"Spiel Cloud Opus",        "Claude Opus",         "Wort 'Spiel' ist Auto-Caption-Artefakt (aus 'Spannend:' o. 'Beispiel:')"),
    (r"Claud Code",              "Claude Code",         "Fehlendes e, häufiger Hörfehler"),

    # === Claude-Code-Skills-&-Plugins-Ökosystem (Session 2026-07-04, "Top 10 Claude Code Skills & Plugins", 42:48) ===
    # Alle hier stammen aus einem systematischen Description-vs.-Transkript-Check eines 10-Item-Rankings
    (r"Feature Death(?:\\s+Plugin)?",     "Feature Dev Plugin",  "P0 — Anthropic Feature Dev Plugin, 'Death' statt 'Dev' (ASR-Endsilben-Kollaps)"),
    (r"Feature Def(?:\\s+Plugin)?",       "Feature Dev Plugin",  "P0 — Kürzere Variante: ASR rastet auf 'Def' ein bevor 'Death' auftritt"),
    (r"\\bCol Medin\\b",                 "Cole Medin",          "P1 — YouTuber-Name, 'Col' statt 'Cole' (fehlendes e)"),
    (r"\\bColedien\\b",                  "Cole Medin",          "P1 — YouTuber-Name, komplett verhunzt"),
    (r"Superpers(?:\s+Plugin)?",        "Superpowers",         "P0 — Plugin-Name, fehlendes 's' am Ende (Power→Powers)"),
    (r"Superpow(?!ers)",                 "Superpowers",         "P0 — Plugin-Name, amputiert"),
    (r"\bSlag\b",                        "Slack",               "P2 — Chat-Tool, deutscher ASR-Hörfehler (Slag→Slack)"),
    (r"\\bFirecll\\b",                   "Firecrawl",           "P0 — Tool-Name, 'cll' statt 'crawl' (Wortende amputiert)"),
    (r"\\bFirecroll\\b",                 "Firecrawl",           "P0 — Tool-Name, 'croll' statt 'crawl' (Vokal-Verschiebung)"),
    (r"\\bPlayright\\b",                 "Playwright",          "P0 — Tool-Name, 'right' statt 'wright' (Wortende ersetzt)"),
    (r"\\bPlayr\\b",                     "Playwright",          "P0 — Tool-Name, stark amputiert (Playwright→Playr)"),
    (r"die Playr",                       "Playwright",          "P0 — 'die Playr' → 'Playwright' (mit Artikel)"),
    (r"\bNotebook LM\b",                  "NotebookLM",           "P0 — Tool-Name, Space im Namen entfernen (häufigster Fall: 23x in Session 2026-07-04-b)"),
    (r"Notebook LM Pi",                  "NotebookLM-py",       "P1 — Package-Name, 'Pi' statt '-py' (phonetisch ähnlich)"),
    (r"\\bContext 7\\b",                 "Context7",            "P2 — Offiziell ohne Space, im Transkript oft mit Space"),
    (r"\\bVoll\\b(?=.*[Vv]ault)",        "Vault",               "P2 — Obsidian-Vault, 'Voll' statt 'Vault' (deutsche Aussprache)"),
    (r"RA\\s+Systeme",                   "RAG-Systeme",         "P2 — Fachbegriff, fehlendes 'G' (Retrieval-Augmented Gen.)"),
    (r"\\bGitup\\s+Repository\\b",       "GitHub Repository",   "P2 — 'Gitup' statt 'GitHub' (ASR stumpft Endsilbe ab)"),

    # === Kimi / Moonshot ===
    (r"Kimy K2\.5",              "Kimi K2.5",           "Moonshot-Modellname mit y statt i"),
    (r"Kimi Car 2\.5",           "Kimi K2.5",           "Hörfehler 'Car' statt 'K' (K2.5)"),
    (r"\bKimy\b",                "Kimi",                "Einzelstehend"),
    (r"\bMoonshot\b",            "Moonshot",            "Korrekt, Company-Name — nicht patchen"),

    # === YouTube-Kompetitoranalyse ===
    (r"Outlayer",                "Outlier",             "Statistischer Fachbegriff verhunzt"),
    (r"Kanäl",                   "Kanäle",              "Umlaut-Fehler"),

    # === Hosting / Server ===
    (r"Routro",                  "Router",              "OpenRouter-API, Auto-Caption-Verhunzung"),
    (r"\bVPS\b",                 "VPS",                 "Wird in Description getaggt, aber im Transkript fehlt das Wort — als Hostinger/Server umschrieben"),
    (r"lavable",                 "Lovable",             "AI-App-Builder Lovable"),
    (r"Gitter\s+Repository",    "GitHub-Repository",   "'Gitter' statt 'GitHub' (GitLab/Matrix-Verwechslung)"),
    (r"Claudian\s+Gitub",       "Claudian GitHub",     "'Gitub' statt 'GitHub' — beide Begriffe in einem Hörfehler"),
    (r"\bGitub\b",               "GitHub",              "Fehlendes 'h' in 'Github'"),

    # === Zustand / Health ===
    (r"Heardbeat",               "Heartbeat",           "OpenClaw-Feature, hörbare statt stille Pause"),

    # === Tools / UI ===
    (r"kannban",                 "Kanban",              "Board-UI-Komponente"),
    (r"Kanboard",                "Kanban-Board",        "Zusammenschreibung, wahrscheinlich 'Kanban Board'"),
    (r"Backlock",                "Backlog",             "Projektmanagement-Begriff verhunzt (Backlog, nicht Backlock)"),
    (r"Yammel Editor",           "YAML-Editor",         "Editor für docker-compose / Konfig"),
    (r"Googleienste",            "Google-Dienste",      "Auto-Caption-Verhunzung (Google + Dienste)"),
    (r"Cloudienste",             "Google-Dienste",      "Alternativ-Verhunzung"),
    (r"\bProan\b",               "Pro-Plan",            "Auto-Caption amputiert 'Pl' bei Pro-Plan"),

    # === Obsidian / Wissensmanagement (Hive Mind — Obsidian+Claude-Setup) ===
    (r"\\bObsidien\\b",            "Obsidian",             "P0 — Tool-Name, 'ie' statt 'ia' (häufiger ASR-Fehler: Obsidien→Obsidian)"),
    (r"\\bKontextordr\\b",         "Kontextordner",        "P2 — Deutscher Ordner-Name, amputiertes 'ne' (Kontextordner → Kontextordr)"),
    (r"\\bKontextordrer\\b",       "Kontextordner",        "P2 — Mit falschem Suffix (Kontextordner → Kontextordrer)"),
    (r"Mark Dateien",             "Markdown-Dateien",     "P0 — Fachbegriff, 'Mark' statt 'Markdown' (ASR amputiert '-down')"),
    (r"Markon Datei",             "Markdown-Datei",       "P0 — 'Markon' statt 'Markdown' (phonetische Nähe)"),
    (r"Markn Dateien",            "Markdown-Dateien",     "P0 — 'Markn' statt 'Markdown' (stark amputiert)"),
    (r"\\bBrain Dump\\b",          "Brain-Dump",           "P2 — Deutsch-Englisch-Kompositum, fehlender Bindestrich"),
    (r"\\bBrain Dump Datei\\b",    "Brain-Dump-Datei",     "P2 — Dreifach-Kompositum, fehlende Bindestriche"),
    (r"\\bGrafansicht\\b",         "Graph View",           "P2 — Deutscher Phonem-Hörfehler (optionale Korrektur — beide Versionen akzeptabel)"),
    (r"\\bGrafen\\b",              "Graphen",              "P2 — Falscher Vokal im Plural (Graph + en = Graphen)"),

    # === Chat / AI-Service ===
    (r"Chat GBT",                "ChatGPT",             "OpenAI — klassischer Hörfehler"),
    (r"\bChatGT\b",              "ChatGPT",             "Ohne 'B' — ASR amputiert das B"),
    (r"\bJGPT\b",                "ChatGPT",             "Auto-Caption tauscht 'Chat' → 'J'"),

    # === Rabattcode ===
    (r"Jurian Ivanov",           "JULIANIVANOV",        "Rabattcode für Hostinger — nicht der Name Jurian"),

    # === Zeit / News ===
    (r"Tagessow",                "Tagesthemen",         "Nachrichten-Sendung"),

    # === Sprach-Artefakte ===
    (r"Not 1 Schritt",           "jeden einzelnen Schritt", "Hörfehler: 'Not 1' → 'jeden'"),
    (r"Note 1",                  "jeden",               "Im N8N-Kontext: 'not 1' → 'jeden'"),
    (r"Node 1 Schritt",          "jeden Schritt",       "Drei-Ebenen-Distortion: Node→Not→Note→jeden. Der Merger muss alle drei Varianten abdecken."),
    (r"mussen müssen",           "müssen",              "ASR-Doppelfehler: Sprecher-Stotter + Caption-Merge"),
    (r"ische Systeme",           "agentische Systeme",  "ASR verschluckt 'agent-' bei 'agentische Systeme'"),
    (r"\[räuspern\]",            "",                    "Cleanup-Token, komplett entfernen"),
    (r"\bTrujah\b",              "Tool",                "Unklarer Tool-Name — in Session 2026-07-04 (5 OpenClaw Usecases) vom Merger korrekt als 'Tool' inferiert. Nur patchen wenn Kontext 'Tool' semantisch passt (z. B. 'dass das Tool viel zu teuer sei'). Gegen Original-Ton prüfen falls Zweifel."),

    # === Falsch-positive vermeiden ===
    # OpenClaw ist EIGENNAME (Tool)! Nicht nach 'OpenClaw' suchen — es ist korrekt; nur 'OpenCla'/'OpenCl' ist fehlerhaft.
    # n8n ist korrekter Tool-Name — nicht patchen.
    # Make.com ist korrekt — nicht patchen.
    # Kimi K2.5 ist korrekt nach Fix — nicht erneut patchen.
    # Hostinger ist korrekter Firmenname — nicht zu 'VPS' patchen; Description-Tag vs. Transkript-Diskrepanz separat melden.
    # Telegram im Transkript = OpenClaw-Slash-Befehl (/models), nicht Telegram-Messaging. Description-Tag ist irreführend — Faktencheck muss das flaggen.
    # "Vault-Struktur" ist KEIN Hörfehler. Es ist ein legitimes deutsches zusammengesetztes Nomen (Sprecher sagt selbst "dann ein Bereich über die Vault-Struktur"). grep findet "Vault-Struktur" wenn es nach "Vault" sucht — das ist ein False-Positive. Der Kontext zeigt, dass es korrekt ist.
    # "Style Settings" (Obsidian Plugin) ist korrekt — nicht patchen.
    # "Graph View" ist korrekt (oder optional "Grafansicht") — nicht patchen. Beide Versionen sind akzeptabel.
]

def post_merge_verification(text: str) -> list[dict]:
    """Prüft polierten Text auf Restfehler. Gibt Liste der Funde zurueck."""
    findings = []
    for pattern, replacement, note in POST_MERGE_PATTERNS:
        matches = list(re.finditer(pattern, text))
        if matches:
            findings.append({
                "pattern": pattern,
                "replacement": replacement,
                "note": note,
                "count": len(matches),
                "samples": [m.group() for m in matches[:3]],
            })
    return findings

# Beispielaufruf:
# remaining = post_merge_verification(polished_text)
# for f in remaining:
#     print(f"  {f['count']}x '{f['pattern']}' -> '{f['replacement']}' (Rest)")

```

## Klassifikation nach Schweregrad

| Schwere | Beispiele | Aktion |
|---------|-----------|--------|
| **P0** (Inhalt falsch) | Cloud Code → Claude Code, Superagent → Subagent, Anthopic → Anthropic | MUSS gefixt werden |
| **P1** (Technisch falsch) | Highq → Haiku, Kontext Rod → Context Rot, MCPS Server → MCP-Server | Sollte gefixt werden |
| **P2** (Kosmetisch) | Areal → Arial, Yammel → YAML, Thorally → Thoroughly | Nice-to-have |
| **Kein Fehler** | OpenClaw, n8n, Make.com, Opus, ein und dieselbe | Nicht patchen |

## Compound-Word-Varianten (häufige Merger-Lücke)

Wenn der Muster-Ersatz `MCP` → `MCP` ist, wird `MCPS` nicht erwischt.
Varianten die separat gecheckt werden müssen:

| Stamm | Varianten | Fix |
|-------|-----------|-----|
| MCP | MCPS, MCPS-Server, MCPS Server, MCPServer, MCP Server | MCP(-Server) |
| Claude | Cloud, Clot, Clud, Clod, Clouds | Claude |
| CLAUDE.md | Cloud MDatei, Cloud MDEI, Cloudmdatei, Cloud Batei, Cloud MDI, Cloud MD Datei | CLAUDE.md |
| Subagent | Superagent, Supagent, SuperAgent, Super Agent | Subagent |
| Anthropic | Anthopic, An tropic, Anthropic | Anthropic |

## Session-Historie: Woher diese Patterns stammen

- **2026-03-02**: OpenClaw 10x stärker (Julian Ivanov) — erste Heuristik-Liste (~50 Korrekturen)
- **2026-03-15**: Claude Code 8 Best Practices (Julian Ivanov) — ~169 Korrekturen, erweiterte AI-Coding-Patterns, Stufe-3-Pipeline validiert
- **2026-07-04**: 5 OpenClaw Usecases (Julian Ivanov) — +22 neue Patterns: OpenClaw-Varianten (OpenCla/OpenClore/OpenCl), Claude-Opus/Sonnet-Modellnamen (Cloud Opos/Cloudsonet/Cloud Sonnet mit Space), Kimi K2.5 (Kimy/Kimi Car), Outlier/Outlayer, Heartbeat/Heardbeat, Lovable/lavalbe, Kanban/kannban, YAML/Yammel, Tagesthemen/Tagessow, ChatGPT/ChatGBT, Google-Dienste/Googleienste, JULIANIVANOV/Jurian Ivanov, Node 1 Schritt/Not 1 Schritt/Note 1, Tag/Transkript-Diskrepanzen (Telegram/VPS/Clawdbot/Moltbot)
- **2026-07-04-merge**: Zweiter Run (gleicher Tag) — Merger musste Input-Dateien aus Conversation-Memory rekonstruieren nach /tmp-Cleanup. Als Konsequenz: Merger-Pitfall für Recovery ergänzt (siehe SKILL.md → Merger-Pitfalls).
- **2026-07-04 (Hive Mind, NVUCQ-pzBn4, Obsidian+Claude Code: So baust du dein zweites Gehirn, 36:24)**: Erster Hive-Mind-Kanal-Run einer anderen Content-Creator-Nische (Obsidian+Claude-Setup, nicht Julian Ivanov). Neue Patterns: Excalidraw-Varianten (Excalid Drop/Excalidrawrop/Excaly Drawrop), JGPT→ChatGPT, Proan→Pro-Plan, Clud/Clod Chat/Claud als standalone Claude-Verhunzungen, Gitter Repository→GitHub-Repository, Claudian Gitub→Claudian GitHub, Gitub→GitHub. Bestätigte die Channel-Agnostik vieler Patterns — Claude-Verhunzungen treten unabhängig vom Youtuber auf. **Merger-Learnings (dieser Run)**: +10 Obsidian/Wissensmanagement-Muster (Obsidien→Obsidian, Kontextordr/Kontextordrer→Kontextordner, Mark Dateien/Markon/Markn→Markdown-Dateien, Brain-Dump-Komposita, Grafansicht→Graph View). ~105 Eigennamen-Fixes, 37/37 Minuten-Marker erhalten, 7.426 Wörter, 0 Restfehler nach Post-Merge-Verifikation. WT/VT/Vault-Hörfehler in 13 Stellen konsistent aufgelöst. Grafansicht (Deutsch-Phonem) als akzeptabel validiert — Faktencheck erlaubt beide Versionen.
- **2026-07-04-b (Top 10 Claude Code Skills & Plugins, Vx6QlEhyybQ, 42:48)**: Zweiter Julian-Ivanov-Lauf am selben Tag. Neue Patterns aus systematischem Description-vs.-Transkript-Check einer 10-Item-Liste: Feature Death→Feature Dev, Col Medin/Coledien→Cole Medin, Superpers/Superpow→Superpowers, Firecll/Firecroll→Firecrawl, Playright/Playr→Playwright, Notebook LM Pi→NotebookLM-py, Voll→Vault, RA Systeme→RAG-Systeme, Gitup Repository→GitHub Repository. **Wichtige Methodik-Erkenntnis**: Description-Zeitstempel sind nicht immer vollständig (nur 8 von 10 Kapiteln getimt, 2 mit „_(weitere)_" markiert). Tool-Attributionen (kepano→Obsidian, obra→Superpowers, Upstash→Context7) sind im Transkript akustisch NACHWEISBAR FEHLEND — die Description erwähnt sie, das Video aber nicht. Wichtig für den Merger: Keine inhaltlichen Widersprüche, nur ASR-Artefakte.
- **2026-07-09 (Remote Control, pvhphecd70Y, Julian Ivanov, 22:57, Stufe 0)**: Erster kurzer Stufe-0-Run (nur deterministisches Polishing, kein LLM). Wichtigste Erkenntnis: **Stufe 0 hat systematische Lücken bei CLI-Tools und Slash-Commands** — der deterministische Pre-Pass hat `Tmax→tmux` (9x), `SLGal→/goal`, `SlashLOP→/loop`, `Slashloop→/loop`, `Slash Goal→/goal`, `SLclear→/clear` NICHT initial gefangen. Erst die Post-Polish-Restfehler-Verifikation hat die Lücken aufgedeckt und musste manuell nachgepatcht werden. **Methodik-Lesson**: Stufe-0-Workflow MUSS eine Post-Verifikations-Runde enthalten, sonst landen Hörfehler im polierten File. **Neue Patterns**: tmux-Varianten (`Tmax`/`TMAX`/`tm UCKS`), Slash-Command-Varianten (`SLGal`/`SlashLOP`/`Slashloop`/`Slash Goal`/`Slash Loop`/`Slashgal`). Der `/compact`-Befehl kam im Video echt vor — Validierung dass er ein legitimer Claude-Code-Befehl ist.
- **2026-07-09 (Remote Control, pvhphecd70Y, Stufe 3, 4-Worker-Bienen-Muster via delegate_task)**: Nachpolier-Run des Stufe-0-Files. **Multi-Agent-Pipeline Fable→M3-Pattern angewandt**: 3 Worker-Bienen parallel (Inhalt/Stil/Faktencheck), Merger-Biene sequentiell. Wichtigste Erkenntnisse: (1) Worker 2 (Stil) hat einen **Compound-Adjective-Bug** eingeführt — "Cloud Code" wurde zu "Claudee Code" weil Worker 2 zu aggressiv ersetzt hat (84x Cloud→Claude + 39x Claud→Claude = 123 Claude-Ersetzungen, aber Worker hat eigenständig "Claudee" als Pattern erfunden das nicht existiert). Merger hat den Bug in der Post-Verifikation gefangen und eliminiert. (2) **Worker 3 (Faktencheck) hat 27 Findings geliefert die Worker 1+2 nicht kannten** — darunter NEUE Patterns: `SLRemote→/remote Control`, `slem Control→/remote Control`, `SlashG→/goal`, `Slash Clear→/clear`, `Rustinger→Hostinger`, `Hey Claud/Clud`, `Clode/Clot/Cludier→Claude`, `closed starten→claude starten`, `Anmoldeformular→Anmeldeformular`, `züllen→füllen`, `erknüpfen→verknüpfen`, `debugen→debuggen`, `Impressummatte→Impressumsmaske`. Diese sind jetzt in die `POST_MERGE_PATTERNS`-Liste eingepflegt. (3) **Compound-Adjective-Falle**: "Cloud Code Skill" (Bindestrich-Compound-Adjektiv) bleibt korrekt — nur standalone "Cloud Code" wird ersetzt. Der Merger hat das geprüft. (4) **4 Rest-Ambiguitäten konservativ belassen** weil Kontext unklar: `KFM2 Plan` (vermutlich KVM 2 Plan), `Resent` (vermutlich Resend), `[musik]` (vermutlich Auto-Mode-Setting), `Textag` (unklar). Diese sind im File-Header dokumentiert. **Ergebnis**: 23/23 Minuten-Marker erhalten, +1.14% Wort-Drift (innerhalb 5%-Limit), NULL Restfehler im polierten Block, 4 Ambiguitäten im Header. Beste Quality-Bilanz aller bisherigen Stufe-3-Runs. **Lessons learned fürs Schwarms-Pattern**: (a) Worker 2's Stil-Output kann Compound-Wort-Bugs einführen — Merger muss eigenes Post-Verifikations-Verfahren haben, (b) Worker 3 (Faktencheck) ist der wertvollste Worker weil er die Lücken findet die Worker 1+2 nicht kennen, (c) Konservative Belassung von Ambiguitäten ist besser als Halluzinations-Fixes.
- **2026-07-09 (Remote Control, pvhphecd70Y, Stufe 4, 5-Worker-Bienen-Muster + LLM-Glättung)**: Erster vollständiger Stufe-3→Stufe-4-Pipeline-Run. Sub-Phase 4.1: 2 hochsichere Ambiguitäten deterministisch gefixt (`KFM2→KVM 2` Hostinger-Standardtarif, `Resent→Resend` E-Mail-API), beide nach Video-Kontext 85-90% sicher. Sub-Phase 4.2-4.3: Worker 5 (LLM-Glättung) dispatched als 5. Biene, geliefert in 50s (schneller als Stufe-3-Worker weil Single-Pass). Sub-Phase 4.4-4.5: Integration + Verifikation. Worker 5 hat 38 Satzzeichen-Korrekturen gemacht (28× Kommas vor Nebensätzen weil/dass/denn/und-Spaltsätze/sondern, 3× Infinitivgruppen, 2× Partizipialangaben, 3× Hervorhebungen, 2× Aufzählungen) und 4 Wort-Reparaturen (Relativpronomen-Deklination "mit dem wir"→"mit denen wir" bei Bezug auf "Befehle" Plural, Kompositum "Danke-Seite" statt "Danke, Seite", "dass"→"das" Rechtschreib-Korrektur, fehlende Substantive ergänzt). **WICHTIGE Erkenntnis: Worker 5 hat 0 Füllwort-Reduktionen gemacht** — die strikte Anweisung "Julians Stil erhalten" wurde respektiert. Drift -0.06% (4904→4901, weit unter ±2%-Limit). **Lessons learned**: (1) Stufe 4 ist ein **polishing-only** Pass — keine inhaltlichen Änderungen, nur sprachliche Politur, daher kann ein einzelner Worker reichen (kein Merger nötig wenn Worker-5-Disziplin stimmt). (2) Die Königin muss **vor** dem LLM-Pass die hochsicheren Ambiguitäten fixen — sonst hat der LLM die Ambiguität als Fehler "erkannt" und halluziniert eine Lösung. (3) Strikte Constraints ("Julians Stil erhalten", "Eigennamen nicht anfassen") funktionieren gut — Worker 5 hat sie respektiert. (4) Wall-Clock für Stufe 4: ~5 Min (2 Min deterministische Fixes + 50s LLM + 3 Min Integration). **Empfehlung für künftige Sessions**: Stufe 4 nur für wichtige/zitierfähige Transcripts (Reference-Material, Schulungs-Dokumente), NICHT für Quick-Save-Captures.
