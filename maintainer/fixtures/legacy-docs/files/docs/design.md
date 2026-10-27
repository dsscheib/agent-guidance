# wc-cli design

wc-cli counts lines, words and characters in one text file or standard input and
prints `LINES WORDS CHARS PATH`. Scripts parse that output, so its format is a
compatibility contract (decision D-1).
