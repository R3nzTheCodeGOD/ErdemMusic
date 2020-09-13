import discord,asyncio,youtube_dl
from discord.ext import commands
import os
import aiohttp
import sys
sys.path.append('./')
from config.ayarlar import *


def get_prefix(bot, msg):
    prefixes = [prefix]
    return commands.when_mentioned_or(*prefixes)(bot, msg)

bot=commands.Bot(command_prefix=get_prefix)
bot.remove_command('help')

exts=['src.cogs.müzik', 'src.cogs.genel', 'src.cogs.help']

@bot.event
async def on_ready():
    status=f'{prefix}yardım | Beta v0.29' 
    activity_type=discord.ActivityType.listening
    await bot.change_presence(activity=discord.Activity(type=activity_type,name=status), status=discord.Status.online)
    print(f"Bot Giriş Kimliği: {bot.user.name}")
    count = 1
    print("Botun Bulunduğu Sunucular;")
    for guild in bot.guilds:
        print(f"{count}= {guild}")
        count += 1

@bot.event
async def on_guild_join(guild):
    channel = bot.get_channel(MainGuildChannel)
    e = discord.Embed(title="Sunucuya Eklendim", colour=Yeşil)
    e.set_author(name=bot.user.name, icon_url=bot.user.avatar_url)
    e.set_footer(text=Footer)
    e.set_thumbnail(url=guild.icon_url)
    e.add_field(name="`Sunucu Bilgileri`", value=f"Sunucu Adı: `{guild.name}`\n"f"Sunucu Kurucusu: `{guild.owner}`")
    return await channel.send(embed=e)

@bot.event
async def on_guild_remove(guild):
    channel = bot.get_channel(MainGuildChannel)
    e = discord.Embed(title="Sunucudan Çıkarıldım", colour=Kırmızı)
    e.set_author(name=bot.user.name, icon_url=bot.user.avatar_url)
    e.set_footer(text=Footer)
    e.set_thumbnail(url=guild.icon_url)
    e.add_field(name="`Sunucu Bilgileri`", value=f"Sunucu Adı: `{guild.name}`\n"f"Sunucu Kurucusu: `{guild.owner}`")
    return await channel.send(embed=e)

@bot.event
async def on_message(message):
    guild = bot.get_guild(MainGuild)
    channel = bot.get_channel(MainGuildChannel)
    if message.channel.type == discord.ChannelType.private:
        if message.author.id != bot.user.id:
            e = discord.Embed(title="DmLog", color=guild.me.color, description=f"```{message.content}```")
            e.set_footer(text=Footer)
            e.set_author(name=message.author, icon_url=message.author.avatar_url)  
            e.timestamp = message.created_at
            return await channel.send(embed=e)
    await bot.process_commands(message)

for i in exts:
    bot.load_extension(i)

bot.run(quadroon)
