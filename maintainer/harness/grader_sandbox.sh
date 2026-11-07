#!/bin/sh
# Run a holdout grader (a model CLI, or a shell for a human) in a bubblewrap sandbox (repository-only).
#
# Usage: [GR_RO="PATH ..."] [GR_HIDE="DIR ..."] grader_sandbox.sh GRADER_HOME MATERIAL_DIR SHEET_DIR CMD [ARGS...]
#
# Unlike sandbox.sh, the whole home folder is replaced by GRADER_HOME, a fresh folder for this grader only. sandbox.sh
# mounts each CLI's real config folder (~/.claude, ~/.codex, ...) so agents can sign in, and those folders keep every
# earlier session, including the scenario runs, whose paths name the condition. Here a grader sees none of them: put
# only the CLI's sign-in file in GRADER_HOME (for Claude Code, ~/.claude/.credentials.json -> GRADER_HOME/.claude/;
# for Codex, ~/.codex/auth.json -> GRADER_HOME/.codex/), never a copied config folder, history or ~/.claude.json.
# The sign-in file is a live credential: delete it from GRADER_HOME when grading ends. Keep the rest of GRADER_HOME,
# which holds the grader's own session logs.
#
# Inside, HOME is the real home path, and the grader sees:
#   ~/material  MATERIAL_DIR, read-only: this grader's copy of the blinded runs, the rubric and the protocol's Grading section
#   ~/sheet     SHEET_DIR, writable: this grader's blank sheet, and nothing else
#   GR_RO       extra paths mounted read-only at their own place, for CLIs installed under home (e.g. ~/.local/bin)
# GR_RO must not name a CLI config folder, which holds earlier sessions. GR_HIDE lists folders outside home to replace
# with empty mounts, such as a results folder kept elsewhere. /tmp and /run/user are private, so other sessions' scratch
# files and sockets are out of reach, and the grader has its own process namespace: without it, /proc lists every
# process of the user, and their command lines (another grader's folders, a blinding run's seed) are readable. The environment is cleared
# except for KEEP_ENV. The network stays on, since a model grader needs its provider.
set -eu
[ $# -ge 4 ] || { sed -n '4p' "$0" >&2; exit 2; }
gh=$(realpath "$1"); mat=$(realpath "$2"); sheet=$(realpath "$3"); shift 3
H=$HOME
for d in "$gh" "$mat" "$sheet"; do [ -d "$d" ] || { echo "not a folder: $d" >&2; exit 2; }; done
[ "$gh" = "$H" ] && { echo "GRADER_HOME must be a fresh folder, not your home" >&2; exit 2; }
for d in "$H/.claude" "$H/.codex" "$H/.gemini" "$H/.copilot"; do
  case "$gh/" in "$d/"*) echo "GRADER_HOME must not be inside $d" >&2; exit 2 ;; esac
done
ro=""
for p in ${GR_RO:-}; do
  [ -e "$p" ] || { echo "GR_RO path not found: $p" >&2; exit 2; }
  for d in "$H/.claude" "$H/.claude.json" "$H/.codex" "$H/.gemini" "$H/.copilot" "$H/.config/github-copilot"; do
    case "$(realpath "$p")/" in "$d/"*) echo "GR_RO must not include $d: it holds earlier sessions" >&2; exit 2 ;; esac
  done
  ro="$ro --ro-bind $p $p"  # Assumes paths without spaces.
done
hides=""
for p in ${GR_HIDE:-}; do
  [ -d "$p" ] && hides="$hides --tmpfs $p"
done
KEEP_ENV="PATH USER LOGNAME SHELL LANG LANGUAGE LC_ALL TERM TZ COLORTERM"
envs=""
for v in $KEEP_ENV; do
  eval "val=\${$v-}"
  [ -n "$val" ] && envs="$envs --setenv $v $val"
done
run_dir="/run/user/$(id -u)"
[ -d "$run_dir" ] && hides="$hides --tmpfs $run_dir"
# shellcheck disable=SC2086  # $hides, $ro and $envs are lists of option words built above.
exec bwrap --die-with-parent --unshare-pid \
  --ro-bind / / --dev /dev --proc /proc \
  --tmpfs /tmp \
  $hides \
  --bind "$gh" "$H" \
  $ro \
  --ro-bind "$mat" "$H/material" \
  --bind "$sheet" "$H/sheet" \
  --clearenv $envs \
  --setenv HOME "$H" \
  --chdir "$H" \
  "$@"
