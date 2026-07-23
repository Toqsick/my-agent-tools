---
name: ui-dashboard
description: "Use when user asks for dashboard layout, KPI dashboard from data schema, composed dashboard UI with charts. NOT for single charts, data analysis, or backend data pipelines. Compose a full dashboard layout from a data schema — KPI cards, charts, tables."
version: 1.0.0
author: Yuno (Hermes Agent) — based on KIMI K2 UI-Factory-Pattern 2026-06-30
license: MIT
metadata:
  hermes:
    tags:
    - ui
    - dashboard
    - kpi
    - charts
    - data-visualization
    - monitoring
    - admin-panel
    - analytics
    related_skills:
    - ui-design-system
    - ui-component-library
    - ui-color-system
    - ui-data-table
    - ui-chart-builder
    - ui-factory
    part_of: ui-factory
    triggers:
    - dashboard
    - admin panel
    - monitoring dashboard
    - analytics view
    - KPIs
    - Übersichts-Seite
    - Statistiken anzeigen
    - metrics view
    - Admin-Page
    - Übersicht
    - Stats
    - Monitoring-View
    - visualize metrics
lane: worker-vision
reasoning_effort: xhigh
trigger_keywords: ['dashboard', 'data', 'charts', 'layout', 'schema']
keywords: ['dashboard', 'data', 'charts', 'layout', 'schema']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ui-factory']
---


## 🚨 AUTO-TRIGGER

Dieser Skill triggert **automatisch** wenn Bastis Input nach Dashboard/Data-Visualization fragt. Auch ohne expliziten Aufruf — wenn die Trigger-Phrasen matchen, wird dieser Skill geladen.

**Trigger-Keywords (deutsch + englisch):** dashboard, admin panel, monitoring, analytics, KPI, Übersicht, Statistik, Stats, metrics, visualize, data view, Monitoring-View, charts, graph, Auswertung, Übersichts-Seite

Wenn Basti nach **mehreren UI-Aspekten** fragt (z.B. "komplettes UI mit Dashboard + Components + Tokens"), wird stattdessen `ui-factory` getriggert (orchestriert die ganze Chain).

# ui-dashboard

> **Atom:** Composes a complete dashboard layout (KPI cards, charts, tables, filters) from a data schema. The "molecule" that combines all UI atoms into a working view.

## When to use

- User asks for a "dashboard", "admin panel", "monitoring UI"
- Want to visualize metrics (users, revenue, errors, latency)
- Need a real-time data view with filters and date-range
- Combining multiple data sources into one cohesive view

## Inputs

```yaml
data_schema:
  metrics:
    - name: "users"
      type: "count"  # count | sum | avg | custom
      source: "users table"
      format: "number"  # number | currency | percent | duration
    - name: "revenue"
      type: "sum"
      source: "orders.amount"
      format: "currency:USD"
      trend: "vs_last_week"
  charts:
    - name: "revenue_trend"
      type: "line"  # line | bar | area | pie | scatter
      x_axis: "date"
      y_axis: "revenue"
      period: "30d"
    - name: "users_by_plan"
      type: "pie"
      dimensions: ["plan", "user_count"]
  tables:
    - name: "recent_errors"
      columns: ["timestamp", "endpoint", "error_code", "message"]
      sortable: true
      filterable: true
      pagination: 20

filters:
  date_range: "last_30_days | last_7_days | custom"
  custom_filters: ["plan_type", "region", "user_role"]

framework: "react | vue | svelte | vanilla-html"
chart_lib: "recharts | chart.js | d3 | apexcharts"
```

## Output

**Single-file dashboard** with:
- Header (title, date-range picker, user-menu)
- KPI grid (4-6 cards)
- Charts row (1-2 charts)
- Data table (recent events/logs/errors)
- Sidebar (filters, navigation)
- Responsive layout (mobile: stack, desktop: grid)

## Workflow

### Step 1: Layout-Planning (2 min)

