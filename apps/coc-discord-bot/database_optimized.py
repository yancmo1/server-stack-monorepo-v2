"""
Optimized Database Operations
Enhanced database module with connection pooling and performance tracking
(PostgreSQL only)
"""

import os
import time
import logging
from datetime import datetime, timedelta
import platform
from typing import List, Dict, Any, Optional, Union
from performance_optimization import get_performance_optimizer, performance_decorator

# Only support Postgres
import psycopg2
import psycopg2.extras
import config
DB_TYPE = 'postgres'
DB_FILE = getattr(config, 'DB_PATH', None)

# Set up logger
logger = logging.getLogger(__name__)

print(f"[DATABASE] Using PostgreSQL database: {DB_FILE}")

# Initialize performance optimizer
_perf_optimizer = None

def get_optimized_connection():
    """Get optimized database connection from pool (Postgres only)"""
    global _perf_optimizer
    if _perf_optimizer is None:
        _perf_optimizer = get_performance_optimizer()
    # If performance optimizer is still None or doesn't have db_pool, fall back to regular connection
    if _perf_optimizer is None or not hasattr(_perf_optimizer, 'db_pool') or _perf_optimizer.db_pool is None:
        print(f"[DATABASE] Performance optimizer not available, using regular Postgres connection")
        return psycopg2.connect(config.DB_PATH, cursor_factory=psycopg2.extras.RealDictCursor)
    return _perf_optimizer.db_pool.get_connection()

def get_connection():
    """Legacy compatibility - use optimized connection (Postgres only)"""
    return get_optimized_connection()

