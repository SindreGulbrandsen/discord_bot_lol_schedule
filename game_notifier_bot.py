import discord
import asyncio
import os
from datetime import datetime, timedelta
from scraper import fetch_matches

TOKEN = ''
CHANNEL_ID = 1252905510047322112  # Use the correct integer ID
NOTIFIED_MATCHES_FILE = "notified_matches.txt"
CHECK_INTERVAL = 300  # 5 minutes in seconds

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

def load_notified_matches():
    if not os.path.exists(NOTIFIED_MATCHES_FILE):
        return set()
    with open(NOTIFIED_MATCHES_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_notified_match(match_id):
    with open(NOTIFIED_MATCHES_FILE, "a") as f:
        f.write(match_id + "\n")

notified_matches = load_notified_matches()

async def check_matches():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    while not client.is_closed():
        matches = fetch_matches()
        for match in matches:
            team_left, team_right, league, datetime_string = match
            match_id = f"{team_left} vs {team_right} | {league} | {datetime_string}"
            if match_id not in notified_matches:
                try:
                    # Adjust datetime format here
                    match_time = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M')
                    current_time = datetime.now()
                    if 0 <= (match_time - current_time).total_seconds() <= 3600:
                        formatted_message = f"{team_left} vs {team_right}\nLeague: {league}\nTime: {datetime_string}"
                        await channel.send(formatted_message)
                        save_notified_match(match_id)
                        notified_matches.add(match_id)
                except ValueError as e:
                    print(f"Error parsing date '{datetime_string}': {e}")
        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')

@client.event
async def on_connect():
    print(f'Bot connected as {client.user.name}')

@client.event
async def on_disconnect():
    print(f'Bot disconnected as {client.user.name}')

async def main():
    async with client:
        client.loop.create_task(check_matches())
        await client.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