Standard dashboard grid:
```
┌─────────────────────────────────────────────────────────┐
│  HEADER (logo, title, date-range, user-menu)            │
├──────────┬──────────────────────────────────────────────┤
│          │  KPI 1    KPI 2    KPI 3    KPI 4           │
│  SIDEBAR ├──────────────────────────────────────────────┤
│  (filters│  Chart 1 (large)        │  Chart 2         │
│  + nav)  │                         │  (side panel)    │
│          ├──────────────────────────────────────────────┤
│          │  Data Table (recent events, paginated)       │
└──────────┴──────────────────────────────────────────────┘
```

**Responsive behavior:**
- **Desktop (≥1024px):** 4-column KPI grid, 2-column charts, sidebar visible
- **Tablet (768-1023px):** 2-column KPI grid, 1-column charts, sidebar collapsible
- **Mobile (<768px):** 1-column stack, sidebar = drawer, KPI cards = scrollable row

### Step 2: Component-Loading (1 min)

Use `ui-component-library` outputs:
- `<KpiCard>` from components
- `<Chart>` (recharts/chart.js adapter)
- `<DataTable>` from ui-data-table
- `<FilterPanel>` for sidebar
- `<DateRangePicker>` from ui-form-builder

### Step 3: KPI-Cards (3-5 min)

```tsx
// KpiCard.tsx
import { Card, Badge } from '@/components/ui';
import { ArrowUp, ArrowDown } from '@/icons';

interface KpiCardProps {
  label: string;
  value: string | number;
  trend?: {
    direction: 'up' | 'down' | 'flat';
    value: string; // "+12.5%"
    isPositive?: boolean; // override (e.g., error count going up is bad)
  };
  sparklineData?: number[];
}

export const KpiCard = ({ label, value, trend, sparklineData }: KpiCardProps) => {
  const trendColor = trend?.isPositive === false ? 'error' : 
                     trend?.direction === 'up' ? 'success' : 
                     trend?.direction === 'down' ? 'error' : 'neutral';
  
  return (
    <Card padding="lg">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {trend && (
        <div className={`kpi-trend trend-${trendColor}`}>
          {trend.direction === 'up' && <ArrowUp />}
          {trend.direction === 'down' && <ArrowDown />}
          <span>{trend.value}</span>
        </div>
      )}
      {sparklineData && <Sparkline data={sparklineData} />}
    </Card>
  );
};
```

### Step 4: Charts (5-10 min)

```tsx
// RevenueChart.tsx (recharts example)
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { color } from '@/tokens';

interface RevenueChartProps {
  data: Array<{ date: string; revenue: number }>;
}

export const RevenueChart = ({ data }: RevenueChartProps) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={color.neutral[200]} />
        <XAxis dataKey="date" stroke={color.neutral[500]} />
        <YAxis stroke={color.neutral[500]} />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: color.neutral[900],
            border: 'none',
            borderRadius: '0.5rem',
            color: color.neutral[50]
          }} 
        />
        <Line 
          type="monotone" 
          dataKey="revenue" 
          stroke={color.primary[500]} 
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6, fill: color.primary[500] }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

### Step 5: Data-Table (3-5 min)

Use `ui-data-table` skill for sortable/filterable/paginated tables:
```tsx
<RecentErrorsTable
  columns={[
    { key: 'timestamp', label: 'Time', sortable: true, format: 'datetime' },
    { key: 'endpoint', label: 'Endpoint', filterable: true },
    { key: 'error_code', label: 'Code', sortable: true, align: 'right' },
    { key: 'message', label: 'Message', truncate: 80 },
  ]}
  pageSize={20}
  onRowClick={(row) => openErrorDetails(row.id)}
