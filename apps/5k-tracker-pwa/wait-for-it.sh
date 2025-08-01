#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available
#   Source: https://github.com/vishnubob/wait-for-it

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""
CMD=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -q|--quiet)
            QUIET=1
            shift
            ;;
        --)
            shift
            CMD="$@"
            break
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$HOST" || -z "$PORT" ]]; then
    echo "Usage: $0 -h host -p port [-t timeout] [-- command args]"
    exit 1
fi

for i in $(seq $TIMEOUT); do
    if nc -z "$HOST" "$PORT"; then
        if [[ $QUIET -ne 1 ]]; then
            echo "Host $HOST:$PORT is available after $i seconds."
        fi
        exec $CMD
        exit 0
    fi
    sleep 1
done

echo "Timeout after $TIMEOUT seconds waiting for $HOST:$PORT"
exit 1
