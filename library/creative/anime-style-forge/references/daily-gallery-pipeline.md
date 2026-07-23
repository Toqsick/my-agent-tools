# Daily Gallery Pipeline (Image-to-Image Series)

## Trigger

User will eine tägliche Serie/Bildersammlung im selben Stil aus einer Referenz:
- "mache jeden Tag ein Bild nach diesem Muster"
- "tägliche Yuno-Galerie"
- "daily image series from reference"

## Pipeline-Übersicht

Anders als die normale Phase 0–5 Pipeline ist das ein **Endlos-Modus**: Einmal aufgesetzt, dann jeden Tag ein neues Bild mit neuem Tages-Prompt.

```mermaid
flowchart LR
    A[Setup: Referenz + Ordner + Cron] --> B[Jeden Tag: neues Motiv]
    B --> C[Referenz-URL (stabil) verwenden]
    C --> D[image_generate mit image_url + neuer Prompt]
    D --> E[Download + Galerie-Eintrag + Telegram]
    E --> B
```

## Phase 0.5: Daily-Gallery-Setup

### Einmalig: Galerie-Ordner + README + Referenz hochladen

```bash
mkdir -p ~/Bilder/yuno-gallery/
```

README mit Index erstellen. Referenz-Bild auf einen **dauerhaften Host** hochladen (wichtig für Cron-Jobs — einmalige URL für alle zukünftigen Generierungen).

### Referenz-Bild öffentlich hosten

Der FAL-image_generate (aktiver Backend: FLUX 2 Klein 9B) akzeptiert KEINE lokalen Pfade für `image_url`. Lokale Dateipfade wie `/home/bratan/Bilder/Yuno-Art.png` führen zu `file_download_error` (FAL-Cloud-Server können lokale Filesysteme nicht sehen).

**✅ Getestet und funktioniert: freeimage.host**

Dauerhafter Upload, keine Auth, kein Ablauf (expiry=0), liefert HTTPS-Direkt-URL:

```bash
curl -s -F "source=@/pfad/zum/referenz.png" -F "type=file" -F "action=upload" \
  "https://freeimage.host/json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['image']['url'])  # z.B. https://iili.io/XXXXX.png"
```

Die URL ist dauerhaft — einmal hochladen und als Konstante im Cron-Prompt hardcoden.

**❌ Definitiv kaputte Upload-Services (Stand Juli 2026):**

| Service | Fehler |
|---------|--------|
| `catbox.moe/user/api.php` | "Invalid uploader" |
| `litter.catbox.moe/resources/internals/api.php` | 404 Not Found |
| `0x0.st` | Deaktiviert ("AI botnet spam") |
| `transfer.sh` | Connection reset |
| `imgbb.com` | "Request denied" |
| `pixeldrain.com` | Auth required |
| `temp.sh` | Form-basierter Download, keine direkte Image-URL |

**Alternative bei Cron ohne Public-Host:** Agent kann einen temporären HTTP-Server starten (`python3 -m http.server`) und seine eigene IP nutzen — funktioniert aber NUR wenn das Backend (FAL) das Netzwerk des Hosts erreicht (also nicht für Cloud-Backends).

### Tägliches Bild generieren

**Schritt 1: image_generate mit image_url + Prompt**

Nutze die `image_generate`-Funktion (image-to-image-Modus) mit:

```
image_generate(
    image_url="https://iili.io/XXXXX.png",   # stabile öffentliche Referenz-URL
    aspect_ratio="landscape",                  # 16:9 → 1344×768 px
    prompt="[neues Tagesthema], Yuno Gasai from Mirai Nikki, pink twin-tail hair, red eyes, wearing dark school uniform with red bow tie, [spezifische Pose/Szene], [Stimmungsbeschreibung], anime style, cute, kawaii"
)
```

Wichtig im Prompt:
- `Yuno Gasai from Mirai Nikki, pink twin-tail hair, red eyes` als Character-Anker
- Das Referenzbild VISUELL angeben (über image_url) — der Prompt beschreibt die *neue Szene*
- Die `same character design`-Klausel im Prompt ist optional — `image_url` allein sorgt schon für Image-to-Image