@performance_decorator("database.get_player_data")
def get_player_data():
    """Get all player data with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_eligible_players")
def get_eligible_players():
    """Get all eligible players with optimized query"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM players 
            WHERE bonus_eligibility = 1 
            ORDER BY name
        """)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_ineligible_players")
def get_ineligible_players():
    """Get all ineligible players with optimized query"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM players 
            WHERE bonus_eligibility = 0 
            ORDER BY name
        """)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_player_by_name")
def get_player_by_name(player_name: str) -> Optional[Dict[str, Any]]:
    """Get player by name with case-insensitive search (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM players 
            WHERE LOWER(name) = LOWER(%s) 
            LIMIT 1
        """, (player_name,))
        row = cur.fetchone()
        return dict(row) if row else None

@performance_decorator("database.get_player_by_tag")
def get_player_by_tag(tag: str) -> Optional[Dict[str, Any]]:
    """Get a player by their CoC tag (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM players 
            WHERE LOWER(tag) = LOWER(%s) 
            LIMIT 1
        """, (tag,))
        row = cur.fetchone()
        return dict(row) if row else None

@performance_decorator("database.get_players_by_role")
def get_players_by_role(role: str) -> List[Dict[str, Any]]:
    """Get players by role (optimized with index)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM players 
            WHERE role = %s 
            ORDER BY name
        """, (role,))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_recent_bonus_recipients")
def get_recent_bonus_recipients(days: int = 30) -> List[Dict[str, Any]]:
    """Get players who received bonuses in the last N days (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT * FROM players 
            WHERE last_bonus_date >= %s
            ORDER BY last_bonus_date DESC, name
        """, (cutoff_date,))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_players_needing_bonuses")
def get_players_needing_bonuses(exclude_recent_days: int = 90) -> List[Dict[str, Any]]:
    """Get eligible players who haven't received bonuses recently (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=exclude_recent_days)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT * FROM players 
            WHERE bonus_eligibility = 1 
            AND (last_bonus_date IS NULL OR last_bonus_date < %s)
            ORDER BY 
                CASE WHEN last_bonus_date IS NULL THEN 0 ELSE 1 END,
                last_bonus_date ASC,
                bonus_count ASC,
                name
        """, (cutoff_date,))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.batch_add_players")
def batch_add_players(players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add multiple players in a single transaction (optimized)"""
    results = {'added': 0, 'updated': 0, 'errors': []}
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("BEGIN")
        try:
            for player_data in players_data:
                try:
                    # Remove id if present
                    player_data = {k: v for k, v in player_data.items() if k != 'id'}
                    # Check if player exists by tag or name (case-insensitive)
                    cur.execute("SELECT id FROM players WHERE LOWER(name) = LOWER(%s) OR LOWER(tag) = LOWER(%s)", (player_data['name'], player_data.get('tag', '')))
                    if cur.fetchone():
                        # Update existing player
                        update_fields = []
                        update_values = []
                        for field in ['tag', 'role', 'join_date', 'bonus_eligibility', 'bonus_count', 'last_bonus_date', 'missed_attacks', 'notes']:
                            if field in player_data:
                                update_fields.append(f"{field} = %s")
                                update_values.append(player_data[field])
                        if update_fields:
                            update_values.append(player_data['name'])
                            cur.execute(f"UPDATE players SET {', '.join(update_fields)} WHERE LOWER(name) = LOWER(%s)", update_values)
                            results['updated'] += 1
                    else:
                        # Insert new player (never specify id)
                        cur.execute(
                            """INSERT INTO players (name, tag, join_date, bonus_eligibility, bonus_count, last_bonus_date, missed_attacks, notes, role) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (tag) DO NOTHING""",
                            (
                                player_data['name'],
                                player_data.get('tag'),
                                player_data.get('join_date', datetime.now().strftime("%Y-%m-%d")),
                                bool(player_data.get('bonus_eligibility', 1)),
                                player_data.get('bonus_count', 0),
                                player_data.get('last_bonus_date'),
                                player_data.get('missed_attacks', 0),
                                player_data.get('notes'),
                                player_data.get('role')
                            )
                        )
                        results['added'] += 1
                except Exception as e:
                    results['errors'].append({'player': player_data.get('name', 'Unknown'), 'error': str(e)})
            conn.commit()
        except Exception as e:
            conn.rollback()
            results['errors'].append({'error': f"Transaction failed: {e}"})
    return results

@performance_decorator("database.get_eligibility_summary")
def get_eligibility_summary() -> Dict[str, Any]:
    """Get comprehensive eligibility summary (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Get counts by eligibility
        cur.execute("""
            SELECT bonus_eligibility, COUNT(*) as count
            FROM players 
            GROUP BY bonus_eligibility
        """)
        eligibility_counts = dict(cur.fetchall())
        
        # Get counts by role
        cur.execute("""
            SELECT role, COUNT(*) as count
            FROM players 
            GROUP BY role
            ORDER BY count DESC
        """)
        role_counts = dict(cur.fetchall())
        
        # Get recent activity
        cur.execute("""
            SELECT COUNT(*) as count
            FROM players 
            WHERE last_bonus_date >= date('now', '-30 days')
        """)
        recent_bonus_count = cur.fetchone()[0]
        
        # Get players with notes
        cur.execute("""
            SELECT COUNT(*) as count
            FROM players 
            WHERE notes IS NOT NULL AND notes != ''
        """)
        noted_players_count = cur.fetchone()[0]
        
        return {
            'total_players': sum(eligibility_counts.values()),
            'eligible_count': eligibility_counts.get(1, 0),
            'ineligible_count': eligibility_counts.get(0, 0),
            'role_breakdown': role_counts,
            'recent_bonus_recipients': recent_bonus_count,
            'players_with_notes': noted_players_count
        }

@performance_decorator("database.search_players")
def search_players(search_term: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
    """Search players by name, tag, or notes (optimized)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Build search query
        search_pattern = f"%{search_term}%"
        base_query = """
            SELECT * FROM players 
            WHERE (
                LOWER(name) LIKE LOWER(%s) OR 
                LOWER(tag) LIKE LOWER(%s) OR 
                LOWER(notes) LIKE LOWER(%s)
            )
        """
        
        params = [search_pattern, search_pattern, search_pattern]
        
        if not include_inactive:
            base_query += " AND bonus_eligibility = 1"
        
        base_query += " ORDER BY name"
        
        cur.execute(base_query, params)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_autocomplete_names")
def get_autocomplete_names(prefix: str = "") -> List[str]:
    """Get player names for autocomplete (optimized with limit)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        if prefix:
            cur.execute("""
                SELECT name FROM players 
                WHERE LOWER(name) LIKE LOWER(%s) 
                ORDER BY name 
                LIMIT 25
            """, (f"{prefix}%",))
        else:
            cur.execute("""
                SELECT name FROM players 
                ORDER BY name 
                LIMIT 25
            """)
        return [row[0] for row in cur.fetchall()]

# Enhanced operations for better performance
@performance_decorator("database.add_player")
def add_player(
    name,
    tag=None,
    join_date=None,
    bonus_eligibility=1,
    bonus_count=0,
    last_bonus_date=None,
    missed_attacks=0,
    notes=None,
    role=None,
    location=None,
    latitude=None,
    longitude=None,
    favorite_troop=None,
    **kwargs  # ignore extra keys like id
):
    """Add player with performance tracking"""
    import logging
    logger = logging.getLogger("add_player_debug")
    # Ensure bonus_eligibility is a boolean
    bonus_eligibility = bool(bonus_eligibility)
    logger.debug(f"Attempting to add player: name={name}, tag={tag}, join_date={join_date}, bonus_eligibility={bonus_eligibility}, bonus_count={bonus_count}, last_bonus_date={last_bonus_date}, missed_attacks={missed_attacks}, notes={notes}, role={role}, location={location}, latitude={latitude}, longitude={longitude}, favorite_troop={favorite_troop}")
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        sql = (
            """INSERT INTO players (name, tag, join_date, bonus_eligibility, 
               bonus_count, last_bonus_date, missed_attacks, notes, role,
               location, latitude, longitude, favorite_troop) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (tag) DO NOTHING
            """
        )
        values = (
            name,
            tag,
            join_date or datetime.now().strftime("%Y-%m-%d"),
            bonus_eligibility,
            bonus_count,
            last_bonus_date,
            missed_attacks,
            notes,
            role,
            location or "Unknown",
            latitude,
            longitude,
            favorite_troop,
        )
        try:
            cur.execute(sql, values)
            conn.commit()
            logger.info(f"[DATABASE] Added player: {name} ({tag})")
            return True, "Player added successfully"
        except Exception as e:
            logger.error(f"[DATABASE][ERROR] Failed to add player {name} ({tag}): {e}")
            logger.error(f"[DATABASE][ERROR] Values: {values}")
            return False, f"Database error: {e}"
    """Increment bonus count with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET bonus_count = COALESCE(bonus_count, 0) + 1 WHERE LOWER(name) = LOWER(%s)",
            (player_name,),
        )
        conn.commit()

@performance_decorator("database.update_bonus_date")
def update_bonus_date(player_name, date_str):
    """Update bonus date with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET last_bonus_date = %s WHERE LOWER(name) = LOWER(%s)",
            (date_str, player_name),
        )
        conn.commit()

@performance_decorator("database.award_player_bonus")
def award_player_bonus(player_name, awarded_by=None, player_tag=None, bonus_type='CWL', notes=None):
    """Award bonus to player (combined operation for better performance)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        current_date = datetime.now().strftime("%Y-%m-%d")
        cur.execute("BEGIN")
        try:
            # Update player record
            cur.execute("""
                UPDATE players 
                SET bonus_count = COALESCE(bonus_count, 0) + 1,
                    last_bonus_date = %s
                WHERE LOWER(name) = LOWER(%s)
            """, (current_date, player_name))
            # Add to bonus history (use correct columns)
            cur.execute("""
                INSERT INTO bonus_history (player_name, player_tag, awarded_date, awarded_by, bonus_type, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (player_name, player_tag, current_date, awarded_by, bonus_type, notes))
            conn.commit()
            return True, "Bonus awarded successfully"
        except Exception as e:
            conn.rollback()
            return False, f"Database error: {e}"

@performance_decorator("database.get_bonus_history")
def get_bonus_history(limit: int = 100):
    """Get bonus history with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT player_name, awarded_date, awarded_by 
            FROM bonus_history 
            ORDER BY awarded_date DESC, id DESC 
            LIMIT %s
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.update_player_eligibility")
def update_player_eligibility(player_name, is_eligible, notes=None):
    """Update player eligibility with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        if notes is not None:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s, notes = %s WHERE LOWER(name) = LOWER(%s)",
                (1 if is_eligible else 0, notes, player_name),
            )
        else:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s WHERE LOWER(name) = LOWER(%s)",
                (1 if is_eligible else 0, player_name),
            )
        conn.commit()

@performance_decorator("database.toggle_player_eligibility")
def toggle_player_eligibility(player_name, notes=None):
    """Toggle player eligibility with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        # Get current eligibility status
        cur.execute(
            "SELECT bonus_eligibility FROM players WHERE LOWER(name) = LOWER(%s)",
            (player_name,)
        )
        row = cur.fetchone()
        if not row:
            return False, "Player not found"
        
        current_eligibility = row[0]
        new_eligibility = 0 if current_eligibility else 1
        
        # Update eligibility and optionally notes
        if notes is not None:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s, notes = %s WHERE LOWER(name) = LOWER(%s)",
                (new_eligibility, notes, player_name)
            )
        else:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s WHERE LOWER(name) = LOWER(%s)",
                (new_eligibility, player_name)
            )
        
        conn.commit()
        status = "eligible" if new_eligibility else "ineligible"
        return True, f"Player is now {status}"

@performance_decorator("database.set_player_eligibility")
def set_player_eligibility(player_name, eligible, notes=None):
    """Set player eligibility with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        eligibility_value = 1 if eligible else 0
        
        if notes is not None:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s, notes = %s WHERE LOWER(name) = LOWER(%s)",
                (eligibility_value, notes, player_name)
            )
        else:
            cur.execute(
                "UPDATE players SET bonus_eligibility = %s WHERE LOWER(name) = LOWER(%s)",
                (eligibility_value, player_name)
            )
        
        if cur.rowcount == 0:
            return False, "Player not found"
        
        conn.commit()
        status = "eligible" if eligible else "ineligible"
        return True, f"Player set to {status}"

@performance_decorator("database.update_player_notes")
def update_player_notes(player_name, notes):
    """Update player notes with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET notes = %s WHERE LOWER(name) = LOWER(%s)",
            (notes, player_name)
        )
        
        if cur.rowcount == 0:
            return False, "Player not found"
        
        conn.commit()
        return True, "Notes updated successfully"

