#!/bin/sh
# Run one agent command inside a bubblewrap sandbox (repository-only maintainer tooling).
#
# The agent gets a home folder of its own: SB_HOME, a folder for this run only, is mounted over the real home, so none
# of the maintainer's files are visible (finding 54: with only a list of hidden folders, agents printed the shell
# history, listed the home folder, and read the CLI's own history of earlier sessions). Into SB_HOME go, once per run:
#   - each CLI's sign-in file, copied (SB_SIGN_IN, relative to home; by default Claude Code's and Codex's), so the CLI
#     can authenticate without seeing the rest of its config folder, its sessions or the maintainer's settings;
#   - unless SB_TRUST=0, a .codex/config.toml that only trusts the fixture, so Codex loads the project's .codex/ layer
#     (rules and agents) as it does in a real, trusted project; Copilot is trusted through COPILOT_ALLOW_ALL in run.py;
#   - a .gitconfig with a scenario identity, so agents commit as "Scenario Agent", not as the maintainer, and with no
#     credential helper, so no git command reaches the maintainer's real remotes.
# The CLIs therefore run at their own defaults: user-level settings, plugins, skills, rules and MCP servers in the real
# home are not applied. The CLI keeps its sessions in SB_HOME, so a run's later steps can resume them; run.py deletes
# SB_HOME when the run ends.
#
# Inside, the agent sees the real filesystem read-only, its fixture (first argument) writable, SB_LOGDIR writable for
# CLI transcripts, SB_GUIDANCE (the guidance snapshot that S11 adopts from) read-only, SB_COPILOT_HOOKS read-only over
# ~/.copilot/hooks if set, and SB_TOOLS read-only at their own paths: the tool installs under home that PATH uses
# (defaults below; only those that exist are mounted). Keyrings, browser data and dotfiles are never among them.
# SB_HIDE lists folders outside home replaced by an empty tmpfs; folders under home are hidden by SB_HOME already.
# /tmp is a private tmpfs, so agents cannot see other runs. The run has its own process namespace: without it, /proc
# lists every process of the user, and their command lines (other runs' prompts, the harness's labels) are readable.
# The environment is cleared except for KEEP_ENV: agents run `env`, and a token in the caller's environment would land
# in the transcript and go to the model provider (finding 53).
#
# Usage: SB_HOME=DIR SB_LOGDIR=DIR SB_GUIDANCE=DIR sandbox.sh FIXTURE_DIR CMD [ARGS...]
set -eu
fix=$(realpath "$1"); shift
H=$HOME
[ -n "${SB_HOME:-}" ] || { echo "sandbox.sh: SB_HOME is required (a folder for this run's home)" >&2; exit 2; }
mkdir -p "$SB_HOME"
home=$(realpath "$SB_HOME")
[ "$home" = "$H" ] && { echo "sandbox.sh: SB_HOME must not be the real home" >&2; exit 2; }
for d in "$H/.claude" "$H/.codex" "$H/.copilot" "$H/.gemini" "$H/.config" "$H/.local"; do
  case "$home/" in "$d/"*) echo "sandbox.sh: SB_HOME must not be inside $d" >&2; exit 2 ;; esac
done
for f in ${SB_SIGN_IN-.claude/.credentials.json .codex/auth.json}; do
  if [ -f "$H/$f" ] && [ ! -e "$home/$f" ]; then
    mkdir -p "$(dirname "$home/$f")"
    cp -p "$H/$f" "$home/$f"
  fi
done
if [ "${SB_TRUST:-1}" = 1 ] && [ ! -e "$home/.codex/config.toml" ]; then
  mkdir -p "$home/.codex"
  printf '[projects."%s"]\ntrust_level = "trusted"\n' "$fix" > "$home/.codex/config.toml"
fi
if [ ! -e "$home/.gitconfig" ]; then
  printf '[user]\n\tname = Scenario Agent\n\temail = agent@example.invalid\n[init]\n\tdefaultBranch = main\n' > "$home/.gitconfig"
fi
binds=""  # Assumes paths without spaces.
for p in ${SB_TOOLS-$H/.local/bin $H/.local/share/mise $H/.config/mise $H/.local/share/uv $H/.local/share/pop-workstation $H/.cargo/bin $H/.rustup $H/go/bin}; do
  [ -e "$p" ] && binds="$binds --ro-bind $p $p"
done
# SB_COPILOT_HOOKS, if set, replaces ~/.copilot/hooks read-only for this run (user-level hook experiments).
[ -n "${SB_COPILOT_HOOKS:-}" ] && binds="$binds --ro-bind $SB_COPILOT_HOOKS $H/.copilot/hooks"
KEEP_ENV="PATH USER LOGNAME SHELL LANG LANGUAGE LC_ALL TERM TZ COPILOT_ALLOW_ALL"
# SB_KEYRING=1 exposes the session bus, and with it the user's keyring, which Copilot CLI and Antigravity sign in from.
# Every command the agent runs can then read keyring secrets such as the gh token, so it is off unless a CLI needs it.
[ "${SB_KEYRING:-}" = 1 ] && KEEP_ENV="$KEEP_ENV XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS"
envs=""
for v in $KEEP_ENV; do
  eval "val=\${$v-}"
  [ -n "$val" ] && envs="$envs --setenv $v $val"  # Assumes values without spaces, as these are.
done
hides=""
for p in ${SB_HIDE:-}; do
  case "$p/" in "$H/"*) continue ;; esac  # under home: already out of sight
  [ -d "$p" ] && hides="$hides --tmpfs $p"
done
run_dir="/run/user/$(id -u)"
# A read-only mount still lets processes connect to the sockets in it, so without SB_KEYRING the folder is hidden.
if [ -d "$run_dir" ]; then
  if [ "${SB_KEYRING:-}" = 1 ]; then binds="$binds --bind $run_dir $run_dir"; else binds="$binds --tmpfs $run_dir"; fi
fi
# shellcheck disable=SC2086  # $binds and $hides are lists of option words built above.
exec bwrap --die-with-parent --unshare-pid \
  --ro-bind / / --dev /dev --proc /proc \
  --tmpfs /tmp \
  $hides \
  --bind "$home" "$H" \
  $binds \
  --bind "$fix" "$fix" \
  --bind "$SB_LOGDIR" "$SB_LOGDIR" \
  --ro-bind "$SB_GUIDANCE" "$SB_GUIDANCE" \
  --clearenv $envs \
  --chdir "$fix" \
  --setenv HOME "$H" \
  "$@"
