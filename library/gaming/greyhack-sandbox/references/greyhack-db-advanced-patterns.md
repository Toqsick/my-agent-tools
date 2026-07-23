# GreyHack DB — Advanced Cross-Reference Patterns

> Session: 2026-07-04, full report at `~/docs/system/greyhack-deep-intel-2026-07-04.md`
> Covers: Essid naming, password classification, AllLibs hash pool, connection status map, TipoRed chronology

---

## 1. Essid Naming Pattern Analysis

Every `Map.Essid` falls into two categories:

```sql
SELECT 
  CASE 
    WHEN Essid GLOB '*_*' THEN 'prefix-suffix (underscore)'
    ELSE 'no-underscore (brand name)'
  END AS pattern,
  count(*) AS n
FROM Map GROUP BY 1;
```

Typical: ~31 prefix-suffix (`Nroni_DIU`, `Flack_Y0ZQN`), ~25 brand names (`Kimball`, `Eidos`, `Yum!`). Underscore = wireless router SSID, bare name = wired/backbone.

---

## 2. Password Advanced Classification

### 2.1 Character Classes

```sql
SELECT 
  CASE 
    WHEN PlainPassword GLOB '*[0-9]*' AND PlainPassword NOT GLOB '*[a-zA-Z]*' THEN 'only-digits'
    WHEN PlainPassword NOT GLOB '*[0-9]*' AND PlainPassword GLOB '*[a-zA-Z]*' THEN 'only-letters'
    WHEN PlainPassword GLOB '*[0-9]*' AND PlainPassword GLOB '*[a-zA-Z]*' THEN 'alphanumeric'
  END AS class,
  count(*) AS n
FROM Passwords GROUP BY class;
```

Typical (267 entries): 239 only-letters, 13 only-digits, 15 alphanumeric.

### 2.2 Trivially Weak Passwords

```sql
SELECT ID, PlainPassword, length(PlainPassword) AS len
FROM Passwords
WHERE PlainPassword GLOB '[0-9]*' OR length(PlainPassword) <= 3
ORDER BY len, PlainPassword;
```

Finds 9+ passwords like `555`, `333`, `321`, `000`, `1111`, `67890` — brute-forceable in seconds.

### 2.3 Word Types

Three categories: **pseudo-words** (`Rockso`, `owmana`, `gundan`, `dancil`), **brand/marken** (`Bill`, `Yum!`, `Adelholzener` = German water brand, 12 chars — likely Easter egg), **digit-only** (`333`, `1111`). Pseudo-words are procedurally generated.

---

## 3. AllLibs — Library Hash Pool (distinct from VersionsControl)

`InfoGen.AllLibs` (~8.3 KB) contains hash pools per library — references for `Map.LibVersions`:

```json
{"libssh.so": ["c1ee51c1...", "f3d1031c..."], "libftp.so": ["b0d6c815...", "bcbaf187..."]}
```

| Column | Size | Purpose |
|--------|------|---------|
| `VersionsControl` | 143 KB | Exploit mechanics: zones, addresses, vulnerabilities |
| `AllLibs` | 8.3 KB | Host generation: hash pool for `Map.LibVersions` |

---

## 4. Connection Map — 3-Way Status

```sql
SELECT DISTINCT m.IpAddress, m.Essid,
  CASE 
    WHEN EXISTS(SELECT 1 FROM Logs WHERE ID LIKE m.IpAddress || ':%') THEN 'in-logs'
    WHEN EXISTS(SELECT 1 FROM WebPages WHERE PublicIp = m.IpAddress) THEN 'has-webpage'
    ELSE 'untouched'
  END AS status
FROM Map m ORDER BY status, m.IpAddress;
```

Typical: ~48 has-webpage, ~2 in-logs (player-visited), ~8 untouched (never visited). Bounce-IPs (from `Logs.contentLog.bounceIp`) are compromised routers.

---

## 5. TipoRed Chronology — World Expansion

```sql
SELECT TipoRed, count(*) AS n, min(Date) AS first_gen
FROM Map GROUP BY TipoRed ORDER BY TipoRed;
```

Key: TipoReds 14/15/17 are ALL first-generation (game start). New ones like 6 and 9 appear at later dates — world expands as player explores. Date format: `YYMMDD` (e.g. `260617`).

---

## 6. Case Study Report

Full 669-line report: **`~/docs/system/greyhack-deep-intel-2026-07-04.md`**

Key finding: `ee23d05c-6782-4aa8-8565-86e8d3045168` TokenTrace = active session (36 actions, 21h). Player chain: Therwing (ISP) → Pool (bounce) → Erpillinek (mission target) → Waterso (lateral move) → Kimball (home base).
