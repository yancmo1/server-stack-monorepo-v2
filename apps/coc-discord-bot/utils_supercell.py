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

def get_current_cwl_war(clan_tag: str):
    """
    Fetch the current CWL war for the given clan tag from the Supercell API.
    Returns a dict with war data, or None if not available.
    """
    api_token = config.SUPERCELL_API_TOKEN
    if not api_token:
        return None
    tag = clan_tag.replace('#', '%23') if clan_tag.startswith('#') else clan_tag
    # Step 1: Get CWL group info
    group_url = f"https://api.clashofclans.com/v1/clans/{tag}/currentwar/leaguegroup"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        group_resp = requests.get(group_url, headers=headers, timeout=10)
        if group_resp.status_code != 200:
            return None
        group_data = group_resp.json()
        if 'rounds' not in group_data or 'state' not in group_data:
            return None
        # Find the current round (the last one with a warTag)
        current_war_tag = None
        for round in reversed(group_data['rounds']):
            for war_tag in round.get('warTags', []):
                if war_tag and war_tag != '#0':
                    current_war_tag = war_tag
                    break
            if current_war_tag:
                break
        if not current_war_tag:
            return None
        # Step 2: Get current war details
        war_tag_encoded = current_war_tag.replace('#', '%23')
        war_url = f"https://api.clashofclans.com/v1/clanwarleagues/wars/{war_tag_encoded}"
        war_resp = requests.get(war_url, headers=headers, timeout=10)
        if war_resp.status_code != 200:
            return None
        war_data = war_resp.json()
        # Add warTag to the data for reference
        war_data['warTag'] = current_war_tag
        return war_data
    except Exception:
        return None
