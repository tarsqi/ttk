#!/bin/csh -f

set expression = $1

echo
echo

grep -n -e $expression *.py
grep -n -e $expression */*.py
grep -n -e $expression */*/*.py
grep -n -e $expression */*/*/*.py

echo


