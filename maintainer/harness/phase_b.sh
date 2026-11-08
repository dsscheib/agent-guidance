#!/bin/sh
# V4-6 Phase B (maintainer/REDESIGN_NOTES.md), repository-only. Usage: phase_b.sh OUT_DIR [HOLDOUT_CATALOG]
# Six configurations at effort medium with no MCP, three conditions, S19-S24 from this repository and H1-H12 from the
# private holdout catalog (default ~/holdout/scenarios.json), three runs each: 6 x 3 x 18 x 3 = 972 runs.
# The conditions are interleaved: each scenario runs under all three before the next starts, so a change in a
# service over the batch falls on every condition alike, and the order of the conditions rotates from one scenario to
# the next. Labels are CONFIG-none (no guidance), CONFIG (this checkout, which must be a clean main) and CONFIG-3.0.2
# (the 3.0.2 release installed into the same fixtures). Providers run in parallel because their quotas are separate;
# each provider's configurations run one after another, so a quota stop leaves one configuration complete. run.py
# skips finished runs, so rerunning this script resumes where it stopped. Copilot runs later, once its quota renews.
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:?usage: phase_b.sh OUT_DIR [HOLDOUT_CATALOG]}
CATALOG=${2:-$HOME/holdout/scenarios.json}
RUNS=${RUNS:-1,2,3}
mkdir -p "$OUT"
RUN="python3 $REPO/maintainer/harness/run.py --out $OUT --workers 3 --effort medium --runs $RUNS"
SCENARIOS="S19 S20 S21 S22 S23 S24 H1 H2 H3 H4 H5 H6 H7 H8 H9 H10 H11 H12"

condition() {  # condition AGENT CONFIG SCENARIO none|main|3.0.2
    case $3 in H*) cat="--catalog $CATALOG" ;; *) cat= ;; esac
    case $4 in
        none) $RUN --agents "$1" --label "$2-none" --no-install --scenarios "$3" $cat ;;
        main) $RUN --agents "$1" --label "$2" --scenarios "$3" $cat ;;
        3.0.2) $RUN --agents "$1" --label "$2-3.0.2" --old-guidance 3.0.2 --scenarios "$3" $cat ;;
    esac
}

config() {  # config AGENT CONFIG
    i=0
    for s in $SCENARIOS; do
        case $((i % 3)) in
            0) order="none main 3.0.2" ;;
            1) order="main 3.0.2 none" ;;
            2) order="3.0.2 none main" ;;
        esac
        for c in $order; do
            echo "== $(date '+%F %T') $2 $s $c"
            condition "$1" "$2" "$s" "$c"
        done
        i=$((i + 1))
    done
}

provider() {  # provider NAME AGENT=CONFIG...
    name=$1; shift
    for pair in "$@"; do
        config "${pair%%=*}" "${pair#*=}"
    done >> "$OUT/progress-$name.log" 2>&1
}

[ "$(git -C "$REPO" branch --show-current)" = main ] || { echo "the candidate is main: check out main" >&2; exit 1; }
[ -z "$(git -C "$REPO" status --porcelain)" ] || { echo "the guidance checkout is not clean" >&2; exit 1; }
[ -f "$CATALOG" ] || { echo "no holdout catalog at $CATALOG" >&2; exit 1; }
git -C "$REPO" rev-parse -q --verify 3.0.2 >/dev/null || { echo "no 3.0.2 tag in $REPO" >&2; exit 1; }
echo "candidate main $(git -C "$REPO" rev-parse HEAD), started $(date '+%F %T')" >> "$OUT/BATCH.md"

provider claude claude@claude-haiku-5-5=claude-haiku claude@claude-opus-5-5=claude-opus &
provider codex codex@gpt-6-luna=codex-luna codex@gpt-6.1-sol=codex-sol &
provider antigravity agy@gemini-3.8-flash-medium=agy-flash agy@gemini-4-argon-medium=agy-argon &
wait
echo "finished $(date '+%F %T')" >> "$OUT/BATCH.md"
