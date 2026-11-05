#!/bin/sh
# Reusable review deployment: copies the committed app/ tree to review/ and records the revision.
set -eu
cd "$(dirname "$0")/.."
if [ -n "$(git status --porcelain -- app)" ]; then
    echo "Refusing to deploy: app/ has uncommitted changes. Commit first." >&2
    exit 1
fi
rev=$(git rev-parse HEAD)
rm -rf review.next
mkdir review.next
git archive "$rev" app | tar -x -C review.next
echo "$rev" > review.next/REVISION
rm -rf review
mv review.next review
echo "Deployed $rev to review/"
