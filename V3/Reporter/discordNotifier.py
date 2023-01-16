from discord.ext import commands
from datetime import datetime
import discord
import asyncio
import sys

# Append the 'Config Files' folder to path and import the needed module
sys.path.append('Config Files')
import config

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='$', intents=intents)

async def generateEmbed(asset, asset_type, flag, type, amount, multiplier, price):
    embed = discord.Embed(
        title='New Transaction',
        description=f"```Asset: {asset}\nAsset Type: {asset_type}\nAsset Flag: {flag}\nOrder Type: {type}\nTrade Size: ${amount}\nMultiplier: {multiplier}x\nAsset Price: ${price}```",
        color=discord.Color.from_rgb(0, 153, 255)
    )
    # embed.set_image(url='Program Files/Images/discord_message_wallpaper.gif')
    now = datetime.now()
    embed.timestamp = datetime.fromisoformat(now.isoformat())
    # embed.set_footer(text='Vulcan Asset Management | vam.network', icon_url='Program Files/Images/discord_message_icon.png')
    return embed

@client.event
async def on_ready():
    # Update the bot's presence to indicate that it is watching the Market
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='the Market'))
    # Fetch all signals from the database
    allSignals = config.get_signals()['data']
    oldSignals = []
    # Add all signals to the oldSignals list
    for key in allSignals.keys():
        signal = allSignals[key]
        if signal not in oldSignals:
            oldSignals.append(signal)
    # Continuously check for new signals
    while True:
        allSignals = config.get_signals()['data']
        for key in allSignals.keys():
            signal = allSignals[key]            
            # If a new signal is found, add it to the oldSignals list and send the signal to the user's discord channel
            if signal not in oldSignals:
                oldSignals.append(signal)
                # Convert the signal data from a string to a JSON object
                signal_data = config.string_to_json(signal[0]['signal'])['data']
                # Get the api_key of the user associated with the signal
                signal_api_key = signal[0]['api_key']
                # Fetch all users from the database
                users = config.get_users()['data']
                for user in users:
                    # If the user's api_key matches the signal's api_key and they have at least 18 discord channels
                    if users[user][0]['api_key'] == signal_api_key and len(users[user][0]['discord_channels']) >= 18:
                        # Get the discord channel id
                        channel_id = int(users[user][0]['discord_channels'])
                        channel = client.get_channel(channel_id)
                        # Send the signal data to the discord channel in the form of an embed
                        await channel.send(
                            embed = await generateEmbed(
                                signal_data['asset_data']['asset_name'], 
                                signal_data['asset_data']['asset_type'], 
                                signal_data['flag'], 
                                signal_data['order_type'], 
                                signal_data['asset_data']['amount'], 
                                signal_data['asset_data']['multiplier'], 
                                signal_data['asset_data']['asset_price']
                            )
                        )
        # Sleep for 5 seconds before checking for new signals again
        await asyncio.sleep(5)

client.run(config.api_keys['discord'])
