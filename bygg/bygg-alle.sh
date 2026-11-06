#!/usr/bin/env bash
# Bygger gjeldende versjon (main) og en forhåndsvisning per åpent
# endringsforslag (PR) til _site/ og _site/pr/<nummer>/.
#
# Kjøres fra roten av en klone av main. Krever gh (innlogget) og jq.
# Koden i bygg/ hentes alltid fra main. Fra PR-ene leses bare innhold
# (paragrafer/, vedlegg/, struktur.yml, historikk.md), aldri kode.
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-asle-vaskinn/hyttelov}"
KILDE="https://github.com/$REPO"
UT="${1:-_site}"
TMP="$(mktemp -d)"

# Åpne forslag fra dette repoet (ikke forks), eldste først.
gh api "repos/$REPO/pulls?state=open&per_page=100" --paginate \
  --jq "[.[] | select(.head.repo.full_name == \"$REPO\") | {nummer: .number, tittel: .title, url: .html_url}]" \
  | jq -s 'add // [] | sort_by(.nummer)' > "$TMP/forslag.json"

python bygg/bygg.py "$UT" --kilde "$KILDE" --forslag "$TMP/forslag.json"

for n in $(jq -r '.[].nummer' "$TMP/forslag.json"); do
  git fetch -q origin "+refs/pull/$n/head:refs/forslag/$n"
  base="$(git merge-base HEAD "refs/forslag/$n")"
  git worktree add -q --detach "$TMP/pr-$n" "refs/forslag/$n"
  git worktree add -q --detach "$TMP/base-$n" "$base"
  if ! python bygg/bygg.py "$UT/pr/$n" --innhold "$TMP/pr-$n" --sammenlign "$TMP/base-$n" \
        --pr "$n" --forslag "$TMP/forslag.json" --rot "../../" --kilde "$KILDE"; then
    echo "::warning::Endringsforslag #$n bygger ikke og vises ikke"
  fi
  git worktree remove --force "$TMP/pr-$n"
  git worktree remove --force "$TMP/base-$n"
done