@performance_decorator("database.set_discord_coc_link")
def set_discord_coc_link(discord_id, coc_name_or_tag):
    """Set Discord-CoC link with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Delete any existing link for this Discord ID
        cur.execute("DELETE FROM discord_coc_links WHERE discord_id = %s", (discord_id,))
        
        # Insert new link
        cur.execute(
            "INSERT INTO discord_coc_links (discord_id, coc_name_or_tag) VALUES (%s, %s)",
            (discord_id, coc_name_or_tag)
        )
        conn.commit()

@performance_decorator("database.get_coc_link_for_discord")
def get_coc_link_for_discord(discord_id):
    """Get CoC link for Discord user with performance tracking"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT coc_name_or_tag FROM discord_coc_links WHERE discord_id = %s",
            (discord_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None

# Additional functions for Discord-CoC linking and role management
@performance_decorator("database.get_coc_name_by_discord_id")
def get_coc_name_by_discord_id(discord_id):
    """Returns the CoC name or tag linked to the given Discord user ID"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT coc_name_or_tag FROM discord_coc_links WHERE discord_id = %s",
            (str(discord_id),),
        )
        row = cur.fetchone()
        return row[0] if row else None

@performance_decorator("database.get_clan_role_by_coc_name_or_tag")
def get_clan_role_by_coc_name_or_tag(coc_name_or_tag):
    """Returns the clan role for a given CoC name or tag"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT role FROM players WHERE LOWER(name) = LOWER(%s) OR LOWER(tag) = LOWER(%s)",
            (coc_name_or_tag, coc_name_or_tag),
        )
        row = cur.fetchone()
        return row[0] if row else None