/>
```

### Step 6: Filters + Sidebar (3-5 min)

```tsx
// FilterPanel.tsx
export const FilterPanel = ({ filters, onChange }) => {
  return (
    <aside className="filter-panel" aria-label="Filters">
      <h2>Filters</h2>
      <FilterGroup title="Date Range">
        <RadioGroup value={filters.dateRange} onChange={(v) => onChange({ ...filters, dateRange: v })}>
          <Radio value="7d">Last 7 days</Radio>
          <Radio value="30d">Last 30 days</Radio>
          <Radio value="90d">Last 90 days</Radio>
          <Radio value="custom">Custom range</Radio>
        </RadioGroup>
      </FilterGroup>
      <FilterGroup title="Plan">
        <MultiSelect
          options={['Free', 'Pro', 'Enterprise']}
          value={filters.plans}
          onChange={(v) => onChange({ ...filters, plans: v })}
        />
      </FilterGroup>
      <FilterGroup title="Region">
        <MultiSelect
          options={['US', 'EU', 'APAC']}
          value={filters.regions}
          onChange={(v) => onChange({ ...filters, regions: v })}
        />
      </FilterGroup>
    </aside>
  );
};
```

### Step 7: Empty-States + Loading (2 min)

Every dashboard section needs:
- **Loading state:** Skeleton placeholder (shimmer animation)
- **Empty state:** Illustration + helpful message + CTA
- **Error state:** Red banner + retry button + error details

```tsx
{loading && <KpiCardSkeleton />}
{!loading && data.length === 0 && <EmptyState 
  title="No data for this period"
  description="Try a different date range or check your filters"
  action={<Button onClick={resetFilters}>Reset filters</Button>}
/>}
{error && <ErrorBanner error={error} onRetry={refetch} />}
```

### Step 8: Live-Data-Integration (optional, 5-10 min)

Für **Live-Dashboards mit echten Daten** gibt es zwei Patterns:

#### Pattern A: SSE/WebSocket (React/Svelte)
```tsx
useEffect(() => {
  const eventSource = new EventSource('/api/metrics/stream');
  eventSource.addEventListener('update', (e) => {
    const update = JSON.parse(e.data);
    setLiveData(prev => [...prev.slice(-29), update]);
  });
  return () => eventSource.close();
}, []);
```

#### Pattern B: Python Data-Provider + fetch-Polling (Vanilla HTML)

Wenn das Dashboard als **static HTML** läuft aber echte Daten braucht (z.B. Hermes-Stats, System-Metriken):

**Architektur:**
```
Browser (live.html)
  ├── fetch() alle 10s → localhost:PORT/api/data
  │                          ↑
  │                    server.py (Python HTTPServer)
  │                     ├── subprocess → CLI-Befehle (hermes skills list, etc.)
  │                     ├── urllib → API-Endpoints (z.B. /api/status)
  │                     ├── psutil → System-Stats (CPU, RAM, Disk, Temp)
  │                     └── File-Scans (Memory-Files, Session-DBs)
