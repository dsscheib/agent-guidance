#!/bin/sh
# One-off probe used on 2026-10-23 to check the review server answered after deployment 5.
curl -fsS http://127.0.0.1:8001/ >/dev/null && echo "review up"