@performance_decorator("database.get_all_discord_coc_links_with_roles")
def get_all_discord_coc_links_with_roles():
    """Returns all Discord-CoC links with clan roles"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT dcl.discord_id, dcl.coc_name_or_tag, p.role
            FROM discord_coc_links dcl
            LEFT JOIN players p ON LOWER(dcl.coc_name_or_tag) = LOWER(p.name) 
                                OR LOWER(dcl.coc_name_or_tag) = LOWER(p.tag)
        """)
        return cur.fetchall()

@performance_decorator("database.update_player_role")
def update_player_role(tag, role):
    """Update player role by tag"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE players SET role = %s WHERE tag = %s", (role, tag))
        conn.commit()

# Database health and maintenance
@performance_decorator("database.analyze_performance")
def analyze_database_performance() -> Dict[str, Any]:
    """Analyze database performance and provide recommendations"""
    global _perf_optimizer
    if _perf_optimizer is None:
        _perf_optimizer = get_performance_optimizer()
    
    # Get performance report from optimizer (with null check)
    perf_report = {}
    optimization_results = {}
    pool_stats = {}
    
    if _perf_optimizer and hasattr(_perf_optimizer, 'get_performance_report'):
        perf_report = _perf_optimizer.get_performance_report(hours=24)
    
    # Run database optimization (with null check)
    if _perf_optimizer and hasattr(_perf_optimizer, 'optimize_database_queries'):
        optimization_results = _perf_optimizer.optimize_database_queries()
    
    # Get pool stats (with null check)
    if _perf_optimizer and hasattr(_perf_optimizer, 'db_pool') and _perf_optimizer.db_pool:
        pool_stats = _perf_optimizer.db_pool.get_pool_stats()
    
    # Get database statistics
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Table statistics (PostgreSQL version)
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        table_stats = {}
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            table_stats[table] = count
        
        # Index usage statistics
        cur.execute("PRAGMA index_list(players)")
        indexes = [row[1] for row in cur.fetchall()]
        
        return {
            'performance_report': perf_report,
            'optimization_results': optimization_results,
            'table_statistics': table_stats,
            'database_indexes': indexes,
            'database_file': DB_FILE,
            'connection_pool_stats': pool_stats
        }

def cleanup_database_connections():
    """Cleanup database connections on shutdown"""
    global _perf_optimizer
    if _perf_optimizer:
        _perf_optimizer.db_pool.close_all()
        _perf_optimizer = None

# Performance monitoring context manager
class PerformanceContext:
    """Context manager for tracking custom operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
        else:
            duration_ms = 0
        success = exc_type is None
        
        global _perf_optimizer
        if _perf_optimizer:
            _perf_optimizer.track_operation(
                self.operation_name, 
                duration_ms, 
                success,
                {'error': str(exc_val)} if exc_val else {}
            )

@performance_decorator("database.mark_cwl_non_participants")
def mark_cwl_non_participants(player_tags):
    """Mark players as CWL non-participants by setting eligibility to 0"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        conn.execute("BEGIN TRANSACTION")
        
        try:
            for tag in player_tags:
                cur.execute(
                    "UPDATE players SET bonus_eligibility = 0, notes = %s WHERE tag = %s",
                    ("CWL non-participant", tag)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

# =====================================
# CWL ACTIVE STATUS MANAGEMENT FUNCTIONS  
# =====================================
# These functions manage CWL war rotation participation (separate from bonus eligibility)

@performance_decorator("database.set_player_active_status")
def set_player_active_status(player_name, is_active, notes=None):
    """Set player active status for CWL war rotation participation"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        inactive_value = 0 if is_active else 1  # inactive field is boolean: 0=active, 1=inactive
        
        if notes is not None:
            cur.execute(
                "UPDATE players SET inactive = %s, notes = %s WHERE LOWER(name) = LOWER(%s)",
                (inactive_value, notes, player_name)
            )
        else:
            cur.execute(
                "UPDATE players SET inactive = %s WHERE LOWER(name) = LOWER(%s)",
                (inactive_value, player_name)
            )
        
        if cur.rowcount == 0:
            return False, "Player not found"
        
        conn.commit()
        status = "active" if is_active else "inactive"
        return True, f"Player CWL participation status set to {status}"

