# team-portal

The owner's self-hosted portal for links and display preferences.

## Run

    python3 -m app.server

Then open http://127.0.0.1:8000.

## Review environment

    scripts/deploy-review.sh

## Current status

- Latest review deployment: `f09b1c3` on 2026-10-31 (deployment 14).
- Open: browser harness (OW-12), backup retention decision (OW-15), dark-theme contrast (OW-18).
- Tests: 22 passing on the latest deployment.

## Development
Run the tests with `python3 -m unittest`.

Agent instructions are in AGENTS.md.
