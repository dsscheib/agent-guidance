#!/bin/sh
# The 2026-11-04 final suite (maintainer/EVALUATION.md), repository-only. Usage: final_suite.sh OUT_DIR
# Each provider runs its configurations one after another, in the order no guidance, old guidance (62d3756), final
# guidance, so a quota stop leaves complete comparisons behind it; providers run in parallel because their quotas are
# separate. run.py skips finished runs, so rerunning this script resumes where it stopped. It tests the guidance in
# this checkout: for the published suite, check out 85a4035 and keep the tree clean, because run.py snapshots it.
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:?usage: final_suite.sh OUT_DIR}
mkdir -p "$OUT"
RUN="python3 $REPO/maintainer/harness/run.py --out $OUT --workers 3"
NONE=S2,S3,S4,S5,S6,S7,S8,S9,S10,S12,S13,S14,S15,S17
OLD=S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,S15,S16,S17
FINAL=S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,S15,S16,S17,S18
VARIANTS=S2-prototype,S2-internal,S2-production,S2-enterprise,S6-prototype,S6-internal,S6-production,S6-enterprise
VARIANTS=$VARIANTS,S10-prototype,S10-internal,S10-production,S10-enterprise,S7-prototype,S7-internal,S7-production,S7-enterprise

config() {  # config AGENT NAME
    $RUN --agents "$1" --label "$2-none" --no-install --scenarios $NONE --runs 1,2,3
    $RUN --agents "$1" --label "$2-old" --old-guidance 62d3756 --scenarios $OLD --runs 1,2,3
    $RUN --agents "$1" --label "$2-final" --scenarios $FINAL --runs 1,2,3
    $RUN --agents "$1" --label "$2-final" --scenarios $VARIANTS --runs 1,2
}

provider() {  # provider NAME AGENT=LABEL...
    name=$1; shift
    for pair in "$@"; do
        config "${pair%%=*}" "${pair#*=}"
    done > "$OUT/progress-$name.log" 2>&1
}

[ -z "$(git -C "$REPO" status --porcelain)" ] || { echo "the guidance checkout is not clean" >&2; exit 1; }

provider antigravity agy@gemini-3.8-flash-medium=agy-flash agy@gemini-4-argon-medium=agy-argon &
provider codex codex@gpt-6.1-sol=codex-sol codex@gpt-6-luna=codex-luna &
provider copilot copilot@gpt-6.1-sol=copilot-sol copilot@gemini-3.8-flash=copilot-flash copilot@claude-sonnet-5.5=copilot-sonnet &
provider claude claude@claude-haiku-5-5=claude-haiku claude@claude-opus-5-5=claude-opus &
wait
echo "suite finished $(date '+%F %T')"
