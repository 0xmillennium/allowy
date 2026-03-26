#!/bin/bash
set -e

trap 'kill -TERM "$SERVER_PID"; wait "$SERVER_PID"' TERM INT

allowy serve &
SERVER_PID=$!

until allowy health live 2>/dev/null; do sleep 1; done
allowy init run

wait "$SERVER_PID"
