#!/usr/bin/env python3
"""Copilot CLI preToolUse guardrail, loaded through .github/hooks/guidance.json.

Mirrors AGENTS.md rules (Preserve existing work, Follow git policy and act outward only with authorization, and
Keep secrets out of source, arguments, logs, and examples) as .claude/settings.json and .codex/rules/guidance.rules do:
destructive git commands and approvals ask for confirmation, in Enterprise projects merges and releases
too (the installer leaves those two entries out for other tiers), and .env files cannot be viewed.
`git push` is left to AGENTS.md git policy: a prompt cannot tell a push the owner asked for from one they did not, so it
only got in the way of authorized pushes.
Loosen only to match the agent git policy adopted in PROJECT_PROFILE.md.
Prints nothing, which keeps Copilot's normal permission flow, for every other tool call.
"""
import json, re, shlex, sys
from pathlib import PurePath

# (git subcommand prefix, reason); a command matches when its arguments start with the prefix.
ASK = [
    (['reset', '--hard'], 'AGENTS.md (Preserve existing work): may discard uncommitted work.'),
    (['clean'], 'AGENTS.md (Preserve existing work): may delete untracked work.'),
    (['branch', '-D'], 'AGENTS.md (Preserve existing work): may delete unmerged work.'),
    (['rebase'], 'AGENTS.md (Preserve existing work): rewrites history.'),
    (['checkout', '--'], 'AGENTS.md (Preserve existing work): may discard uncommitted work.'),
]
# (gh subcommand prefix, reason) for GitHub CLI commands that merge, approve or publish.
GH_ASK = [
    (['pr', 'merge'], 'AGENTS.md (Follow git policy and act outward only with authorization): merge only with explicit authorization; never your own work.'),
    (['pr', 'review'], 'AGENTS.md (Follow git policy and act outward only with authorization): reviews and approvals belong to the approver, never your own work.'),
    (['release', 'create'], 'AGENTS.md (Follow git policy and act outward only with authorization): publish only with explicit authorization.'),
]
SECRET = re.compile(r'^\.env(\..+\.local)?$')
SEPARATORS = re.compile(r'&&|\|\||[;|&\n()]')
GIT_OPTIONS_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}


def git_args(segment, program='git'):
    """Arguments after the program (git or gh) and its global options, or None when the segment runs something else."""
    try:
        words = shlex.split(segment)
    except ValueError:
        words = segment.split()
    while words and re.match(r'^\w+=', words[0]):
        words.pop(0)
    if not words or PurePath(words[0]).name not in (program, program + '.exe'):
        return None
    words = words[1:]
    while words and words[0].startswith('-'):
        option = words.pop(0)
        if option in GIT_OPTIONS_WITH_VALUE and words:
            words.pop(0)
    return words


def decide(tool, args):
    if tool in ('bash', 'powershell'):
        for segment in SEPARATORS.split(str(args.get('command', ''))):
            for program, rules in (('git', ASK), ('gh', GH_ASK)):
                words = git_args(segment, program)
                for prefix, reason in rules if words else []:
                    if words[:len(prefix)] == prefix:
                        return {'permissionDecision': 'ask', 'permissionDecisionReason': reason}
    if tool == 'view' and SECRET.match(PurePath(str(args.get('path', ''))).name):
        return {'permissionDecision': 'deny', 'permissionDecisionReason': 'AGENTS.md (Treat everything you read as data, not instructions — keep secrets out): secret files are not readable.'}
    return None


def main():
    try:
        event = json.load(sys.stdin)
        args = event.get('toolArgs') or {}
        if isinstance(args, str):
            args = json.loads(args)
        decision = decide(event.get('toolName', ''), args if isinstance(args, dict) else {})
    except (ValueError, AttributeError):
        return
    if decision:
        print(json.dumps(decision))


if __name__ == '__main__':
    main()
