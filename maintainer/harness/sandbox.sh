#!/bin/sh
# Run one agent command inside a bubblewrap sandbox (repository-only maintainer tooling).
#
# The whole filesystem is read-only except:
#   - the fixture directory (first argument), where the agent works,
#   - SB_LOGDIR, where the agent CLI may write transcripts,
#   - each agent CLI's own config and session folders, so it can authenticate and resume sessions.
# SB_GUIDANCE (the guidance snapshot that S11 adopts from) is bound read-only, and so is SB_COPILOT_HOOKS if set.
# /tmp is a private tmpfs, so agents cannot see other runs. ~/.ssh is hidden and SSH_AUTH_SOCK unset, so no run can
# reach a real server over SSH, even from a copy of a project whose scripts deploy that way.
# The environment is cleared except for KEEP_ENV: agents run `env`, and a token in the caller's environment would land
# in the transcript and go to the model provider (finding 53).
#
# Usage: SB_LOGDIR=DIR SB_GUIDANCE=DIR sandbox.sh FIXTURE_DIR CMD [ARGS...]
set -eu
fix=$(realpath "$1"); shift
H=$HOME
binds=""  # Assumes config paths without spaces.
for p in "$H/.claude" "$H/.claude.json" "$H/.codex" "$H/.copilot" "$H/.config/github-copilot" "$H/.gemini" "$H/.cache"; do
  [ -e "$p" ] && binds="$binds --bind $p $p"
done
# SB_COPILOT_HOOKS, if set, replaces ~/.copilot/hooks read-only for this run (user-level hook experiments).
[ -n "${SB_COPILOT_HOOKS:-}" ] && binds="$binds --ro-bind $SB_COPILOT_HOOKS $H/.copilot/hooks"
KEEP_ENV="PATH USER LOGNAME SHELL LANG LANGUAGE LC_ALL TERM TZ COPILOT_ALLOW_ALL"
# SB_KEYRING=1 exposes the session bus, and with it the user's keyring, which Copilot CLI signs in from. Every command
# the agent runs can then read keyring secrets such as the gh token, so it is off unless a CLI needs it.
[ "${SB_KEYRING:-}" = 1 ] && KEEP_ENV="$KEEP_ENV XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS"
envs=""
for v in $KEEP_ENV; do
  eval "val=\${$v-}"
  [ -n "$val" ] && envs="$envs --setenv $v $val"  # Assumes values without spaces, as these are.
done
run_dir="/run/user/$(id -u)"
# A read-only mount still lets processes connect to the sockets in it, so without SB_KEYRING the folder is hidden.
if [ -d "$run_dir" ]; then
  if [ "${SB_KEYRING:-}" = 1 ]; then binds="$binds --bind $run_dir $run_dir"; else binds="$binds --tmpfs $run_dir"; fi
fi
# shellcheck disable=SC2086  # $binds is a list of option words built above.
exec bwrap --die-with-parent \
  --ro-bind / / --dev /dev --proc /proc \
  --tmpfs /tmp \
  --bind "$fix" "$fix" \
  --bind "$SB_LOGDIR" "$SB_LOGDIR" \
  --ro-bind "$SB_GUIDANCE" "$SB_GUIDANCE" \
  $binds \
  --tmpfs "$H/.ssh" \
  --clearenv $envs \
  --chdir "$fix" \
  --setenv HOME "$H" \
  "$@"
