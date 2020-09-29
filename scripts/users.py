import os
from pathlib import Path

import discord
import dotenv

env_path = Path('../.') / '.env'
dotenv.load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))

client = discord.Client()


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.id == GUILD:
            for member in guild.members:
                print(f"{member.name}\t{member.id}\t{member.nick}")

client.run(TOKEN)