**Schritt 2: Download + Einsortieren**

```bash
curl -sL -o ~/Bilder/yuno-gallery/day-NNN-YYYY-MM-DD.png "URL_aus_generate"
```

**Schritt 3: README-Index updaten**

Den Markdown-Table in der Galerie-README um den neuen Eintrag ergänzen (3-stellige Nummer + Datum + Kurzbeschreibung).

## Output-Format

FLUX 2 Klein 9B (FAL) generiert 1344×768 px (16:9 landscape direkt). Kein vierfach-Grid-Cropping nötig — FAL gibt Single-Image aus. Der `aspect_ratio` Parameter steuert die Auflösung automatisch.

## Pitfalls

| Problem | Lösung |
|---------|--------|
| `image_url` mit local path → file_download_error | Immer public HTTPS-URL nutzen, nie lokale Pfade |
| Upload-Service down / geändert | freeimage.host mit `expiration: 0` = dauerhaft; einmalig hochladen und URL hardcoden |
| Stil-Treue ohne vision-check | Referenz-Bild wird vom Backend intern gesehen; Nutzerfeedback = einziger QA-Kanal |
| Cron läuft aber nichts passiert | Prüfen: Cron-Job hat `deliver` gesetzt? Lieferziel erreichbar? Agent-Modell verfügbar? |
| Gleiches Datum → falsche Nummer | Cron muss README einlesen, letzte Nummer finden, inkrementieren — nicht vom aktuellen Datum ableiten |
| `image_generate` im Cron | Funktioniert — der Cron-Agent hat vollen Toolzugriff. Prompt muss self-contained sein (kein Memory-Zugriff im Cron-Kontext) |

## Cron (Standard für Automatisierung)

### Hermes-Cron-Job für tägliche Bildgenerierung

Erstelle einen Cron-Job mit `cronjob` Tool:

```bash
# schedule: täglich 21:00 (End-of-Day)
# deliver: an den User via Telegram oder anderen Messenger
# prompt: self-contained Anweisung mit allen Schritten (kein Kontext aus Session nötig)
```

**Cron-Prompt-Struktur (self-contained):**

```
Du bist Yuno, Bastis KI-Assistent.

WORKFLOW:
1. README lesen → letzte Nummer NNN finden → nächste Nummer NNN+1
2. Kreatives Tagesmotiv ausdenken (siehe Themen-Liste unten)
3. image_generate(image_url="[STABILE_REF_URL]", aspect_ratio="landscape",
     prompt="[Motiv], Yuno Gasai, pink twin-tail hair, red eyes, ...")
4. curl download nach ~/Bilder/yuno-gallery/day-NNN-YYYY-MM-DD.png
5. README-Index per patch() updaten (neue Tabellenzeile einfügen)
6. Abschluss-Nachricht mit MEDIA:/pfad/zum/bild (für Telegram-Inline-Bild)

TÄGLICHE THEMEN-IDEEEN (je eines pro Tag auswählen):
- Yuno am Strand / im Schwimmbad (Sommer!)
- Yuno beim Eisessen an heißen Tagen
- Yuno chillt mit einem Buch im Park
- Yuno beim Sonnenuntergang am See
- Yuno zockt spätnachts am PC (Gaming-Session)
- Yuno im GreyHack-Hoodie (Bastis Projekt!)
- Yuno beim Sternschnuppen-Watching
- Yuno im Regen mit Schirm
- Yuno backt Kekse / Cupcakes
- Yuno beim Zelten / Lagerfeuer
- Yuno im Sommerkleid mit Sonnenhut
- Yuno füttert Katzen im Park
```

**Wichtig für Cron-Prompt:**
- `deliver` auf User-Chat setzen (z.B. `telegram:7222661188`)
- Referenz-URL muss stabil sein (freeimage.host, NICHT litter.catbox.moe)
- Der Agent muss die README SELBST einlesen — kein Kontext aus vorheriger Session
- MEDIA:-Pfad im finalen Response für Inline-Bild-Delivery auf Telegram
