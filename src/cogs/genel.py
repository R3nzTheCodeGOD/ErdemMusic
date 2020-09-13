from config.ayarlar import *
import discord
import asyncio
import aiohttp
import random
import datetime
import textblob
import sys
from discord.ext import commands
from discord.ext.commands import command
from discord import Webhook, AsyncWebhookAdapter
sys.path.append('../')


class General(commands.Cog, name="Genel"):
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=["pp", "a"])
    async def avatar(self, ctx, user: discord.User = None):
        if user is None:
            user = ctx.message.author

        avatar = user.avatar_url_as(static_format="png", size=1024)
        e = discord.Embed(
            description=f"Avatar Sahibi: `{user}`\nAvatar Linki: [{user.name}]({avatar})", colour=ctx.guild.me.color)
        e.set_image(url=avatar)
        e.set_footer(text=Footer)
        e.set_author(name=self.bot.user.name,
                     icon_url=self.bot.user.avatar_url)
        e.timestamp = ctx.message.created_at
        await ctx.send(embed=e)

    @command()
    async def ping(self, ctx):
        msg = await ctx.send("**Ping Hesaplanıyor :** `□□□□□□□□□□`")
        await asyncio.sleep(0.3)
        await msg.edit(content="**Ping Hesaplanıyor :** `■■□□□□□□□□`")
        await asyncio.sleep(0.3)
        await msg.edit(content="**Ping Hesaplanıyor :** `■■■■□□□□□□`")
        await asyncio.sleep(0.3)
        await msg.edit(content="**Ping Hesaplanıyor :** `■■■■■■□□□□`")
        await asyncio.sleep(0.3)
        await msg.edit(content="**Ping Hesaplanıyor :** `■■■■■■■■□□`")
        await asyncio.sleep(0.3)
        await msg.edit(content="**Ping Hesaplanıyor :** `■■■■■■■■■■`")
        await asyncio.sleep(0.3)
        await msg.delete()
        e = discord.Embed(colour=ctx.guild.me.color,
                          description=f"Ping Değeri: `{round(self.bot.latency * 1000)}ms`")
        e.set_author(name=self.bot.user.name,
                     icon_url=self.bot.user.avatar_url)
        e.set_footer(text=Footer)
        e.timestamp = ctx.message.created_at
        await ctx.send(embed=e)

    @command(aliases=["kullanıcıbilgi", "kbilgi", "bilgilerim"])
    async def info(self, ctx, *users: discord.Member):
        try:
            if len(users) == 0:
                users = [ctx.message.author]
            guild = ctx.message.guild
            for user in users:
                msg = f":id:: `{user.id}`\n\n"
                if user.nick:
                    msg += f":name_badge: **Takma Adı**: `{user.nick}`\n\n"
                if not user.bot:
                    msg += ":robot: **Bot**: `Hayır`\n\n"
                elif user.bot:
                    msg += ":robot: **Bot**: `Evet`\n\n"
                msg += f":inbox_tray: **Sunucuya Katılma Tarihi**: \n__{user.joined_at.strftime('%d/%m/%Y %H:%M:%S')}__\n\n"
                msg += f":globe_with_meridians: **Discorda Katılma Tarihi**: \n__{user.created_at.strftime('%d/%m/%Y %H:%M:%S')}__\n\n"
                msg += f":information_source: **Durum**: `{str(user.status).upper()}`\n\n"
                if user.activity:
                    msg += f":joystick: **Oynuyor**: `{user.activity.name}`\n\n"
                if user.voice:
                    msg += f":microphone2: **Bulunduğu Ses Kanalı**: `{user.voice.channel.name}`\n\n"
                msg += ":shield: **Rolleri**:{0} - `{1}`\n\n".format(
                    len(user.roles), ", ".join([role.name for role in user.roles]))
                e = discord.Embed(title=f"👤 {user}",
                                  colour=user.color, description=msg)
                e.set_footer(text=Footer)
                e.set_thumbnail(url=user.avatar_url)
                e.timestamp = ctx.message.created_at
                await ctx.send(embed=e)
        except Exception as err:
            await ctx.send(f"Bir Hata Meydana Geldi Hata:\n```{err}```")

    @command(aliases=["sununucubilgi", "server"])
    async def sunucu(self, ctx):
        try:
            guild = ctx.message.guild
            msg = f":id: `{guild.id}`\n\n"
            msg += f":bust_in_silhouette: **Sahip**: {guild.owner.mention}\n\n"
            msg += f":map: **Server Konumu**: `{str(guild.region).upper()}`\n\n"
            msg += f":calendar_spiral: **Oluşturulma Tarihi**: \n__{guild.created_at.strftime('%d/%m/%Y %H:%M:%S')}__\n\n"
            msg += f":busts_in_silhouette: **Üye Sayısı**: `{guild.member_count}`\n\n"
            if guild.verification_level:
                msg += f":exclamation: **Güvenlik Seviyesi**: `{str(guild.verification_level).upper()}`\n\n"
            if guild.system_channel:
                msg += f":speech_balloon: **Sistem Kanalı**: {guild.system_channel}\n\n"
            if guild.afk_channel:
                msg += f":telephone_receiver: **Afk Kanalı**: `{guild.afk_channel}`\n\n"
                msg += f":keyboard: **Afk Düşme Zamanı**: `{str(int(int(guild.afk_timeout) / 60))}`\n\n"
            msg += f":arrow_forward: **Kanallar**: Ses:`{len(guild.voice_channels)}`|Yazı: `{len(guild.text_channels)}`|Toplam: `{int(len(guild.voice_channels)) + int(len(guild.text_channels))}`\n\n"
            msg += f":arrow_forward: **Roller**: `{len(guild.roles)}`\n\n"
            msg2 = ""
            msg2 = msg
            page = False
            if len(guild.emojis) != 0:
                emotes = ""
                for emoji in guild.emojis:
                    emotes += str(emoji)
                msg2 += f":arrow_forward: **Emojiler**: {emotes}\n\n"
                if len(msg2) <= 2048:
                    msg += f":arrow_forward: **Emojiler**: {emotes}\n\n"

                elif len(msg2) >= 2048:
                    page = True
                    page2 = f":arrow_forward: **Emojiler**: {emotes}\n\n"

            e = discord.Embed(
                title=f":desktop: {guild.name}", colour=ctx.guild.me.color, description=msg)
            e.set_footer(text=Footer)
            e.set_thumbnail(url=guild.icon_url)
            e.timestamp = ctx.message.created_at
            embed = await ctx.send(embed=e)
            if page == True:
                e2 = discord.Embed(
                    title=f":desktop: {guild.name}", color=siyah, description=page2)
                e2.set_footer(text=Footer)
                e2.timestamp = ctx.message.created_at
                await embed.add_reaction('\u25c0')  # Sol
                await embed.add_reaction('\u25b6')  # Sağ
                pages = [e, e2]  # indexler "0, 1"
                i = 0
                click = ""
                while True:
                    if click == '\u25c0':
                        if i > 0:
                            i -= 1
                            await embed.edit(embed=pages[i])
                    elif click == '\u25b6':
                        if i < 1:
                            i += 1
                            await embed.edit(embed=pages[i])

                    res = await self.bot.wait_for('reaction_add', timeout=60)
                    if res == None:
                        break
                    if res[1].id == ctx.author.id:
                        click = str(res[0].emoji)

        except Exception as err:
            print(err)

    @command(aliases=["sayıtahmin", "oyna", "game"])
    @commands.cooldown(1, 500)
    async def tahmin(self, ctx):
        try:
            await ctx.message.delete()
            channel = ctx.message.channel
            bilgi = discord.Embed(title="Sayı Tahmin", color=ctx.guild.me.color,
                                  description=f"Merhaba `{ctx.message.author.name}` Hazırsan Başlıyalım.\nOyuna Başlamak için sohbete `başla` yaz `20` saniyen var.")
            bilgi.set_author(name=self.bot.user.name,
                             icon_url=self.bot.user.avatar_url)
            bilgi.set_footer(text=Footer)
            msg = await ctx.send(embed=bilgi, delete_after=20)

            try:
                wait = await self.bot.wait_for("message", timeout=20)
            except asyncio.TimeoutError:
                await ctx.send(f"{ctx.author.mention} Süren Doldu Oyun İptal Edildi.", delete_after=10)
                ctx.command.reset_cooldown(ctx)
                await ctx.message.delete()

            if wait.author != ctx.message.author:
                pass
            elif wait.author == ctx.message.author:
                if wait.content != "başla":
                    await ctx.send(f"{ctx.author.mention} `başla` yazmadıgın için oyun iptal edildi.", delete_after=10)
                    ctx.command.reset_cooldown(ctx)

                elif wait.content == "başla" and wait.channel == channel:
                    await asyncio.sleep(0.3)
                    await wait.delete()
                    await msg.delete()
                    hak = 10
                    sayı = random.randint(1, 50)
                    print(f"Tutulan Sayı: {sayı}")
                    embed = discord.Embed(title="Sayı Tahmin", color=ctx.guild.me.color,
                                          description=f"**Sayı Aralığı**: `1-50`Arasında\n**Belirlenen Hak**: `{hak}`\n**Her Tahmin İçin Beklenecek Süre**: `60sn`\n__**Hadi Tahmin Etmeye Başla**__")
                    embed.set_author(name=ctx.author.name,
                                     icon_url=ctx.author.avatar_url)
                    embed.set_footer(text=Footer)
                    emebed = await ctx.send(embed=embed)

                    try:
                        while hak > 0:
                            tahmin = await self.bot.wait_for("message", timeout=60)
                            if tahmin.author != ctx.message.author:
                                pass

                            elif tahmin.author == ctx.message.author:
                                if int(tahmin.content) <= 50 and int(tahmin.content) >= 1:
                                    if int(tahmin.content) < sayı:
                                        await asyncio.sleep(0.3)
                                        await tahmin.delete()
                                        hak -= 1
                                        doldur = f":arrow_up: `Yukarı`\n:envelope_with_arrow: **Gönderdigin Sayı**: `{int(tahmin.content)}`"
                                        hesap = discord.Embed(
                                            title=f"Kalan Hak: {hak}", color=ctx.guild.me.color, description=doldur)
                                        hesap.set_author(
                                            name=ctx.author.name, icon_url=ctx.author.avatar_url)
                                        hesap.set_footer(text=Footer)
                                        await emebed.edit(embed=hesap)
                                        continue

                                    elif int(tahmin.content) > sayı:
                                        await asyncio.sleep(0.3)
                                        await tahmin.delete()
                                        hak -= 1
                                        doldur = f":arrow_down: `Aşagı`\n:envelope_with_arrow: **Gönderdigin Sayı**: `{int(tahmin.content)}`"
                                        hesap = discord.Embed(
                                            title=f"Kalan Hak: {hak}", color=ctx.guild.me.color, description=doldur)
                                        hesap.set_author(
                                            name=ctx.author.name, icon_url=ctx.author.avatar_url)
                                        hesap.set_footer(text=Footer)
                                        await emebed.edit(embed=hesap)
                                        continue

                                    elif int(tahmin.content) == sayı:
                                        await asyncio.sleep(0.3)
                                        await tahmin.delete()
                                        await asyncio.sleep(0.1)
                                        await emebed.delete()
                                        hak -= 1
                                        hesap = discord.Embed(
                                            title=f"Tebrikler {tahmin.author.name}", color=Yeşil,
                                            description=f"**Tutulan Sayı**: `{sayı}`\n**Kaç Denemede Bulundu**: `{10 - hak}`")
                                        hesap.set_author(
                                            name=ctx.author.name, icon_url=ctx.author.avatar_url)
                                        hesap.set_footer(text=Footer)
                                        hesap.set_thumbnail(
                                            url=ctx.author.avatar_url)
                                        hesap.timestamp = ctx.message.created_at
                                        await ctx.send(embed=hesap)
                                        ctx.command.reset_cooldown(ctx)
                                        break

                                else:
                                    await tahmin.delete()
                                    await emebed.delete()
                                    süre = discord.Embed(
                                        title="Hata", color=Kırmızı,
                                        description=":warning: : Yazdıgınınız değer `sayı` olmalı.\n:warning: : Yazdığınız Değer `1-50` arasında olmalı.\n:warning: : Her hak süresi `60sn`.")
                                    süre.set_author(
                                        name=ctx.author.name, icon_url=ctx.author.avatar_url)
                                    süre.set_footer(text=Footer)
                                    await ctx.send(embed=süre, delete_after=15)
                                    ctx.command.reset_cooldown(ctx)
                                    break

                        if hak == 0:
                            await emebed.delete()
                            await ctx.send(f"Knk Üzgünüm Ama Hakkın Bitti.\n**Tuttugum Sayı**: `{sayı}`", delete_after=60)
                            ctx.command.reset_cooldown(ctx)
                    except Exception:
                        await asyncio.sleep(0.2)
                        await tahmin.delete()
                        süre = discord.Embed(
                            title="Hata", color=Kırmızı,
                            description=":warning: : Yazdıgınınız değer `sayı` olmalı.\n:warning: : Yazdığınız Değer `1-50` arasında olmalı.\n:warning: : Her hak süresi `60sn`.")
                        süre.set_author(name=ctx.author.name,
                                        icon_url=ctx.author.avatar_url)
                        süre.set_footer(text=Footer)
                        await ctx.send(embed=süre, delete_after=15)
                        ctx.command.reset_cooldown(ctx)
        except Exception as err:
            print(err)
            ctx.command.reset_cooldown(ctx)

    @command()
    async def üyeler(self, ctx):
        try:
            guild = ctx.guild
            members = guild.members
            msg = ""
            sayaç = 1
            for member in members:
                if member.id == owner:
                    msg += f"{sayaç}= `{member.name}` Gay Erdem\n"
                    sayaç += 1

                elif member.id == 170538175708528640:
                    msg += f"{sayaç}= `{member.name}` Sürtük Cem\n"
                    sayaç += 1
                else:
                    msg += f"{sayaç}= **{member.name}**\n"
                    sayaç += 1

            embed = discord.Embed(
                title=f"{guild.name} Üye Listesi", color=ctx.guild.me.color, description=msg)
            embed.set_footer(text=Footer)
            embed.set_thumbnail(url=guild.icon_url)
            embed.timestamp = ctx.message.created_at
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)

    @command()
    async def yaz(self, ctx, *, msg=None):
        if msg == None:
            await ctx.send(f"{ctx.author.mention} Bi Mesaj Belirt Knk Kullanım:\n```+yaz <Mesaj>```", delete_after=10)
            await asyncio.sleep(10)
            await ctx.message.delete()
            return
        else:
            await asyncio.sleep(0.2)
            await ctx.message.delete()
            await ctx.send(msg)

    @command(aliases=["clear", "temizlik", "t"])
    async def temizle(self, ctx, limit: int = None, member: discord.Member = None):
        basarili = 0
        basarisiz = 0
        if ctx.author.id != owner:
            return await ctx.send(":no_entry: `Sadece sahibim kullanabilir!`", delete_after=10)
        if limit == None:
            await ctx.send(f"{ctx.author.mention} Kaç Mesaj Silmeliyim. Kullanım:\n```+t <sayı>\n+t <sayı> <kullanıcı>```", delete_after=10)
            await asyncio.sleep(10)
            return await ctx.message.delete()

        if limit > 500 or limit < 1:
            await ctx.send(f"{ctx.author.mention} limit `1-500` arasındadır.", delete_after=10)
            await asyncio.sleep(10)
            return await ctx.message.delete()

        elif member != None:
            async for usermsg in ctx.channel.history(limit=limit):
                if usermsg.author.id == member.id:
                    try:
                        await usermsg.delete()
                        basarili += 1
                    except:
                        basarisiz += 1
                e = discord.Embed(title="Temizle", color=ctx.guild.me.color,description=f"Mesaj Silme Bilgileri:\n**Başarılı:** `{basarili}`\n**Başarısız:** `{basarisiz}`\n**Komutu Kullanan Yetkili** `{ctx.author}`\n**Mesajı Silinen Kişi:** `{member}`")
                e.set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
                e.set_footer(text=Footer)
                e.timestamp = ctx.message.created_at
                await ctx.send(embed=e)
        else:
            async for msg in ctx.channel.history(limit=limit):
                try:
                    await msg.delete()
                    basarili += 1
                except:
                    basarisiz += 1
            e = discord.Embed(title="Temizle", color=siyah,description=f"Mesaj Silme Bilgileri:\n**Başarılı:** `{basarili}`\n**Başarısız:** `{basarisiz}`\n**Komutu Kullanan Yetkili** `{ctx.author}`")
            e.set_author(name=ctx.author.name,icon_url=ctx.author.avatar_url)
            e.set_footer(text=Footer)
            e.timestamp = ctx.message.created_at
            await ctx.send(embed=e)

    @command()
    async def bilgi(self, ctx):
        msg = ""
        count = 0
        guilds = len(self.bot.guilds)
        count = len(self.bot.users)
        ping = round(self.bot.latency * 1000)
        msg += "**Sahibim :** <@!301405855784501248>\n"
        msg += "**Website :** [ErdemMusic](https://erdemusic.glitch.me)\n"
        msg += "**Komutlar :** [Komutlar](https://erdemusic.glitch.me/komutlar.html)\n"
        msg += "**GitHub :** [R3nzTheCodeGOD](https://github.com/R3nzTheCodeGOD)\n"
        msg += "**Destek Sunucusu :** [Discord](https://discord.gg/pAdTMMa)\n"
        msg += f"**Kaç Sunucu :** `{guilds}`\n"
        msg += f"**Kaç Kullanıcı :** `{count}`\n"
        msg += f"**Ping :** `{ping}ms`\n"
        e = discord.Embed(color=ctx.guild.me.color, description=msg)
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar_url,
                     url="https://erdemusic.glitch.me")
        e.set_footer(text="Copyright (c) 2020 Erdem Yılmaz")
        e.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(embed=e)

    @command(aliases=["beniekle", "invite", "inv"])
    async def davet(self, ctx):
        url = discord.utils.oauth_url(client_id=str(
            self.bot.user.id), permissions=discord.Permissions(permissions=573860928))
        e = discord.Embed(color=ctx.guild.me.color,
                          description=f"Beni eklemek için [buraya]({url}) tıkla")
        e.set_author(name=self.bot.user.name,
                     icon_url=self.bot.user.avatar_url)
        e.set_footer(text=Footer)
        e.timestamp = ctx.message.created_at
        await ctx.send(embed=e)

    @command(aliases=["emojiyazı"])
    async def eyaz(self, ctx, *, text):
        def converter(text):
            karakterler = {
                "a": ":regional_indicator_a:", "A": ":regional_indicator_a:",
                "b": ":regional_indicator_b:", "B": ":regional_indicator_b:",
                "c": ":regional_indicator_c:", "C": ":regional_indicator_c:",
                "d": ":regional_indicator_d:", "D": ":regional_indicator_d:",
                "e": ":regional_indicator_e:", "E": ":regional_indicator_e:",
                "q": ":regional_indicator_q:", "Q": ":regional_indicator_q:",
                "w": ":regional_indicator_w:", "W": ":regional_indicator_w:",
                "r": ":regional_indicator_r:", "R": ":regional_indicator_r:",
                "t": ":regional_indicator_t:", "T": ":regional_indicator_t:",
                "y": ":regional_indicator_y:", "Y": ":regional_indicator_y:",
                "u": ":regional_indicator_u:", "U": ":regional_indicator_u:",
                "ı": ":regional_indicator_i:", "I": ":regional_indicator_i:",
                "o": ":regional_indicator_o:", "O": ":regional_indicator_o:",
                "p": ":regional_indicator_p:", "P": ":regional_indicator_p:",
                "ğ": ":regional_indicator_g:", "Ğ": ":regional_indicator_g:",
                "ü": ":regional_indicator_u:", "Ü": ":regional_indicator_u:",
                "s": ":regional_indicator_s:", "S": ":regional_indicator_s:",
                "f": ":regional_indicator_f:", "F": ":regional_indicator_f:",
                "g": ":regional_indicator_g:", "G": ":regional_indicator_g:",
                "h": ":regional_indicator_h:", "H": ":regional_indicator_h:",
                "j": ":regional_indicator_j:", "J": ":regional_indicator_j:",
                "k": ":regional_indicator_k:", "K": ":regional_indicator_k:",
                "l": ":regional_indicator_l:", "L": ":regional_indicator_l:",
                "ş": ":regional_indicator_s:", "Ş": ":regional_indicator_s:",
                "i": ":regional_indicator_i:", "İ": ":regional_indicator_i:",
                "z": ":regional_indicator_z:", "Z": ":regional_indicator_z:",
                "x": ":regional_indicator_x:", "X": ":regional_indicator_x:",
                "v": ":regional_indicator_v:", "V": ":regional_indicator_v:",
                "n": ":regional_indicator_n:", "N": ":regional_indicator_n:",
                "m": ":regional_indicator_m:", "M": ":regional_indicator_m:",
                "ö": ":regional_indicator_o:", "Ö": ":regional_indicator_o:",
                "ç": ":regional_indicator_c:", "Ç": ":regional_indicator_c:",
                "0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:", "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:",
                " ": "   "
            }
            text = list(text)
            for karakter in text:
                if karakter in karakterler:
                    text[text.index(karakter)] = karakterler[karakter]

            return "".join(text)

        mesaj = converter(text)
        await ctx.send(mesaj)
        await ctx.message.delete()

    @command(aliases=["reboot", "yenidenbaşlat", "kapan"])
    async def die(self, ctx):
        msg = await ctx.send("Emojiye Tıkla Sahibimsen Bot Yeniden Başlatılıcak!")
        await msg.add_reaction(emoji="👋")
        while True:
            bekle = await self.bot.wait_for('reaction_add', timeout=60)
            if bekle[1].id == owner:
                if str(bekle[0].emoji) == '👋':
                    await msg.delete()
                    await ctx.send("Bot Yeniden Başlatılıyor!")
                    await self.bot.logout()
                    break
            else:
                await ctx.send(":no_entry: `Sadece sahibim kullanabilir!`", delete_after=5)
                continue

    @command(aliases=["tr", "tl", "translate"])
    async def çeviri(self, ctx, lang1: str = None, *, text: str = None):
        if lang1 is None:
            await ctx.send(f"{ctx.author.mention} Mesaj ve çevirilecek dil belirtin! Kullanım;\n```+çeviri en nasılsın```", delete_after=15)
            return
        if text is None:
            await ctx.send(f"{ctx.author.mention} Mesaj Belirtin! Kullanım;\n```+çeviri en nasılsın```", delete_after=15)
            return
        try:
            result = textblob.TextBlob(text).translate(
                from_lang="auto", to=lang1)
        except textblob.exceptions.NotTranslated:
            await ctx.send(f"{ctx.author.mention} Çeviri Yapılamadı!", delete_after=15)
        else:
            await ctx.send(f"```{result}```")

    @command()
    async def durumdegiş(self, ctx, *, status=None):
        if ctx.author.id != owner:
            return await ctx.send(":no_entry: `Sadece sahibim kullanabilir!`")
        if status is None:
            return
        activity_type = discord.ActivityType.listening
        await self.bot.change_presence(activity=discord.Activity(type=activity_type, name=status), status=discord.Status.idle)

    @command(aliases=['webh'])
    async def webhook(self, ctx, url=None):
        if ctx.author.id != owner:
            return await ctx.send(":no_entry: `Sadece sahibim kullanabilir!`")
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            emb = discord.Embed(color=discord.Color.from_rgb(30,215,96), title="Erdem Music", description=f"`Giriş`\nBu bot spotify apisini doğrudan kullanan `türkçe` müzik botudur artık sizlerle, botu eklemek için [Buraya](https://discord.com/oauth2/authorize?client_id=718225758790877374&scope=bot&permissions=573860928) tıklayınız.\n`Güvenlik`\nBot sunucuya eklenirken yöneticilik almaz gerekli yetkileri alır ve bu aldıgı yetkiler saldırı amaçlı kullanılamaz bu yüzden güvenlidir.\n\n**Geliştirici:** <@!{owner}>\n**Website:** [ErdemMusic](https://erdemusic.glitch.me)\n**Geliştirici GitHub:** [Erdem](https://github.com/R3nzTheCodeGOD)\n**Botun Kodları:** [ErdemMusicCODE](https://github.com/R3nzTheCodeGOD)")
            emb.set_footer(text="© 2020 Spotify AB")
            emb.set_image(url="https://oyuncubur.com/wp-content/uploads/2019/02/spotify-gif-oliver-keane.gif")
            await webhook.send(embed=emb, username="Spotify", avatar_url="https://image.flaticon.com/icons/png/512/2111/2111624.png")
            

def setup(bot):
    bot.add_cog(General(bot))
