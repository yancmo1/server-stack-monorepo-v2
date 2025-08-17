#!/usr/bin/env python3
"""
List all users in the 5k-tracker Postgres database.

Usage (from project root):
  docker compose -f deploy/docker-compose.yml exec tracker python list_users.py

If you get ModuleNotFoundError, try:
  docker compose -f deploy/docker-compose.yml exec tracker bash
  python list_users.py
"""
from app import app, db, User
from tabulate import tabulate

with app.app_context():
    users = User.query.order_by(User.id).all()
    if not users:
        print("No users found.")
    else:
        table = [
            [u.id, u.username, u.email, u.first_name, u.last_name, u.created_at.strftime('%Y-%m-%d'), u.is_active]
            for u in users
        ]
        print(tabulate(table, headers=["ID", "Username", "Email", "First Name", "Last Name", "Created", "Active"], tablefmt="github"))
