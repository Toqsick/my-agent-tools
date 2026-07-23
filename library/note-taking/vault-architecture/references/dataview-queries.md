# Dataview Queries for Vault Health Monitoring

## Top Hubs (sorted by Out-Links)

```markdown
\`\`\`dataview
TABLE length(file.outlinks) AS "Out-Links"
FROM ""
SORT length(file.outlinks) DESC
LIMIT 10
\`\`\`
```

## Orphan Notes Check

```markdown
\`\`\`dataview
LIST FROM ""
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
\`\`\`
```

## Per-Folder Size

```markdown
\`\`\`dataview
TABLE length(file.outlinks) AS "Out-Links", file.size AS "Bytes"
FROM ""
WHERE file.name != "_MOC"
GROUP BY file.folder
\`\`\`
```

## Notes in a Folder

```markdown
<!-- Dataview query -->
\`\`\`dataview
TABLE file.ctime as Created, file.mtime as Modified
FROM "<folder-path>"
SORT file.name ASC
\`\`\`
```

## Monthly Review Checklist

1. **Wiki-Link-Coverage** — run Dataview queries above
2. **Verwaiste Notes** — enrich or archive
3. **Top-Hubs** — verify cross-connections are current
4. **Daily-Note-Coverage** — fill gaps if < 80%
5. **Tag-Inflation-Check** — notes with ≥ 7 tags need reduction
6. **Vault-Größe** — check against disk quota