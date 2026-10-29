#!/usr/bin/env python3
"""Copilot CLI preToolUse guardrail, loaded through .github/hooks/guidance.json.

Mirrors AGENTS.md rules 2, 3 and 9 as .claude/settings.json and .codex/rules/guidance.rules do:
remote and destructive git commands ask for confirmation, and .env files cannot be viewed.
Loosen only to match the agent git policy adopted in PROJECT_PROFILE.md.
Prints nothing, which keeps Copilot's normal permission flow, for every other tool call.
"""
import json, re, shlex, sys
from pathlib import PurePath

# (git subcommand prefix, reason); a command matches when its arguments start with the prefix.
ASK = [
    (['push'], 'AGENTS.md rule 3: push only with explicit authorization.'),
    (['reset', '--hard'], 'AGENTS.md rule 2: may discard uncommitted work.'),
    (['clean'], 'AGENTS.md rule 2: may delete untracked work.'),
    (['branch', '-D'], 'AGENTS.md rule 2: may delete unmerged work.'),
    (['rebase'], 'AGENTS.md rule 2: rewrites history.'),
    (['checkout', '--'], 'AGENTS.md rule 2: may discard uncommitted work.'),
]
SECRET = re.compile(r'^\.env(\..+\.local)?$')
SEPARATORS = re.compile(r'&&|\|\||[;|&\n()]')
GIT_OPTIONS_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace'}


def git_args(segment):
    """Arguments after `git` and its global options, or None when the segment is not a git command."""
    try:
        words = shlex.split(segment)
    except ValueError:
        words = segment.split()
    while words and re.match(r'^\w+=', words[0]):
        words.pop(0)
    if not words or PurePath(words[0]).name not in ('git', 'git.exe'):
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
            words = git_args(segment)
            for prefix, reason in ASK if words else []:
                if words[:len(prefix)] == prefix:
                    return {'permissionDecision': 'ask', 'permissionDecisionReason': reason}
    if tool == 'view' and SECRET.match(PurePath(str(args.get('path', ''))).name):
        return {'permissionDecision': 'deny', 'permissionDecisionReason': 'AGENTS.md rule 9: secret files are not readable.'}
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
