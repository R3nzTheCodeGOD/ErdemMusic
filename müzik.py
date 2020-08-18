import discord
import asyncio
import random
import youtube_dl
import string
import os
from discord.ext import commands
from discord.ext.commands import command
import datetime

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '{}',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    "extractaudio": True,
    "audioformat": "opus",
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

stim = {
    'default_search': 'auto',
    "ignoreerrors": True,
    'quiet': True,
    "no_warnings": True,
    "simulate": True,
    "nooverwrites": True,
    "keepvideo": False,
    "noplaylist": True,
    "skip_download": False,
    'source_address': '0.0.0.0'
}


ffmpeg_options = {
    'options': '-vn',
}


class Downloader(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get("url")
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.views = data.get('view_count')
        self.playlist = {}

    @classmethod
    async def video_url(cls, url, ytdl, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        data1 = {'queue': []}
        if 'entries' in data:
            if len(data['entries']) > 1:
                playlist_titles = [title['title'] for title in data['entries']]
                data1 = {'title': data['title'], 'queue': playlist_titles}
                data1['queue'].pop(0)

            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data), data1

    async def get_info(self, url):
        yt = youtube_dl.YoutubeDL(stim)
        down = yt.extract_info(url, download=False)
        data1 = {'queue': []}
        if 'entries' in down:
            if len(down['entries']) > 1:
                playlist_titles = [title['title'] for title in down['entries']]
                data1 = {'title': down['title'], 'queue': playlist_titles}

            down = down['entries'][0]['title']

        return down, data1


class MusicPlayer(commands.Cog, name='Müzik'):
    def __init__(self, client):
        self.bot = client
        self.player = {
            "audio_files": []
        }

    @commands.Cog.listener('on_voice_state_update')
    async def music_voice(self, user, before, after):
        if after.channel is None and user.id == self.bot.user.id:
            try:
                self.player[user.guild.id]['queue'].clear()
            except KeyError:
                print(f"{user.guild.id} Guild İd Alınamadı")

    async def filename_generator(self):
        chars = list(string.ascii_letters+string.digits)
        name = ''
        for i in range(random.randint(9, 25)):
            name += random.choice(chars)

        if name not in self.player['audio_files']:
            return name

        return await self.filename_generator()

    async def playlist(self, data, msg):
        for i in data['queue']:
            self.player[msg.guild.id]['queue'].append(
                {'title': i, 'author': msg})

    async def queue(self, msg, song):
        title1 = await Downloader.get_info(self, url=song)
        title = title1[0]
        data = title1[1]
        if data['queue']:
            await self.playlist(data, msg)
            return await msg.send(f"`{data['title']}` Oynatma Listesine Eklendi")
        self.player[msg.guild.id]['queue'].append(
            {'title': title, 'author': msg})
        return await msg.send(f"`{title}` **Sıraya Eklendi**".title())

    async def voice_check(self, msg):
        if msg.voice_client is not None:
            await asyncio.sleep(120)
            if msg.voice_client is not None and msg.voice_client.is_playing() is False and msg.voice_client.is_paused() is False:
                await msg.voice_client.disconnect()

    async def clear_data(self, msg):
        name = self.player[msg.guild.id]['name']
        os.remove(name)
        self.player['audio_files'].remove(name)

    async def loop_song(self, msg):
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(self.player[msg.guild.id]['name']))
        loop = asyncio.get_event_loop()
        try:
            msg.voice_client.play(
                source, after=lambda a: loop.create_task(self.done(msg)))
            msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
        except Exception as Error:
            print(Error)

    async def done(self, msg, msgId=None):
        if msgId:
            await msgId.delete()


        if self.player[msg.guild.id]['reset'] is True:
            self.player[msg.guild.id]['reset'] = False
            return await self.loop_song(msg)

        if msg.guild.id in self.player and self.player[msg.guild.id]['repeat'] is True:
            return await self.loop_song(msg)

        await self.clear_data(msg)
        status = '+bilgi | https://erdemusic.glitch.me'
        activity_type = discord.ActivityType.listening
        await self.bot.change_presence(activity=discord.Activity(type=activity_type, name=status), status=discord.Status.idle)

        if self.player[msg.guild.id]['queue']:
            queue_data = self.player[msg.guild.id]['queue'].pop(0)
            return await self.start_song(msg=queue_data['author'], song=queue_data['title'])

        else:
            await self.voice_check(msg)

    async def start_song(self, msg, song, spotify=False, member=None, sayı=None):
        new_opts = ytdl_format_options.copy()
        audio_name = await self.filename_generator()

        self.player['audio_files'].append(audio_name)
        new_opts['outtmpl'] = new_opts['outtmpl'].format(audio_name)

        ytdl = youtube_dl.YoutubeDL(new_opts)
        download1 = await Downloader.video_url(song, ytdl=ytdl, loop=self.bot.loop)

        download = download1[0]
        data = download1[1]
        self.player[msg.guild.id]['name'] = audio_name
        if spotify == False:
            emb = discord.Embed(colour=msg.guild.me.color, title='Şimdi oynuyor',
                                description=download.title, url=download.url)
            emb.set_thumbnail(url=download.thumbnail)
            emb.set_footer(text=f'Coded By Erdem')
        if spotify == True:
            mesaj = f"**Müzik Süresi:** `{download.duration}saniye`\n"
            mesaj += f"**Youtube İzlenme Sayısı:** `{download.views}`\n"
            mesaj += f"**Müzik İndirme Linki:** [downloadURL]({download.url})\n"
            mesaj += f"**Spotify Sunucu:** `{member.name}`\n"
            mesaj += f"**Degiştirilen Şarkı Sayısı:** `{sayı}`"
            emb = discord.Embed(colour=msg.guild.me.color,description=mesaj, title=download.title)
            emb.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url,url="https://erdemusic.glitch.me")
            emb.set_image(url=download.thumbnail)
            emb.set_footer(text=f'Copyright (c) 2020 Erdem Yılmaz',icon_url="https://cdn.discordapp.com/avatars/301405855784501248/ba45ef33392fae28f6c142f38e954f7a.png?size=1024")
        loop = asyncio.get_event_loop()
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=download.title), status=discord.Status.idle)

        if data['queue']:
            await self.playlist(data, msg)
        msgId = await msg.send(embed=emb)
        if spotify == True:
            await msgId.add_reaction(emoji="⏹️")
        self.player[msg.guild.id]['player'] = download
        self.player[msg.guild.id]['author'] = msg
        msg.voice_client.play(download, after=lambda a: loop.create_task(self.done(msg, msgId)))
        msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
        return msg.voice_client

    @command(aliases=["p", "play"])
    async def çal(self, msg, *, song):
        if msg.guild.id in self.player:
            if msg.voice_client.is_playing() is True:
                return await self.queue(msg, song)

            if self.player[msg.guild.id]['queue']:
                return await self.queue(msg, song)

            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await self.start_song(msg, song)

        else:
            self.player[msg.guild.id] = {
                'player': None,
                'queue': [],
                'author': msg,
                'name': None,
                "reset": False,
                'repeat': False,
                'volume': 0.5
            }
            return await self.start_song(msg, song)

    @çal.before_invoke
    async def before_play(self, msg):
        if msg.author.voice is None:
            return await msg.send('**Müzik çalmak için lütfen bir ses kanalına katılın**'.title())

        if msg.voice_client is None:
            return await msg.author.voice.channel.connect()

        if msg.voice_client.channel != msg.author.voice.channel:
            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await msg.voice_client.move_to(msg.author.voice.channel)

            if self.player[msg.guild.id]['queue']:
                return await msg.send("Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın")

    @command(aliases=["loop", "repeat"])
    async def tekrar(self, msg):
        if msg.guild.id in self.player:
            if msg.voice_client.is_playing() is True:
                if self.player[msg.guild.id]['repeat'] is True:
                    self.player[msg.guild.id]['repeat'] = False
                    return await msg.message.add_reaction(emoji='⏸️')

                self.player[msg.guild.id]['repeat'] = True
                return await msg.message.add_reaction(emoji='🔁')

            return await msg.send("Şu anda çalınan ses yok")
        return await msg.send("Bot ses kanalında yok veya müzik çalıyor")

    @command()
    async def reset(self, msg):
        if msg.voice_client is None:
            return await msg.send(f"**{msg.author.display_name}, şu anda botta oynatılan ses yok.**")

        if msg.author.voice is None or msg.author.voice.channel != msg.voice_client.channel:
            return await msg.send(f"**{msg.author.display_name}, botla aynı ses kanalında olmalısın.**")

        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            return await msg.send("**Şu anda oynatılan ses veya sırada şarkı yok**".title(), delete_after=25)

        self.player[msg.guild.id]['reset'] = True
        msg.voice_client.stop()

    @command(aliases=["skip"])
    async def geç(self, msg):
        if msg.voice_client is None:
            return await msg.send("**Şu anda oynatılan müzik yok**".title(), delete_after=60)

        if msg.author.voice is None or msg.author.voice.channel != msg.voice_client.channel:
            return await msg.send("Lütfen botla aynı ses kanalına katılın")

        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            return await msg.send("**Sırada atlanacak şarkı yok**".title(), delete_after=60)

        self.player[msg.guild.id]['repeat'] = False
        msg.voice_client.stop()
        return await msg.message.add_reaction(emoji='⏭️')

    @command(aliases=["stop"])
    async def dur(self, msg):
        if msg.voice_client is None:
            return await msg.send("Bot bir ses kanalına bağlı değil")

        if msg.author.voice is None:
            return await msg.send("Bot ile aynı ses kanalında olmalısınız")

        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_playing() is True or self.player[msg.guild.id]['queue']:
                self.player[msg.guild.id]['queue'].clear()
                self.player[msg.guild.id]['repeat'] = False
                msg.voice_client.stop()
                return await msg.message.add_reaction(emoji='☑️')

            return await msg.send(f"**{msg.author.display_name}, şu anda oynatılan ses veya sırada şarkı yok**")

    @command(aliases=['sg', 'dc', 'siktirgit'])
    async def çık(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_playing() is True or self.player[msg.guild.id]['queue']:
                self.player[msg.guild.id]['queue'].clear()
                msg.voice_client.stop()
                return await msg.voice_client.disconnect(), await msg.message.add_reaction(emoji='😔')

            return await msg.voice_client.disconnect(), await msg.message.add_reaction(emoji='😔')

        if msg.author.voice is None:
            return await msg.send("Odayla bağlantısını kesmek için botla aynı ses kanalında olmalısınız")

    @command(aliases=["pause"])
    async def duraklat(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_paused() is True:
                return await msg.send("Şarkı zaten duraklatılmış")

            if msg.voice_client.is_paused() is False:
                msg.voice_client.pause()
                await msg.message.add_reaction(emoji='⏸️')

    @command(aliases=["resume"])
    async def devam(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_paused() is False:
                return await msg.send("Şarkı zaten oynatılıyor")

            if msg.voice_client.is_paused() is True:
                msg.voice_client.resume()
                return await msg.message.add_reaction(emoji='▶️')

    @command(name='sıradakiler', aliases=['queue', 'q'])
    async def _queue(self, msg):
        if msg.voice_client is not None:
            if msg.guild.id in self.player:
                if self.player[msg.guild.id]['queue']:
                    emb = discord.Embed(
                        colour=msg.guild.me.color, title='sıradakiler')
                    emb.set_footer(text=f'Coded By Erdem')
                    for i in self.player[msg.guild.id]['queue']:
                        emb.add_field(
                            name=f"**{i['author'].author.name}**", value=i['title'], inline=False)
                    return await msg.send(embed=emb)

        return await msg.send("Sırada şarkı yok")

    @command(name='çalan', aliases=['np'])
    async def song_info(self, msg):
        if msg.voice_client is not None and msg.voice_client.is_playing() is True:
            emb = discord.Embed(colour=msg.guild.me.color, title='Şuanda Oynatılan',
                                description=self.player[msg.guild.id]['player'].title)
            emb.set_footer(text="Coded By Erdem")
            emb.set_thumbnail(
                url=self.player[msg.guild.id]['player'].thumbnail)
            return await msg.send(embed=emb)

        return await msg.send(f"**Şu anda oynatılan şarkı yok**".title(), delete_after=30)

    @command(aliases=["k", "join"])
    async def katıl(self, msg, *, channel: discord.VoiceChannel = None):
        if msg.voice_client is not None:
            return await msg.send("Zaten bir ses kanalında")

        if msg.voice_client is None:
            if channel is None:
                return await msg.author.voice.channel.connect(), await msg.message.add_reaction(emoji='☑️')

            return await channel.connect(), await msg.message.add_reaction(emoji='☑️')

        else:
            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await msg.author.voice.channel.connect(), await msg.message.add_reaction(emoji='☑️')

    @katıl.before_invoke
    async def before_join(self, msg):
        if msg.author.voice is None:
            return await msg.send("Bir ses kanalında değilsin")

    @katıl.error
    async def join_error(self, msg, error):
        if isinstance(error, commands.BadArgument):
            return msg.send(error)

        if error.args[0] == 'Command raised an exception: Exception: playing':
            return await msg.send("**Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın**".title())

    @command(aliases=['volume', 'v'])
    async def ses(self, msg, vol: int):
        if vol > 200:
            vol = 200
        vol = vol/100
        if msg.author.voice is not None:
            if msg.voice_client is not None:
                if msg.voice_client.channel == msg.author.voice.channel and msg.voice_client.is_playing() is True:
                    msg.voice_client.source.volume = vol
                    self.player[msg.guild.id]['volume'] = vol
                    return await msg.message.add_reaction(emoji='🔊')

        return await msg.send("**Komutu kullanmak için lütfen botla aynı ses kanalına katılın**".title(), delete_after=30)

    @ses.error
    async def volume_error(self, msg, error):
        if isinstance(error, commands.MissingPermissions):
            return await msg.send("Ses seviyesini değiştirmek için gerekli kanalları veya yönetici izinlerini kontrol edin.", delete_after=30)

    @command(aliases=["sp"])
    async def spotify(self, msg, *members: discord.Member):
        if len(members) == 0:
            members = [msg.author]
        for member in members:
            if member.activity == None:
                return await msg.send("Şuanda Spotify dinlemiyorsun.", delete_after=20)
            elif member.activity.type == discord.ActivityType.custom:
                return await msg.send("Bu özelliğin çalışması için Kullanıcının `Custom Status'u` kaldırması gerek.", delete_after=20)
            elif member.activity.type != discord.ActivityType.listening:
                return await msg.send("Şuanda Spotify dinlemiyorsun.", delete_after=20)
            elif member.activity.type == discord.ActivityType.listening:
                title = "title31"
                count = 0
                try:
                    while True:
                        if title != "title31":
                            await asyncio.sleep(1)

                        if member.activity == None:
                            await asyncio.sleep(1.5)
                            if member.activity == None:
                                await asyncio.sleep(5)
                                if member.activity == None:
                                    await msg.send(f"{msg.author.mention} [{member.name}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.")
                                    break
                        elif member.activity != None:
                            if member.activity.type != discord.ActivityType.listening:
                                await asyncio.sleep(1.5)
                                if member.activity.type != discord.ActivityType.listening:
                                    await asyncio.sleep(5)
                                    if member.activity.type != discord.ActivityType.listening:
                                        await msg.send(f"{msg.author.mention} [{member.name}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.")
                                        break

                        if member.activity.title != title:
                            title = member.activity.title
                            song = f"{member.activity.title} {member.activity.artist}"

                            if msg.voice_client.is_playing() is True:
                                self.player[msg.guild.id]['queue'].clear()
                                self.player[msg.guild.id]['repeat'] = False
                                msg.voice_client.stop()

                            if msg.guild.id in self.player:
                                if msg.voice_client.is_playing() is True:
                                    await self.queue(msg, song)
                                    continue

                                if self.player[msg.guild.id]['queue']:
                                    await self.queue(msg, song)
                                    continue

                                if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                                    await self.start_song(msg, song, True, member, count)
                                    count += 1
                                    continue

                            else:
                                self.player[msg.guild.id] = {
                                    'player': None,
                                    'queue': [],
                                    'author': msg,
                                    'name': None,
                                    "reset": False,
                                    'repeat': False,
                                    'volume': 0.5
                                }
                                await self.start_song(msg, song, True, member, count)
                                count += 1
                                continue
                except Exception as e:
                    await msg.send(f"{msg.author.mention} Bir Hata Meydana Geldi Döngüden Çıkılıyor!")

    @spotify.before_invoke
    async def before_play(self, msg):
        if msg.author.voice is None:
            return await msg.send('**Müzik çalmak için lütfen bir ses kanalına katılın**'.title(), delete_after=10)

        if msg.voice_client is None:
            return await msg.author.voice.channel.connect()

        if msg.voice_client.channel != msg.author.voice.channel:
            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await msg.voice_client.move_to(msg.author.voice.channel)

            if self.player[msg.guild.id]['queue']:
                return await msg.send("**Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın**", delete_after=10)


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