```

**Schritte:**
1. **Data-Provider `server.py`** schreiben (siehe `references/live-data-provider-pattern.md`)
2. **Client-side `fetch()`** mit 10s Polling-Interval
3. **Auto-Refresh-Indicator** (Progress-Bar oben die sich über 10s füllt)
4. **Error-Banner** wenn Server nicht erreichbar
5. **Loading-States** (skeleton-shimmer bei ersten Load)
6. **Start-Skript** (`start.sh`) das Data-Provider + HTML-Server + Browser-Open kombiniert

**Key Insight — Hermes API-Surface (2026-07-01):**
- `/api/status` ist der **einzige no-auth Endpoint** — liefert Version, Gateway-State, Platforms, Active-Sessions
- Alle anderen `/api/*` Endpoints geben **HTTP 401 ohne Auth-Token**
- Für Skills/Profiles/Cron-Daten → `hermes` CLI via `subprocess` nutzen (braucht keinen Token)
- Für System-Stats → `psutil` (Python-Library, kein Auth nötig)
- **Caching** wichtig: CLI-Output alle 30-60s cachen, nicht bei jedem Request neu ausführen

**Template:** `templates/live-data-server.py` — fertiger Python-Server für Hermes-Stats

### Step 9: Interactive Accordion-Cards + KPI-as-Buttons (v3-Pattern, 2026-07-01)

User-Präferenz (explizit geäußert): **"alle tabs sollen anklickbar sein wo sich ein untermenü mit details die dazu passen es soll richtig übersichtlich sein"** — Dashboards sollen nicht alle Details sofort zeigen, sondern **Progressive Disclosure** nutzen: kompakte KPIs oben, klickbare Cards die aufklappen.

#### Accordion-Card Pattern

Jede Card ist ein `<article class="card">` mit:
- **`.card-header`** = klickbar (`role="button"`, `tabindex="0"`, `aria-expanded`)
- **`.card-body`** = `max-height: 0` → beim Aufklappen `max-height: 2000px` mit CSS-Transition
- **`.card-chevron`** = ▼ das sich um 180° dreht beim Aufklappen

```css
.card-body { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
.card.expanded .card-body { max-height: 2000px; transition: max-height 0.5s ease; }
.card-chevron { transition: transform 0.3s ease; }
.card.expanded .card-chevron { transform: rotate(180deg); }
```

```javascript
// Toggle beim Klick oder Enter/Space
document.querySelectorAll('.card-header').forEach(header => {
    const toggle = () => {
        const card = header.closest('.card');
        const expanded = card.classList.toggle('expanded');
        header.setAttribute('aria-expanded', expanded);
    };
    header.addEventListener('click', (e) => { e.stopPropagation(); toggle(); });
    header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
    });
});
```

#### KPI-as-Button Pattern (KPI-Cards die Details öffnen)

KPI-Cards oben (die kleinen Übersichts-Karten) sind **klickbar** und öffnen die zugehörige Detail-Card:

```html
<article class="kpi-card" data-target="card-system" tabindex="0" role="button">
  <div class="kpi-label">RAM</div>
  <div class="kpi-value" id="kpi-ram">9.8 / 15.3 GB</div>
</article>
<!-- ... später im Dokument ... -->
<article class="card" id="card-system">...</article>
```

```javascript
// KPI-Klick → öffnet zugehörige Card + scrollt dorthin
document.querySelectorAll('.kpi-card[data-target]').forEach(kpi => {
    kpi.addEventListener('click', () => {
        const target = document.getElementById(kpi.dataset.target);
        if (target) {
            target.classList.add('expanded');
            target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    });
});
```

#### "Alle auf/zu" Keyboard Shortcut (Ctrl+A)

```javascript
// Ctrl+A klappt alle Cards gleichzeitig auf oder zu
if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
    const cards = document.querySelectorAll('.card');
    const anyCollapsed = [...cards].some(c => !c.classList.contains('expanded'));
    cards.forEach(c => c.classList.toggle('expanded', anyCollapsed));
}
```

#### Mini-Tiles (Detail-Summary in aufgeklappter Card)

Jede aufgeklappte Card enthält am Ende eine **Mini-Tile-Row** mit großen Zahlen:

```html
<div class="detail-section">
  <div class="detail-title">⚡ Quick Stats</div>
  <div class="mini-chart">
    <div class="mini-tile"><div class="mini-tile-value">1</div><div class="mini-tile-label">Sessions</div></div>
    <div class="mini-tile"><div class="mini-tile-value">0</div><div class="mini-tile-label">Agents</div></div>
  </div>
</div>
```

#### Refresh-Rate Empfehlung

| Use Case | Refresh | Begründung |
|----------|---------|------------|
| **System-Monitoring** (CPU/RAM/Disk) | **3s** | User will sehen wie Last sich verändert — Basti's Explizit-Wunsch |
| **Hermes-Agent-Status** | 3-5s | Sessions/Agents ändern sich schnell |
| **SaaS-Production-Dashboard** | 10-30s | Metrics ändern sich selten, Server-Last minimieren |
| **Statisches Show-Dashboard** | kein Auto-Refresh | Demo, keine Live-Daten |

**Basti's Präferenz:** 3 Sekunden. Die Progress-Bar füllt sich in 2.8s und resettet beim nächsten fetch.

### Step 10: Multi-Theme Support (Theme-Mapping-Layer, 2026-07-08)

Wenn ein Dashboard **Token-System + Theme-Switcher + Data-Dense-Layout** kombinieren soll, brauchst du eine **dritte CSS-Schicht** zwischen dem Token-System (`colors.css`) und dem Layout-CSS:

```
Layer 1: Token-System (colors.css)         →  :root { --yuno-pink-500: #FF1493; ... }
Layer 2: Theme-Mapping-Layer               →  [data-theme="cozy"] { --yuno-accent-strong: #4338ca; ... }
Layer 3: Layout-CSS (im HTML)              →  .kpi-value { color: var(--yuno-accent-strong); }
```

**Warum Layer 2 nötig ist:** Das Token-System ist statisch. Der Theme-Switcher ändert die **semantische Zuordnung**: "Akzent im Cozy-Mode = Indigo, im Dark-Mode = Pink, im Cyber-Mode = Fuchsia". Wenn du direkt das Token-System editierst, brichst du den Theme-Switcher.

**Pattern — `data-theme`-Attribute auf Layout-Variablen mappen:**

```css
:root, [data-theme="cozy"] {        /* Warm-light, Indigo-Akzent */
  --yuno-bg:            var(--yuno-cream-50);
  --yuno-accent-strong: #4338ca;    /* Indigo-700 — extended-reading-safe */
  --yuno-accent-soft:   #6366f1;
  --yuno-fg-primary:    #1e1b4b;
  --yuno-fg-secondary:  #4338ca;
  --yuno-border:        #c7d2fe;
}
[data-theme="dark"] {                 /* Standard dark, Pink-Magenta */
  --yuno-bg:            #0f0f11;
  --yuno-accent-strong: #FF1493;     /* Yuno Pink */
  --yuno-fg-primary:    #fafafa;
  --yuno-fg-secondary:  #a1a1aa;
  --yuno-border:        #3f3f46;
}
[data-theme="cyberpunk"] {            /* Deep-purple, Fuchsia-Neon */
  --yuno-bg:            #0D0020;
  --yuno-accent-strong: #d946ef;     /* Fuchsia-500 */
  --yuno-border:        #581c87;
}
[data-theme="hc"] {                   /* Pure black, Bright-Pink (AAA) */
  --yuno-bg:            #000000;
  --yuno-accent-strong: #FF6BC6;
  --yuno-border:        #FFFFFF;
}
```

**Theme-Switcher JS:**

```javascript
function setTheme(name) {
  document.documentElement.setAttribute('data-theme', name);
  localStorage.setItem('yuno-theme', name);
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.toggle('active', b.dataset.theme === name));
}
const saved = localStorage.getItem('yuno-theme') || 'cozy';
setTheme(saved);
```

**Akzent-Auswahl-Guide:**

| Use-Case | Akzent | Begründung |
|----------|--------|------------|
| Light-Mode, extended use | **Indigo-700** `#4338ca` | Weniger ermüdend als Pink. Hoher Kontrast auf Cream-BG. |
| Light-Mode, Brand-heavy | **Pink-800** `#C2185B` | Brand-fidel. Braucht zwei Stufen dunkler für AA. |
| Dark-Mode (Standard) | **Pink/Magenta** `#FF1493` | Neon-Feeling, guter Kontrast auf Dark-Grey. |
| Cyberpunk-Mode | **Fuchsia** `#d946ef` | Neon-Asthetik auf tiefem Purple-BG. |
| HC-Mode | **Bright-Pink** `#FF6BC6` | Max-Kontrast auf pure-black. AAA-konform. |

