import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# URL of the Liquipedia League of Legends matches page
URL = "https://liquipedia.net/leagueoflegends/Liquipedia:Matches"

# Time zone mappings
tz_mappings = {
    "CST": "Asia/Shanghai",  # China Standard Time
    "CT": "America/Chicago",  # Central Time
    "CEST": "Europe/Berlin",  # Central European Summer Time
}

# Local time zone
local_tz = pytz.timezone("Europe/Oslo")

# Define the leagues of interest
target_leagues = {"LEC", "LCS", "LPL", "LCK"}

def convert_to_local_time(datetime_str, tz_str):
    try:
        # Parse the datetime string and attach the time zone
        naive_dt = datetime.strptime(datetime_str, "%B %d, %Y - %H:%M")
        source_tz = pytz.timezone(tz_mappings.get(tz_str, "UTC"))
        source_dt = source_tz.localize(naive_dt)
        
        # Convert to local time
        local_dt = source_dt.astimezone(local_tz)
        return local_dt.strftime("%Y-%m-%d %H:%M"), local_dt
    except Exception as e:
        return f"Error converting date: {str(e)}", None

def fetch_matches():
    response = requests.get(URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table", class_="wikitable wikitable-striped infobox_matches_content")

    matches = []
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            team_left_cell = row.find("td", class_="team-left")
            team_right_cell = row.find("td", class_="team-right")

            if team_left_cell and team_right_cell:
                countdown_cell = row.find_next_sibling("tr").find("td", class_="match-filler")
                
                datetime_string = "Unknown date-time"
                local_datetime = None
                if countdown_cell:
                    datetime_span = countdown_cell.find("span", class_="timer-object timer-object-countdown-only")
                    if datetime_span:
                        datetime_string = datetime_span.text.strip()
                        datetime_parts = datetime_string.split()
                        if len(datetime_parts) == 6:
                            date_part = " ".join(datetime_parts[:3])
                            time_part = datetime_parts[4]
                            tz_part = datetime_parts[5]
                            datetime_full_str = f"{date_part} - {time_part}"
                            datetime_string, local_datetime = convert_to_local_time(datetime_full_str, tz_part)

                if local_datetime and (local_datetime - datetime.now(local_tz)).total_seconds() <= 3600:
                    team_left = team_left_cell.get_text(strip=True)
                    team_right = team_right_cell.get_text(strip=True)
                    next_row = row.find_next_sibling("tr")
                    league_cell = next_row.find("div", class_="tournament-text")
                    league = league_cell.find("a").get_text(strip=True) if league_cell else "Unknown League"

                    if any(league.startswith(tl) for tl in target_leagues) and all(substring not in league for substring in ["LCKA", "LCK CL"]):
                        matches.append((team_left, team_right, league, datetime_string))

    return matches