@performance_decorator("database.toggle_player_active_status")
def toggle_player_active_status(player_name):
    """Toggle player active status for CWL war rotation participation"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Get current status
        cur.execute(
            "SELECT inactive FROM players WHERE LOWER(name) = LOWER(%s)",
            (player_name,)
        )
        result = cur.fetchone()
        
        if not result:
            return False, "Player not found"
        
        current_inactive = result[0] or 0  # Default to 0 (active) if None
        new_inactive = 1 - current_inactive  # Toggle: 0->1, 1->0
        
        cur.execute(
            "UPDATE players SET inactive = %s WHERE LOWER(name) = LOWER(%s)",
            (new_inactive, player_name)
        )
        
        conn.commit()
        new_status = "inactive" if new_inactive else "active"
        return True, f"Player CWL participation status toggled to {new_status}"

@performance_decorator("database.get_active_players")
def get_active_players():
    """Get all players marked as active for CWL war rotation participation"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        # Get players where inactive is 0 or NULL (active)
        cur.execute("""
            SELECT * FROM players 
            WHERE (inactive = 0 OR inactive IS NULL)
            ORDER BY name
        """)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_inactive_players")
def get_inactive_players():
    """Get all players marked as inactive for CWL war rotation participation"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        # Get players where inactive is 1
        cur.execute("""
            SELECT * FROM players 
            WHERE inactive = 1 
            ORDER BY name
        """)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.reset_all_active_status")
def reset_all_active_status():
    """Reset all players to active status for new CWL season (monthly reset)"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Get count of players that will be affected
        cur.execute("SELECT COUNT(*) FROM players WHERE inactive = 1")
        inactive_count = cur.fetchone()[0]
        
        # Reset all players to active (inactive = 0)
        cur.execute("UPDATE players SET inactive = 0")
        conn.commit()
        
        return inactive_count

@performance_decorator("database.get_cwl_active_status_summary")
def get_cwl_active_status_summary():
    """Get summary of CWL active status for all players"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Get counts
        cur.execute("SELECT COUNT(*) FROM players WHERE (inactive = 0 OR inactive IS NULL)")
        active_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM players WHERE inactive = 1")
        inactive_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM players")
        total_count = cur.fetchone()[0]
        
        return {
            'total_players': total_count,
            'active_players': active_count,
            'inactive_players': inactive_count
        }

@performance_decorator("database.auto_reactivate_player")
def auto_reactivate_player(player_name):
    """Automatically reactivate a player who participated without missing attacks"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Check if player exists and is currently inactive
        cur.execute(
            "SELECT inactive FROM players WHERE LOWER(name) = LOWER(%s)",
            (player_name,)
        )
        result = cur.fetchone()
        
        if not result:
            return False, "Player not found"
        
        if not result[0]:  # Player is already active
            return False, "Player is already active"
        
        # Reactivate the player
        cur.execute(
            "UPDATE players SET inactive = 0 WHERE LOWER(name) = LOWER(%s)",
            (player_name,)
        )
        
        conn.commit()
        return True, f"Player {player_name} automatically reactivated for CWL participation"

# Location management functions for clan-map integration

@performance_decorator("database.update_player_location")
def update_player_location(player_name, location, latitude=None, longitude=None, favorite_troop=None):
    """Update player location data for clan-map integration"""
    from datetime import datetime
    
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Update location fields
        cur.execute("""
            UPDATE players SET 
                location = ?, 
                latitude = ?, 
                longitude = ?, 
                favorite_troop = ?,
                location_updated = ?
            WHERE LOWER(name) = LOWER(?)
        """, (
            location or "Unknown",
            latitude,
            longitude,
            favorite_troop,
            datetime.now().isoformat(),
            player_name
        ))
        
        if cur.rowcount == 0:
            return False, "Player not found"
        
        conn.commit()
        return True, f"Location updated for {player_name}"