**Pitfall — HC-Mode: Cards unsichtbar:**
```css
[data-theme="hc"] {
  --yuno-bg:        #000000;
  --yuno-bg-panel:  #0A0A0A;    /* 4% heller — subtle separation */
  --yuno-border:    #FFFFFF;     /* weiße Borders für Card-Trennung */
}
```

## Validation Checklist

- [ ] Layout responsive (mobile/tablet/desktop)
- [ ] All KPI cards have trend indicators
- [ ] All charts have hover-tooltip with formatted values
- [ ] All tables have sort + filter + pagination
- [ ] All filters actually filter (no dead controls)
- [ ] Loading + Empty + Error states for every section
- [ ] Date-range picker works with timezone handling
- [ ] Real-time updates don't break UI (cleanup on unmount)
- [ ] Color-coded trends (success/error) accessible to color-blind users (icon + text)
- [ ] Mobile: chart axes readable, tables scroll horizontally
- [ ] **Accordion-Cards sind keyboard-accessible** (Tab + Enter/Space)
- [ ] **KPI-Cards sind klickbar** und öffnen zugehörige Detail-Card
- [ ] **`aria-expanded`** korrekt gesetzt bei Accordion-Toggle
- [ ] **Color-coded bars** (grün <70%, gelb 70-90%, rot >90%)
- [ ] **Theme-Switcher mit 4 Modi** (Cozy/Dark/Cyber/HC) — localStorage-Persistenz
- [ ] **HC-Mode:** Card-BG ≠ Page-BG (sonst Cards unsichtbar)
- [ ] **HC-Mode:** Weiße Borders zur Card-Trennung
- [ ] **HC-Mode:** Kein Glow/Shadow (transparent)
- [ ] **Alle Theme-Pairs WCAG-geprüft** (mindestens 10 kritische Pairs pro Theme)
- [ ] **Theme-Mapping-Layer** verwendet `var(--*)` aus Token-System — kein Hardcoding
- [ ] **Theme-Wechsel funktioniert ohne Page-Refresh** (data-theme Attribut)
- [ ] **Browser-Konsole = 0 JS-Errors** (`browser_console` → `js_errors` leer)
- [ ] **browser_navigate zeigt echte Daten** (nicht skeleton/"connecting…")
- [ ] **Alle 4 Themes ohne Console-Fehler** (Theme-Klick + Console-Check)
- [ ] **Headless-Chrome liefert NICHT JS-Validierung** (siehe `references/browser-validation-workflow.md`)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Showing too many KPIs (>6) | Limit to 4-6 most important metrics |
| Charts with arbitrary y-axis scale | Always start at 0 for bar/area, log-scale for exponential |
| Tables without pagination | Always paginate (default 20 rows) |
| Filters that don't actually filter | Test every filter, add validation |
| No loading states | Skeleton loaders for every section |
| Color-only trend indicators | Add ↑/↓ icon + text label for accessibility |
| Long numbers without formatting | Use `Intl.NumberFormat` for 1,234,567 vs 1234567 |
| HC-Mode: Cards unsichtbar (Page-BG = Card-BG) | Set Card-BG 4% lighter (#0A0A0A vs #000) + white borders |
| Theme-Switcher ohne localStorage-Persistenz | `localStorage.setItem('yuno-theme', name)` + setzen beim Page-Load |
| Nur 2 Themes (light/dark) statt 4 | Biete Cozy/Dark/Cyber/HC — User liebt die Wahl (siehe ui-color-system) |
| Theme-Mapping-Layer fehlt — direktes Token-System-Editing | Dritte CSS-Schicht zwischen Tokens und Layout — siehe Step 10 |
| Akzent im Light-Mode zu knallig (Pink-500 auf Cream) | Pink-800 oder Indigo-700 — zwei Stufen dunkler als Brand |
| Sparklines mit hardcoded Farbe | SVG-Farbe per `var(--yuno-accent-strong)` dynamisieren |
| JS-Fehler nur im Browser sichtbar (nicht im Headless-Chrome) | `--virtual-time-budget` feuert Screenshot BEVOR async fetch() resolved. Nutze `browser_navigate` + `browser_console` für JS-Debug (siehe `references/browser-validation-workflow.md`) |

## Companion Skills

- **`claude-design`** — Dashboards sind **Monitor-Surfaces**. claude-design lehrt: "A dashboard is a Monitor surface, not a Decide surface — do not give it a centered hero and three feature cards." Lies das BEVOR du ein Dashboard baust — sonst bekommst du AI-Slop.
- **ui-design-system** — REQUIRED first (tokens)
- **ui-component-library** — Uses Button/Input/Card components
- **ui-color-system** — Generates color palette with contrast checks
- **ui-data-table** — Sortable/filterable/paginated tables
- **ui-chart-builder** — Chart components (bar, line, pie, area)
- **web-design-guidelines** — Vercel's UI review checklist

## Part of UI-Factory

This skill is the **highest-level atom** in the UI-Factory pattern — combines everything below it into a working dashboard. Use after `ui-design-system` + `ui-component-library` + `ui-data-table` + `ui-chart-builder` are scaffolded.

Based on the KIMI K2 UI-Factory-Pattern (2026-06-30).
