# DeepSeek V4 Flash & V4 Pro — Pricing-Details
Stand: Juni 2026, gesammelt von OpenRouter

## DeepSeek V4 Flash (284B total, 13B aktiv)

### Basis-Preise (pro 1M Tokens)

| Provider | Input $/M | Output $/M | Cache $/M | Uptime | Max Output |
|---|---|---|---|---|---|
| **Nous Portal (free)** | **$0** | **$0** | — | — | — |
| DeepInfra | $0,098 | $0,197 | $0,020 | 97,9% | 131K |
| OpenRouter (Default) | $0,10 | $0,20 | $0,02 | 99,1% | 16K |
| Parasail | $0,112 | $0,224 | $0,022 | 97,8% | 1,05M |
| DigitalOcean | $0,13 | $0,28 | $0,028 | 97,3% | 393K |
| Alibaba Cloud Int. | $0,134 | $0,268 | $0,027 | 99,9% | 393K |
| DeepSeek offiziell | $0,134 | $0,268 | $0,027 | 99,99% | 384K |

### Effektiv-Preise (cache-bereinigt, letzte Stunde)

| Provider | Input $/M | Output $/M | Cache Hit Rate |
|---|---|---|---|
| DeepSeek offiziell | $0,029 | $0,279 | 81,2% |
| NovitaAI | $0,057 | $0,279 | 73,8% |
| GMICloud | $0,063 | $0,223 | 54,7% |
| Alibaba Cloud Int. | $0,065 | $0,268 | 64,4% |
| DeepInfra | $0,072 | $0,199 | 34,6% |
| **Gewichteter Ø** | **$0,065** | **$0,264** | — |

### Performance

| Metrik | Bester Provider | Wert |
|---|---|---|
| Durchsatz | DeepSeek | 79 tok/s |
| Latenz (1. Token) | Parasail | 0,61 s |
| Tool Call Error Rate | DeepInfra | 1,22% |

---

## DeepSeek V4 Pro (1,6T total, 49B aktiv)

### Basis-Preise (pro 1M Tokens)

| Provider | Input $/M | Output $/M | Cache $/M |
|---|---|---|---|
| DeepSeek offiziell | $0,435 | $0,87 | $0,0036 |
| NovitaAI | $0,33 | $3,20 | ~Cache |
| DeepInfra | $0,75 | $2,60 | ~$0,14 |
| SiliconFlow | $0,62 | $3,48 | ~$0,08 |
| Alibaba Cloud Int. | $0,626 | $3,22 | ~Cache |
| DigitalOcean | $1,74 | $3,47 | kein Cache |
| Together | $1,35 | $4,40 | ~Cache |

### Effektiv-Preise (cache-bereinigt, letzte Stunde)

| Provider | Input $/M | Output $/M | Cache Hit Rate |
|---|---|---|---|
| DeepSeek offiziell | $0,052 | $0,869 | 88,7% |
| NovitaAI | $0,330 | $3,20 | 86,7% |
| SiliconFlow | $0,617 | $3,48 | 67,5% |
| Alibaba Cloud Int. | $0,626 | $3,22 | 66,8% |
| DeepInfra | $0,752 | $2,60 | 45,6% |
| **Gewichteter Ø** | **$0,348** | **$2,48** | — |

### Performance

| Metrik | Bester Provider | Wert |
|---|---|---|
| Durchsatz | Fireworks | 47 tok/s |
| Latenz (1. Token) | Parasail | 0,53 s |
| Tool Call Error Rate | Alibaba Cloud Int. | 2,50% |

---

## Kostenvergleich (realistische Szenarien)

### Pro Session (~5M Tokens, 70% Input / 30% Output)

| Modell / Provider | Kosten |
|---|---|
| V4 Flash / Nous Portal | €0 |
| V4 Flash / DeepInfra | ~$0,64 |
| V4 Flash / DeepSeek direkt | ~$0,87 |
| V4 Pro / DeepSeek direkt | ~$2,83 |
| V4 Pro / NovitaAI | ~$5,96 |
| V4 Pro / DeepInfra | ~$6,53 |

### Pro Tag (~10M Tokens)

| Modell / Provider | Kosten |
|---|---|
| V4 Flash / Nous Portal | €0 |
| V4 Flash / DeepInfra | ~$1,28 |
| V4 Pro / DeepSeek direkt | ~$5,66 |
| V4 Pro / DeepInfra | ~$13,05 |

### Pro Monat (~300M Tokens)

| Modell / Provider | Kosten |
|---|---|
| V4 Flash / Nous Portal | €0 |
| V4 Flash / DeepInfra | ~$38 |
| V4 Pro / DeepSeek direkt | ~$170 |
| V4 Pro / DeepInfra | ~$392 |

---

## Wichtige Erkenntnisse

- **Nous Portal Free Tier** ist der absolute Gewinner für V4 Flash — 0€, unbegrenzt im Free-Tier
- **DeepSeek V4 Pro** lohnt sich kaum gegenüber V4 Flash im Think-Max-Modus (90% der Qualität, 0% der Kosten)
- **Cache Hit Rates** sind bei DeepSeek offiziell extrem hoch (81-89%) — die effektiven Input-Kosten sind oft nur 10-20% der Listenpreise
- **Nous Portal Pricing Page** (portal.nousresearch.com/pricing) ist hinter Cloudflare — Preise für V4 Pro auf Nous sind nicht direkt auslesbar
- Für Premium-Analyse ist claude-opus-4.8 ($15/$75) die Alternative, nicht V4 Pro

---

## Quellen

- OpenRouter Modellseiten (Jun 2026)
- Effective Pricing über OpenRouter Past-Hour-Daten
- Nous Portal: Free Tier (Stand Jun 2026, per Teknium/Twitter)