@performance_decorator("database.get_players_with_locations")
def get_players_with_locations():
    """Get all players with their location data for clan-map"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, role, location, latitude, longitude, favorite_troop, location_updated, tag
            FROM players 
            WHERE name IS NOT NULL AND name != ''
            ORDER BY name
        """)
        
        players = []
        for row in cur.fetchall():
            name, role, location, latitude, longitude, favorite_troop, location_updated, tag = row
            player = {
                'name': name,
                'role': role or 'Member',
                'location': location or 'Unknown',
                'tag': tag
            }
            
            if latitude is not None and longitude is not None:
                player['latitude'] = latitude
                player['longitude'] = longitude
            
            if favorite_troop:
                player['favorite_troop'] = favorite_troop
            
            if location_updated:
                player['location_updated'] = location_updated
                
            players.append(player)
        
        return players

@performance_decorator("database.get_players_needing_location")
def get_players_needing_location():
    """Get players who don't have location data set"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, role, tag
            FROM players 
            WHERE name IS NOT NULL AND name != ''
            AND (location IS NULL OR location = 'Unknown' OR latitude IS NULL OR longitude IS NULL)
            ORDER BY name
        """)
        
        return [{'name': row[0], 'role': row[1] or 'Member', 'tag': row[2]} for row in cur.fetchall()]

# CWL Stars functions
@performance_decorator("database.update_cwl_stars")
def update_cwl_stars(player_name, player_tag, stars_earned, new_total, round_num, war_date):
    """Update player's CWL stars and record history"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Update player's total stars
        cur.execute("UPDATE players SET cwl_stars = %s WHERE LOWER(name) = LOWER(%s)", (new_total, player_name))
        
        # Record history in cwl_stars_history table if it exists
        try:
            cur.execute("""
                INSERT INTO cwl_stars_history 
                (player_name, player_tag, stars_earned, total_stars, round_num, war_date, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (player_name, player_tag, stars_earned, new_total, round_num, war_date))
        except psycopg2.Error:
            # Table doesn't exist or other database error, that's okay
            pass
        
        conn.commit()

@performance_decorator("database.has_recorded_war_stars")
def has_recorded_war_stars(player_name, round_num, war_date):
    """Check if we've already recorded stars for this player in this war"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) FROM cwl_stars_history 
                WHERE LOWER(player_name) = LOWER(%s) AND round_num = %s AND war_date = %s
            """, (player_name, round_num, war_date))
            result = cur.fetchone()
            return result[0] > 0 if result else False
        except psycopg2.Error:
            # Table doesn't exist, assume not recorded
            return False

@performance_decorator("database.get_player_star_history")
def get_player_star_history(player_name):
    """Get CWL star history for a specific player"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT stars_earned, total_stars, round_num, war_date, timestamp
                FROM cwl_stars_history 
                WHERE LOWER(player_name) = LOWER(%s)
                ORDER BY timestamp DESC
            """, (player_name,))
            return [dict(row) for row in cur.fetchall()]
        except psycopg2.Error:
            # Table doesn't exist
            return []

@performance_decorator("database.get_all_players_with_stars")
def get_all_players_with_stars():
    """Get all players with their CWL stars"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, cwl_stars, missed_attacks FROM players WHERE active = 1 ORDER BY cwl_stars DESC, name")
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.reset_all_cwl_stars")
def reset_all_cwl_stars():
    """Reset all CWL stars to zero for a new season"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE players SET cwl_stars = 0")
        conn.commit()
        return cur.rowcount

# CWL missed attacks automation functions
@performance_decorator("database.add_missed_attack_record")
def add_missed_attack_record(player_tag, player_name, war_tag, round_num, date_processed):
    """Add a record of a missed attack to prevent duplicate processing"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missed_attacks_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_tag TEXT NOT NULL,
                player_name TEXT NOT NULL,
                war_tag TEXT NOT NULL,
                round_num INTEGER NOT NULL,
                date_processed TEXT NOT NULL,
                UNIQUE(player_tag, war_tag)
            )
        """)
        
        # Insert the record (ignore if duplicate)
        cur.execute("""
            INSERT OR IGNORE INTO missed_attacks_history 
            (player_tag, player_name, war_tag, round_num, date_processed)
            VALUES (%s, %s, %s, %s, %s)
        """, (player_tag, player_name, war_tag, round_num, date_processed))
        conn.commit()
        return cur.rowcount > 0  # Returns True if new record was inserted

@performance_decorator("database.check_missed_attack_processed")
def check_missed_attack_processed(player_tag, war_tag):
    """Check if a missed attack has already been processed for this player and war"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 1 FROM missed_attacks_history 
            WHERE player_tag = %s AND war_tag = %s
        """, (player_tag, war_tag))
        return cur.fetchone() is not None

@performance_decorator("database.get_missed_attacks_summary")
def get_missed_attacks_summary(limit=20):
    """Get recent missed attacks history"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT player_name, war_tag, round_num, date_processed
            FROM missed_attacks_history 
            ORDER BY date_processed DESC 
            LIMIT %s
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.reset_all_missed_attacks")
def reset_all_missed_attacks():
    """Reset all missed attack counters to 0"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE players SET missed_attacks = 0")
        conn.commit()
        return cur.rowcount

