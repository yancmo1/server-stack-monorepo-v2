import requests
import config
from datetime import datetime

def get_player_clan_history(player_tag: str):
    """
    Fetch the last 5 clans and days in each for a player from the Supercell API.
    Returns a list of dicts: [{clan_name, join_date, leave_date, days_in_clan}]
    """
    api_token = config.SUPERCELL_API_TOKEN
    if not api_token:
        return []
    tag = player_tag.replace('#', '%23') if player_tag.startswith('#') else player_tag
    url = f"https://api.clashofclans.com/v1/players/{tag}"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if 'clan' not in data or 'clanHistory' not in data:
            return []
        history = data['clanHistory'][-5:][::-1]  # last 5, most recent first
        result = []
        for c in history:
            join = c.get('joinTime')
            leave = c.get('leaveTime')
            clan_name = c.get('name', 'Unknown')
            try:
                join_dt = datetime.strptime(join[:10], '%Y-%m-%d') if join else None
                leave_dt = datetime.strptime(leave[:10], '%Y-%m-%d') if leave else None
                days = (leave_dt - join_dt).days if join_dt and leave_dt else 0
            except Exception:
                days = 0
            result.append({
                'clan_name': clan_name,
                'join_date': join[:10] if join else '',
                'leave_date': leave[:10] if leave else 'Now',
                'days_in_clan': days
            })
        return result
    except Exception:
        return []
