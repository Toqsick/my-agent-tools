# Awesome-Hacking Research for GreyHack

Condensed knowledge bank from the 2026-06-19 research pass over `Toqsick/Awesome-Hacking` / `Hack-with-Github/Awesome-Hacking`.

## Scope

`Awesome-Hacking` is useful for GreyHack MMO as a **concept and methodology source**, not as a 1:1 port source. Most entries target real-world security work; translate only safe game-relevant patterns into GreyScript tools, missions, CTF-style puzzles, or documentation.

## Full 68-Repo Categorization (2026-06-19, Toqsick/Awesome-Hacking Fork)

### 🔴 HIGH — Direkt im Spiel nutzbar (11 Repos)

| Repository | GreyHack-Connection | Aktuelle GreyScript-Tools |
|---|---|---|
| [SecLists](https://github.com/danielmiessler/SecLists) | Wordlists (Usernames, Passwords, Subdomains) → Input für Forcer, Decypher | `forcer.src`, `decypher.src` |
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | Web Payloads + ByPasses → Exploit-Entwicklung | `metaxploit.src`, `auto_exploit.src` |
| [GTFOBins](https://gtfobins.github.io) | Unix LPE-Techniken → GreyHack-Missionen nutzen exakt diese Binaries | **Kein Tool existiert → Opportunity!** |
| [Probable Wordlists](https://github.com/berzerk0/Probable-Wordlists) | Wahrscheinlichkeitsbasierte Passwörter → bessere Crack-Rate | `forcer.src` |
| [CyberChef](https://gchq.github.io/CyberChef) | Decode/Encode (Base64, Hex, ROT, XOR) → Crypto-Challenges | `decypher.src` (Caesar/Vigenere/XOR) |
| [Awesome Pentest](https://github.com/enaqx/awesome-pentest) | Pentest-Methodik → Missions-Chain | Portscan → Metaxploit → Backdoor |
| [Awesome OSINT](https://github.com/jivoi/awesome-osint) | Whois, DNS, Subdomain Recon | `recon_lite.src`, `recon.src` |
| [Awesome CTF](https://github.com/apsdehal/awesome-ctf) | CTF-Strategien = Mission-Solving | Alle Tools |
| [Bug Bounty Reference](https://github.com/ngalongc/bug-bounty-reference) | Write-ups nach Bug-Typ → Exploit-Strategien | Kein spezifisches Tool |
| [Awesome Password Cracking](https://github.com/n0kovo/awesome-password-cracking) | Cracking-Tools + Wordlists → Methodik | `decypher.src`, `forcer.src` |
| [Awesome Web Hacking](https://github.com/infoslack/awesome-web-hacking) | SQLi, XSS, LFI → SQL-Server + Web-Missionen | `portscan.src`, `metaxploit.src` |

### 🟡 MEDIUM — Indirekt relevant (9 Repos)

| Repository | Warum relevant |
|---|---|
| [Cryptography](https://github.com/sobolevn/awesome-cryptography) | Algorithmen-Verständnis für decypher (Caesar, Vigenere, XOR, RSA) |
| [Vulhub](https://github.com/vulhub/vulhub) | Docker-Vulnerable-Environments → ähnliche Szenarien im Spiel |
| [Red Teaming Toolkit](https://github.com/infosecn1nja/Red-Teaming-Toolkit) | Komplette Red-Team-Chain (Recon → Exploit → Persistence) |
| [Social Engineering](https://github.com/giuliacassara/awesome-social-engineering) | Phishing/Manipulation → SMTP-Enum + Social Engineering Missionen |
| [Malware Analysis](https://github.com/rshipp/awesome-malware-analysis) | Backdoor/Ransomware-Verständnis → `backdoor.src`, `ransomeware.src` |
| [Reversing](https://github.com/HACKE-RC/awesome-reversing) | Binary-Reversing für Exploit-Entwicklung |
| [Fuzzing](https://github.com/secfigo/Awesome-Fuzzing) | Fuzzing-Strategien → Buffer-Overflow-Exploit |
| [Linux Kernel Exploitation](https://github.com/xairy/linux-kernel-exploitation) | Kernel-Exploit-Techniken → Kernel-Missionen |
| [Tor / Awesome Tor](https://github.com/polycarbohydrate/awesome-tor) | Anonymitätstechniken → GreyHack-Anonymity-Mechaniken |

### ⚪ LOW — Nicht GreyHack-relevant (7+ Repos, für später archiviert)

- Android Security, OSX/iOS Security, PHP Security, Node.js Security
- CI/CD Attacks, Industrial Control Security, Mainframe Hacking
- Cellular Hacking, AI Security, ML for Cyber Security
- Prompt Injection, Web3 Security, Suricata
- Detection Engineering, Red Team Physical Tools, RFSec-ToolKit
- **Archiviert in:** `~/docs/system/awesome-hacking-research-2026-06-19.md`

## Top-20 GreyHack Ranking (2026-06-19, Toqsick/Fork)

| Rank | Resource | Prio | GreyHack-Connection | Aktueller Tool-Bezug |
|---:|---|---|---|---|
| 1 | SecLists | HIGH | Wordlists für forcer/decypher | `forcer.src`, `decypher.src` |
| 2 | PayloadsAllTheThings | HIGH | Exploit-Payloads für metaxploit | `metaxploit.src` |
| 3 | GTFOBins | HIGH | LPE-Techniken — GreyHack-Missionen nutzen genau das | **Kein Tool → Opportunity** |
| 4 | Probable Wordlists | HIGH | Optimierte Wordlists für Cracking | `forcer.src` |
| 5 | CyberChef | HIGH | Crypto/Encode-Decode-Verständnis | `decypher.src` |
| 6 | Awesome Pentest | HIGH | Pentest-Methodik = Missions-Chain | Alle Tools |
| 7 | Awesome OSINT | HIGH | recon_lite Inspirationsquelle | `recon_lite.src`, `recon.src` |
| 8 | Awesome CTF | HIGH | CTF-Strategien = Mission-Solving | Alle Tools |
| 9 | Bug Bounty Reference | HIGH | Exploit-Strategien nach Bug-Typ | Kein Tool |
| 10 | Awesome Password Cracking | HIGH | Cracking-Methodik | `decypher.src`, `forcer.src` |
| 11 | Awesome Web Hacking | HIGH | Web-Exploit-Techniken | `metaxploit.src` |
| 12 | Cryptography | MED | Crypto-Algorithmen für decypher | `decypher.src` |
| 13 | Vulhub | MED | Verwundbare-Szenarien Inspiration | — |
| 14 | Red Teaming Toolkit | MED | Red-Team-Workflow für Tool-Chain | Alle Tools |
| 15 | Social Engineering | MED | Phishing-Missionen | `smtp_enum.src` |
| 16 | Malware Analysis | MED | Backdoor/Ransomware-Verständnis | `backdoor.src` |
| 17 | Reversing | MED | Exploit-Development-Knowledge | — |
| 18 | Fuzzing | MED | Exploit-Finding-Strategien | — |
| 19 | Linux Kernel Exploitation | MED | Kernel-Exploit-Knowledge | — |
| 20 | Tor / Anonymity | MED | Anonymity-Mechaniken | — |

### P1 Next Steps (from 2026-06-19 session)
1. **GTFOBins erkunden** → LPE-Tool in GreyScript bauen (aktuell kein Tool!)
2. **SecLists Wordlists** → in GreyHack importieren für Forcer-Testing
3. **Probable Wordlists** → Download + Test gegen Standard-GreyHack-Wordlists
4. **28 tool-specific one-liner-inspection bugs** — all in the original Github repo, 0 in active src/

## Recommended workflow

1. **Research first, scripts later.** Do not edit `src/` or `tools/` until the Top-20 plan and safety filter are written.
2. **Create a Top-20 plan.** Use `.hermes/plans/` for a bite-sized implementation plan with exact future paths.
3. **Create a knowledge database for the rest.** Store lower-priority resources in Markdown/CSV so later research can resume without re-reading everything.
4. **Filter through GreyScript constraints.** GreyScript 1.5.1 has `0` truthy, no negative indices, no `str_repeat`, no real HTTP, `char(10)` for newline, and `is_binary` is not a reliable folder detector.
5. **Prefer concept transfer over porting.** Real-world exploit tools should become game-safe mechanics: recon, scanning, parsing, logging, debugging, crypto puzzles, or documentation.
6. **Use HermesUltraCode for delegated implementation.** If a later implementation uses `delegate_task`, expect the cross-lab gate to tighten or block the worker prompt.

## Candidate files for future implementation

Only after review:

- `tools/portscan.src` — `portscan-v2`
- `src/filecore.src` — `filecore-hardened`
- `src/debugcore.src` — debug/trace improvements
- `src/crypto/decypher.src` — game-safe cipher helpers
- `src/crypto/grsa_v2.src` — puzzle/crypto mechanics only

## Knowledge database schema for lower-priority resources

Use CSV or Markdown with:

```csv
resource,section,url,relevance_score,why_later,future_angle,notes
```

Suggested scores:

- `high` — top-20 or near-top-20
- `medium` — useful later, but not first
- `low` — keep for reference only

## Safety filter

Reject or defer ideas that require:

- real exploit execution
- real credentials or leaked wordlists
- external network targets
- OS shell access unavailable in GreyHack
- HTTP or real web services unavailable in GreyScript
- destructive host operations

Translate instead into:

- CTF-style puzzles
- local dummy data
- parser/testcase design
- in-game recon/logging tools
- defensive or hardening concepts