@performance_decorator("database.update_player_missed_attacks_by_tag")
def update_player_missed_attacks_by_tag(tag: str, count: int):
    """Update missed attacks by player tag with a specific count"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET missed_attacks = %s WHERE LOWER(tag) = LOWER(%s)",
            (count, tag),
        )
        conn.commit()
        return cur.rowcount

# CWL Season Summary Functions
@performance_decorator("database.get_cwl_season_summary")
def get_cwl_season_summary(year=None, month=None):
    """Get CWL season summary for a specific year and month"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        if year and month:
            # Query for specific year and month
            date_pattern = f"{year}-{month:02d}-%"
            cur.execute("""
                SELECT 
                    strftime('%Y', date_processed) as season_year,
                    strftime('%m', date_processed) as season_month,
                    COUNT(DISTINCT player_name) as total_players,
                    COUNT(*) as total_missed_attacks,
                    CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT player_name) as avg_missed_attacks,
                    COUNT(*) as max_missed_attacks,
                    MIN(date_processed) as reset_date
                FROM missed_attacks_history 
                WHERE date_processed LIKE %s
                GROUP BY strftime('%Y-%m', date_processed)
                ORDER BY date_processed DESC
            """, (date_pattern,))
        else:
            # Query for all seasons if no filter
            cur.execute("""
                SELECT 
                    strftime('%Y', date_processed) as season_year,
                    strftime('%m', date_processed) as season_month,
                    COUNT(DISTINCT player_name) as total_players,
                    COUNT(*) as total_missed_attacks,
                    CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT player_name) as avg_missed_attacks,
                    COUNT(*) as max_missed_attacks,
                    MIN(date_processed) as reset_date
                FROM missed_attacks_history 
                GROUP BY strftime('%Y-%m', date_processed)
                ORDER BY date_processed DESC
                LIMIT 12
            """)
        
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_cwl_history")
def get_cwl_history(year=None, month=None, player_name=None, limit=20):
    """Get CWL history for a specific player in a season"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Build query based on filters
        conditions = []
        params = []
        
        if year and month:
            date_pattern = f"{year}-{month:02d}-%"
            conditions.append("date_processed LIKE %s")
            params.append(date_pattern)
        
        if player_name:
            conditions.append("LOWER(player_name) = LOWER(%s)")
            params.append(player_name)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        cur.execute(f"""
            SELECT 
                player_name,
                1 as missed_attacks,
                strftime('%Y', date_processed) as season_year,
                strftime('%m', date_processed) as season_month,
                date_processed as reset_date
            FROM missed_attacks_history
            WHERE {where_clause}
            ORDER BY date_processed DESC
            LIMIT %s
        """, params)
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.get_player_cwl_history")
def get_player_cwl_history(player_name, limit=10):
    """Get overall CWL history for a player across all seasons"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                player_name,
                COUNT(*) as missed_attacks,
                strftime('%Y', date_processed) as season_year,
                strftime('%m', date_processed) as season_month,
                MIN(date_processed) as first_missed,
                MAX(date_processed) as last_missed
            FROM missed_attacks_history
            WHERE LOWER(player_name) = LOWER(%s)
            GROUP BY strftime('%Y-%m', date_processed)
            ORDER BY season_year DESC, season_month DESC
            LIMIT %s
        """, (player_name, limit))
        return [dict(row) for row in cur.fetchall()]

@performance_decorator("database.clear_missed_attacks_history_for_month")
def clear_missed_attacks_history_for_month(year, month):
    """Clear missed attack history for a specific month (but preserve other months)
    
    This function removes:
    1. All missed_attacks_history entries for the specified month
    2. All war_attacks entries for the specified month
    
    This allows the automation to reprocess wars for that month.
    """
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        date_pattern = f"{year}-{month:02d}-%"
        
        # Clear missed_attacks_history for this month
        cur.execute("""
            DELETE FROM missed_attacks_history 
            WHERE date_processed LIKE %s
        """, (date_pattern,))
        history_deleted = cur.rowcount
        
        # Clear war_attacks for this month (based on war_date)
        cur.execute("""
            DELETE FROM war_attacks 
            WHERE date(war_date) LIKE %s
        """, (date_pattern,))
        attacks_deleted = cur.rowcount
        
        conn.commit()
        
        return {
            'history_deleted': history_deleted,
            'attacks_deleted': attacks_deleted,
            'total_deleted': history_deleted + attacks_deleted
        }

@performance_decorator("database.initialize_database")
def initialize_database():
    """Initialize database and create all required tables"""
    print("[DATABASE] Initializing database and creating tables...")
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Create missed_attacks_history table (Postgres compatible)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missed_attacks_history (
                id SERIAL PRIMARY KEY,
                player_tag TEXT NOT NULL,
                player_name TEXT NOT NULL,
                war_tag TEXT NOT NULL,
                round_num INTEGER NOT NULL,
                date_processed TEXT NOT NULL,
                UNIQUE(player_tag, war_tag)
            )
        """)
        conn.commit()
        print("[DATABASE] Database initialization complete")

