#!/usr/bin/env sh

# Be eXplicit about which programs are running
# Helps with debugging.
set -x

EXIT_CODE=0

for FILE in scripts/*.py
do
    uvx --with-requirements "$FILE" pytest "$FILE";
    STATUS=$?
    if ! [ $STATUS -eq 5 ] && ! [ $STATUS -eq 0 ]
    then
        EXIT_CODE=$STATUS
    fi
done

exit $EXIT_CODE
