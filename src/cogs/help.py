import discord, sys
import asyncio
from discord.ext import commands
from discord.ext.commands import command
sys.path.append('../')
from config.ayarlar import *

class Help(commands.Cog, name="Yardım"):
    def __init__(self, bot):
        self.bot = bot

    async def music(self):
        pass
    
    async def general(self):
        pass

    async def game(self):
        pass

    async def moderation(self):
        pass

    async def information(self):
        pass

    async def owner(self):
        pass

    @property
    async def ownerCheck(author_id):
        if author_id == owner:
            return True
        else:
            return False

    @command(aliases=["help", "h", "hlp", "destek"])
    async def yardım(self, msg):
        emb = discord.Embed(color=msg.guild.me.color, description="[Komutlar](https://erdemusic.glitch.me/komutlar.html)\nKodlanıyor...")
        mesaj = await msg.send(embed=emb)
        await mesaj.add_reaction('\u23ee')  # çift sol
        await mesaj.add_reaction('\u25c0')  # sol
        await mesaj.add_reaction('\u25b6')  # sağ
        await mesaj.add_reaction('\u23ed')  # çift sağ

def setup(bot):
    bot.add_cog(Help(bot))