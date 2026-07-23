# Cron Debug Deep Dive

## Debug Workflow
1. **Gateway:** `systemctl --user is-active hermes-gateway.service`
2. **Logs:** `journalctl --user -u hermes-gateway.service --since "1h" | grep -i "error\|fail\|429"`
3. **Pattern:** ALL LLM jobs fail → gateway. Only scripts → script bug.
4. **Test scripts:** `bash ~/.hermes/scripts/<name>.sh`
5. **Config drift:** Scripts may reference old providers

## Provider-Key-Health-Check
**Lesson:** 401 tarnt sich als 429.
1. Key in ENV? `grep '^KEY_NAME=' ~/.hermes/.env`
2. Key valid? `curl -s -H "Authorization: Bearer $KEY" https://<provider>/auth`
3. Model exists? `curl -s https://<provider>/models | jq '.[].id' | grep <model>`

## Config-Drift Scripts
`*-switch.sh` scripts hardcode `DESIRED_PROVIDER` + overwrite config. Before migration: grep scripts, backup, patch, test.
