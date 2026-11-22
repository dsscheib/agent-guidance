#!/usr/bin/env python3
"""Copilot CLI agentStop hook, loaded through .github/hooks/guidance.json.

Prompts the agent to apply AGENTS.md (Talk plainly and ask directly) when a register changed in the working tree
and the final reply asks nothing. The hook blocks that stop once so the agent can check if a decision still needs
the owner's input. Every other stop passes. Any error or missing data lets the stop through, like a hook timeout.

It can also run as a user-level hook from ~/.copilot/hooks/ (docs/AGENT_TOOLS.md), which covers sessions that
start before a project has the package. When both copies run for the same stop, the first claims it and the
other exits, so the agent is asked once.
"""
import json, os, re, subprocess, sys, tempfile, time

REGISTER = re.compile(r'(?i)(^|/)(OPEN_WORK|TODO[\w-]*|DECISIONS[\w-]*)\.md$')
WAIT_SECONDS = 3  # the reply reaches the transcript shortly after the hook starts
REASON = ('You changed open items in {files} and your reply asks no question. Check them against AGENTS.md '
          "(Talk plainly and ask directly). If an unresolved decision needs the owner's input, ask it directly "
          'and say what you completed meanwhile. If none needs their input, finish without adding a question.')


def changed_registers(cwd):
    out = subprocess.run(['git', '-C', cwd, 'status', '--porcelain', '--untracked-files=all'],
                         capture_output=True, text=True, timeout=5).stdout
    return sorted({line[3:].split(' -> ')[-1] for line in out.splitlines() if REGISTER.search(line[3:].split(' -> ')[-1])})


def final_reply(transcript):
    """The text of the turn's last assistant message without tool requests, or None if it has not arrived yet."""
    events = []
    with open(transcript) as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    last_user = max((i for i, e in enumerate(events) if e.get('type') == 'user.message'), default=-1)
    later = events[last_user + 1:]
    replies = [i for i, e in enumerate(later) if e.get('type') == 'assistant.message']
    if not replies:
        return None
    data = later[replies[-1]].get('data', {})
    tools_after = any(e.get('type', '').startswith('tool.') for e in later[replies[-1] + 1:])
    return None if data.get('toolRequests') or tools_after else data.get('content') or ''


def claim(data):
    """True for the first copy of this hook to see this stop; a repository and a user-level copy see the same event."""
    key = re.sub(r'\W', '_', f"{data.get('sessionId', '')}-{data.get('timestamp', '')}")
    try:
        os.close(os.open(os.path.join(tempfile.gettempdir(), f'copilot-guidance-stop-{key}'), os.O_CREAT | os.O_EXCL))
        return True
    except FileExistsError:
        return False


def main():
    data = json.load(sys.stdin)
    if data.get('stop_hook_active') or data.get('stopHookActive'):
        return
    files = changed_registers(data.get('cwd') or '.')
    transcript = data.get('transcriptPath') or data.get('transcript_path')
    if not files or not transcript:
        return
    deadline = time.monotonic() + WAIT_SECONDS
    reply = final_reply(transcript)
    while reply is None and time.monotonic() < deadline:
        time.sleep(0.25)
        reply = final_reply(transcript)
    if reply is None or '?' in reply or not claim(data):
        return
    print(json.dumps({'decision': 'block', 'reason': REASON.format(files=', '.join(files))}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pass  # fail open: a broken hook must never trap the agent
