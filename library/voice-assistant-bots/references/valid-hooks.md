# Hermes VALID_HOOKS Reference (from hermes_cli/plugins.py)

## Source of Truth

Diese Hooks sind in `hermes_cli/plugins.py` als `VALID_HOOKS` definiert.
Jeder Plugin-`provides_hooks`-Eintrag MUSS hier drin sein — sonst lädt die
Plugin-Engine das Plugin still, feuert aber nie.

## Hook-Tabelle

| Hook | Wann gefeuert | Zweck |
|------|---------------|-------|
| `pre_tool_call` | Vor jedem Tool-Call | Blocken, ratelimiten, modifizieren |
| `post_tool_call` | Nach jedem Tool-Call | Resultat inspizieren/loggen |
| `transform_terminal_output` | Terminal-Output vor Agentenanlieferung | Ausgabe filtern/umformatieren |
| `transform_tool_result` | Tool-Resultat vor Agentenanlieferung | Result umbauen |
| `transform_llm_output` | LLM-Antwort vor User-Auslieferung | Text transformieren — **am ehesten geeignet für TTS-Injection** |
| `pre_llm_call` | Vor jedem LLM-API-Call | Prompt manipulieren |
| `post_llm_call` | Nach jedem LLM-API-Call | Completion inspizieren |
| `pre_verify` | Vor Verification-Stop-Guard | Keep-going/block Entscheidung |
| `pre_api_request` | Vor HTTP-API-Call | Request manipulieren |
| `post_api_request` | Nach HTTP-API-Call | Response inspizieren |
| `api_request_error` | Bei API-Fehler | Error-Handling |
| `on_session_start` | Session-Start | Initialisierung |
| `on_session_end` | Session-Ende | Cleanup |
| `on_session_finalize` | Finalisierung | Persistentes Loggen |
| `on_session_reset` | Reset | State löschen |
| `subagent_start` | Subagent startet | Monitoring |
| `subagent_stop` | Subagent stoppt | Ergebnis erfassen |
| `pre_gateway_dispatch` | Gateway-Nachricht vor Dispatch | Message muten/rewrite/allow |
| `pre_approval_request` | Approval-Abfrage | Override/Loggen |
| `post_approval_response` | Approval-Antwort eingetroffen | Audit-Trail |
| `kanban_task_claimed` | Kanban-Task beansprucht | Dispatcher-Monitoring |
| `kanban_task_completed` | Kanban-Task fertig | Worker-Monitoring |
| `kanban_task_blocked` | Kanban-Task blockiert | Worker-Monitoring |

## Plugin-Entwicklung: Quick-Check

```bash
# Prüfe ob dein Hook existiert:
grep -oP '"([^"]+)"' ~/.hermes/hermes-agent/hermes_cli/plugins.py | head -n 30

# Debug-Modus starten:
HERMES_PLUGINS_DEBUG=1 hermes
```

## Was NICHT existiert (Fehler die ich schon gemacht habe)

| Falscher Hook | Warum es nicht feuert |
|---|---|
| `post_response` | ❌ Nicht in VALID_HOOKS. Existiert nirgends in Hermes |
| `on_response` | ❌ Nicht in VALID_HOOKS |
| `response_complete` | ❌ Nicht in VALID_HOOKS |

## Richtiger Weg: `/voice tts`

Statt eines Plugins für Auto-TTS: **Hermes hat built-in `/voice tts`** für Telegram und Discord,
und `/voice on` für CLI-Voice-Modus. Kein Plugin nötig.