@performance_decorator("database.save_cwl_season_snapshot")
def save_cwl_season_snapshot(season_year=None, season_month=None):
    """Save current CWL stats as historical snapshot before reset"""
    from datetime import datetime
    
    if not season_year or not season_month:
        now = datetime.now()
        season_year = now.year
        season_month = now.month
    
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Create cwl_history table if it doesn't exist (for PostgreSQL)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cwl_history (
                id SERIAL PRIMARY KEY,
                season_year INTEGER NOT NULL,
                season_month INTEGER NOT NULL,
                reset_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                player_name TEXT NOT NULL,
                player_tag TEXT,
                cwl_stars INTEGER NOT NULL DEFAULT 0,
                missed_attacks INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get all players with CWL activity (stars > 0 or missed attacks > 0)
        cur.execute("""
            SELECT name, tag, COALESCE(cwl_stars, 0) as cwl_stars, COALESCE(missed_attacks, 0) as missed_attacks
            FROM players 
            WHERE active = 1 AND (COALESCE(cwl_stars, 0) > 0 OR COALESCE(missed_attacks, 0) > 0)
        """)
        
        players_data = cur.fetchall()
        saved_count = 0
        
        # Save each player's season stats to history
        for player in players_data:
            cur.execute("""
                INSERT INTO cwl_history 
                (season_year, season_month, reset_date, player_name, player_tag, cwl_stars, missed_attacks)
                VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (season_year, season_month, player[0], player[1], player[2], player[3]))
            saved_count += 1
        
        conn.commit()
        
        return {
            'season_year': season_year,
            'season_month': season_month,
            'players_saved': saved_count,
            'total_stars': sum(p[2] for p in players_data),
            'total_missed': sum(p[3] for p in players_data)
        }

@performance_decorator("database.get_cwl_season_history")
def get_cwl_season_history(season_year=None, season_month=None, limit=50):
    """Get CWL season history"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        try:
            if season_year and season_month:
                cur.execute("""
                    SELECT player_name, cwl_stars, missed_attacks, reset_date
                    FROM cwl_history 
                    WHERE season_year = %s AND season_month = %s
                    ORDER BY cwl_stars DESC, player_name ASC
                    LIMIT %s
                """, (season_year, season_month, limit))
            else:
                cur.execute("""
                    SELECT season_year, season_month, player_name, cwl_stars, missed_attacks, reset_date
                    FROM cwl_history 
                    ORDER BY reset_date DESC, cwl_stars DESC
                    LIMIT %s
                """, (limit,))
            
            results = cur.fetchall()
            if not results:
                return []
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.warning(f"Error getting CWL season history: {e}")
            return []

@performance_decorator("database.get_player_cwl_season_history")
def get_player_cwl_season_history(player_name, limit=10):
    """Get CWL season history for a specific player"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT season_year, season_month, cwl_stars, missed_attacks, reset_date
                FROM cwl_history 
                WHERE LOWER(player_name) = LOWER(%s)
                ORDER BY reset_date DESC
                LIMIT %s
            """, (player_name, limit))
            
            results = cur.fetchall()
            if not results:
                return []
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.warning(f"Error getting player CWL season history for {player_name}: {e}")
            return []

@performance_decorator("database.clear_all_cwl_history")
def clear_all_cwl_history():
    """Clear all CWL history and reset missed attacks to zero for a fresh start"""
    with get_optimized_connection() as conn:
        cur = conn.cursor()
        
        # Count current state
        cur.execute("SELECT COUNT(*) FROM players WHERE missed_attacks > 0")
        result = cur.fetchone()
        players_with_missed = result[0] if result else 0
        
        cur.execute("SELECT COALESCE(SUM(missed_attacks), 0) FROM players")
        result = cur.fetchone()
        total_missed = result[0] if result else 0
        
        try:
            cur.execute("SELECT COUNT(*) FROM missed_attacks_history")
            result = cur.fetchone()
            history_count = result[0] if result else 0
        except:
            history_count = 0
        
        # Clear all history tables
        try:
            cur.execute("DELETE FROM missed_attacks_history")
            deleted_history = cur.rowcount
        except:
            deleted_history = 0
        
        # Reset all missed attacks
        cur.execute("UPDATE players SET missed_attacks = 0 WHERE missed_attacks > 0")
        reset_count = cur.rowcount
        
        conn.commit()
        
        return {
            'players_with_missed_before': players_with_missed,
            'total_missed_before': total_missed,
            'history_records_deleted': deleted_history,
            'players_reset': reset_count
        }

# Export the performance context for external use
__all__ = [
    # Database connections
    'get_connection',
    'get_optimized_connection',
    
    # New CWL History Functions
    'save_cwl_season_snapshot',
    'get_cwl_season_history', 
    'get_player_cwl_season_history',
    
    # Existing CWL functions
    'get_cwl_history',
    'get_player_cwl_history',
    'reset_all_cwl_stars',
    'reset_all_missed_attacks',
]

