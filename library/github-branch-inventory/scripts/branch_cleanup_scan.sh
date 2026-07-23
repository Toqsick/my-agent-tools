#!/bin/bash
# Branch cleanup scan — list branches across multiple repos, fetch last-commit
# date per branch, classify by staleness, output TSV + counts.
#
# Usage:
#   OWNER=Toqsick \
#   REPOS="greyscripts hermes-v7 MaxClaw" \
#   REFERENCE_DATE=2026-07-07 THRESHOLD_DAYS=30 \
#   ./branch_cleanup_scan.sh
#
# Env:
#   OWNER            GitHub owner/org (required)
#   REPOS            space-separated repo list (required)
#   REFERENCE_DATE   YYYY-MM-DD — "today" for age calculation (default: today UTC)
#   THRESHOLD_DAYS   STALE threshold in days (default: 30)
#   OUTPUT_PREFIX    output file prefix (default: /tmp/branch_cleanup)
#
# Output:
#   stdout  : nothing (data goes to TSV)
#   stderr  : human-readable summary (counts)
#   file    : ${OUTPUT_PREFIX}.tsv with header
#             repo \t branch \t sha \t date \t age_days \t status

set -uo pipefail

: "${OWNER:?Set OWNER=<github-user>}"
: "${REPOS:?Set REPOS=\"repo1 repo2 repo3\"}"

REFERENCE_DATE="${REFERENCE_DATE:-$(date -u +%Y-%m-%d)}"
THRESHOLD_DAYS="${THRESHOLD_DAYS:-30}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-/tmp/branch_cleanup}"

if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh CLI not authenticated. Run: gh auth login" >&2
  exit 1
fi

OUT_TSV="${OUTPUT_PREFIX}.tsv"

printf "repo\tbranch\tsha\tdate\tage_days\tstatus\n" > "$OUT_TSV"

ref_epoch=$(date -u -d "$REFERENCE_DATE" +%s)

for repo in $REPOS; do
  # /branches API only returns name + commit.sha (no date). We have to
  # fetch per-branch via /commits/{sha} to get the commit date.
  gh api "repos/$OWNER/$repo/branches?per_page=100" --paginate \
    --jq '.[] | "\(.name)\t\(.commit.sha)"' 2>/dev/null \
  | while IFS=$'\t' read -r branch sha; do
      [ -z "$branch" ] && continue
      date_str=$(gh api "repos/$OWNER/$repo/commits/$sha" \
        --jq '.commit.committer.date // .commit.author.date // ""' 2>/dev/null)
      age=9999
      if [ -n "$date_str" ]; then
        commit_epoch=$(date -u -d "$date_str" +%s 2>/dev/null || echo "$ref_epoch")
        age=$(( (ref_epoch - commit_epoch) / 86400 ))
      fi
      if [ "$age" -gt "$THRESHOLD_DAYS" ]; then
        status="STALE"
      else
        status="ACTIVE"
      fi
      printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
        "$repo" "$branch" "$sha" "$date_str" "$age" "$status" \
        >> "$OUT_TSV"
    done
done

total=$(tail -n +2 "$OUT_TSV" | wc -l | tr -d ' ')
stale=$(awk -F'\t' 'NR>1 && $6=="STALE"' "$OUT_TSV" | wc -l | tr -d ' ')
warn=$(awk -F'\t' -v t="$THRESHOLD_DAYS" 'NR>1 && $5>14 && $5<=t' "$OUT_TSV" | wc -l | tr -d ' ')
active=$(awk -F'\t' 'NR>1 && $6=="ACTIVE"' "$OUT_TSV" | wc -l | tr -d ' ')

cat <<EOF >&2
Branch-cleanup scan complete.
  OWNER=$OWNER
  REPOS=$REPOS
  REFERENCE_DATE=$REFERENCE_DATE
  THRESHOLD_DAYS=$THRESHOLD_DAYS
  Total:   $total
  STALE:   $stale  (>${THRESHOLD_DAYS}d)
  WARN:    $warn   (15-${THRESHOLD_DAYS}d)
  ACTIVE:  $active (<=14d)
Output: $OUT_TSV
EOF
