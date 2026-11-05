#!/bin/sh
# One-off recovery from a half-finished deployment on 2026-10-24: restored review/ from review.next.
[ -d review.next ] && mv review.next review
echo "recovered"
