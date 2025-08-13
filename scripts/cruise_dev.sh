#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/docker-compose.dev.yml"
SERVICE="cruise-price-check"

usage() {
  cat <<EOF
cruise_dev.sh <command>

Commands:
  up         Start (or recreate) cruise-price-check service
  build      Build image only
  rebuild    Build and force recreate service
  logs       Stream logs
  down       Stop service container
  shell      Exec into running container
  check      Run one-off price check inside container
  summary    Run summary (7 days) inside container

Examples:
  ./scripts/cruise_dev.sh up
  ./scripts/cruise_dev.sh rebuild
  ./scripts/cruise_dev.sh logs
  ./scripts/cruise_dev.sh check
EOF
}

cmd=${1:-help}

case "$cmd" in
  up)
    docker compose -f "$COMPOSE_FILE" up -d $SERVICE
    ;;
  build)
    docker compose -f "$COMPOSE_FILE" build $SERVICE
    ;;
  rebuild)
    docker compose -f "$COMPOSE_FILE" build $SERVICE
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate $SERVICE
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f $SERVICE
    ;;
  down)
    docker compose -f "$COMPOSE_FILE" stop $SERVICE || true
    ;;
  shell)
    docker compose -f "$COMPOSE_FILE" exec $SERVICE bash || true
    ;;
  check)
    docker compose -f "$COMPOSE_FILE" exec $SERVICE python improved_price_tracker.py --check
    ;;
  summary)
    docker compose -f "$COMPOSE_FILE" exec $SERVICE python improved_price_tracker.py --summary --history 7
    ;;
  *)
    usage
    ;;
esac
