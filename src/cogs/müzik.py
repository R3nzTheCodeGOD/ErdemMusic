import discord, asyncio, aiohttp, random, youtube_dl, string
import os, datetime, re, sys
from discord.ext import commands
from discord.ext.commands import command
from src.cogs.spotify import Spotify
sys.path.append('../')
from config.ayarlar import *
from discord import opus
import subprocess
import json

ytdl_format_options = {
    'audioquality': 0,
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
    'source_address': '0.0.0.0',
    'usenetrc': True
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
        self.youtubeURL = data.get("webpage_url")
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.views = data.get('view_count')
        self.playlist = {}

    @classmethod
    async def video_url(cls, url, ytdl, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream)) 
        data1 = {'queue': []}
        if data is None:
            return None
        if 'entries' in data:
            if len(data['entries']) > 1:
                index = 0
                for i in data['entries']:
                    if i == None:
                        data['entries'].pop(index) 
                    index += 1        
                playlist_titles = [title['title'] for title in data['entries']]      
                data1 = {'title': data['title'], 'queue': playlist_titles}
                data1['queue'].pop(0)
            elif len(data['entries']) == 1:
                if data['entries'][0] is None:
                    return None
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, before_options="-nostdin", options="-vn", stderr=subprocess.PIPE), data=data), data1

    async def get_info(self, url, loop=None):
        yt = youtube_dl.YoutubeDL(stim)
        loop = loop or asyncio.get_event_loop() 
        down = await loop.run_in_executor(None, lambda: yt.extract_info(url=url, download=False))
        if down is None:
            return down
        if down['entries'][0] is None:
            down = None
            return down
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
        opus._load_default()
        print(opus.is_loaded())
        self.aiosession = aiohttp.ClientSession(loop=self.bot.loop)
        self.spotify = Spotify(aiosession=self.aiosession, loop=self.bot.loop)
        if not self.spotify.token:
            print('Spotify bize bir jeton sağlamadı. Devre Dışı Bırakılıyor.')
        else:
            print('Spotify ile kimlik doğrulaması yapıldı.')

        self.stopSpotify = False
        

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
        for i in data['queue'][:200]:
            self.player[msg.guild.id]['queue'].append({'title': i, 'author': msg})
            
    async def queue(self, msg, song, spotify=False):
        title1 = await Downloader.get_info(self, url=song, loop=self.bot.loop) 
        if title1 == None:
            emb = discord.Embed(color=discord.Color.red(), description=F"{msg.author.mention}, bu şarkı sıraya eklenemedi")
            return await msg.send(embed=emb, delete_after=25)
        else:
            title = title1[0]
            data = title1[1]
            if data['queue']:
                await self.playlist(data, msg)
                emb = discord.Embed(color=msg.guild.me.color, description=f"[{title}](https://erdemusic.glitch.me) sıraya alındı [{msg.author.mention}]")
                try:
                    return await msg.send(embed=emb, delete_after=60)
                except Exception:
                    return await msg.send(f"`{title}` Oynatma Listesine Eklendi\n```Bot şuanda düşük performans modunda çalışıyor eğer bu mesajı görüyorsan botu kullandıgın kanalda bota baglantı yerleştir yetkisi verdigin zaman bot artık chatte diğer botlar gibi embed atabilir hale gelicek.\nEğer başka çözemediğin bir sorun varsa bana ulaş.```Sahibim: <@!{owner}>\nDaha Fazla Bilgi: `+bilgi`", delete_after=60)
            self.player[msg.guild.id]['queue'].append({'title': title, 'author': msg})
            emb2 = discord.Embed(color=msg.guild.me.color, description=f"[{title}](https://erdemusic.glitch.me) sıraya alındı [{msg.author.mention}]")
            try:
                return await msg.send(embed=emb2, delete_after=60)
            except Exception:
                return await msg.send(f"`{title}` Sıraya Eklendi\n```Bot şuanda düşük performans modunda çalışıyor eğer bu mesajı görüyorsan botu kullandıgın kanalda bota baglantı yerleştir yetkisi verdigin zaman bot artık chatte diğer botlar gibi embed atabilir hale gelicek.\nEğer başka çözemediğin bir sorun varsa bana ulaş.```Sahibim: <@!{owner}>\nDaha Fazla Bilgi: `+bilgi`", delete_after=60)

    async def voice_check(self, msg):
        if msg.voice_client is not None:
            await asyncio.sleep(120)
            if msg.voice_client is not None and msg.voice_client.is_playing() is False and msg.voice_client.is_paused() is False:
                await msg.voice_client.disconnect()
                emb = discord.Embed(color=msg.guild.me.color, description=f"Şarkı çalmadıgım için ayrıldım [{msg.author.mention}]")
                try:
                    await msg.send(embed=emb, delete_after=600)
                except Exception:
                    pass

    async def clear_data(self, msg):
        name = self.player[msg.guild.id]['name']
        os.remove(name)
        self.player['audio_files'].remove(name)

    async def loop_song(self, msg):
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(self.player[msg.guild.id]['name']))
        loop = self.bot.loop
        try:
            msg.voice_client.play(
                source, after=lambda a: loop.create_task(self.done(msg)))
            msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
        except Exception as Error:
            print(Error)

    async def openspotify(self, msg, song_url):
        async with msg.channel.typing():
            try:
                if 'open.spotify.com' in song_url:
                    song_url = 'spotify:' + re.sub('(http[s]?:\/\/)?(open.spotify.com)\/', '', song_url).replace('/', ':')
                    song_url = re.sub('\?.*', '', song_url)
                if song_url.startswith('spotify:'):
                    parts = song_url.split(":")
                    if 'track' in parts:
                        res = await self.spotify.get_track(parts[-1])
                        song_url = res['artists'][0]['name'] + ' ' + res['name']
                        await self.çal(msg=msg, song_url=song_url)

                    elif 'album' in parts:
                        res = await self.spotify.get_album(parts[-1])
                        counter = 0
                        for i in res['tracks']['items']:
                            counter += 1
                            song_url = i['name'] + ' ' + i['artists'][0]['name']
                            if counter == 1:
                                if msg.guild.id in self.player:
                                    if self.player[msg.guild.id]['queue']:
                                        self.player[msg.guild.id]['queue'].append({'title': song_url, 'author': msg})
                                        continue
                                    else:
                                        await self.çal(msg=msg, song_url=song_url)
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
                                    await self.çal(msg=msg, song_url=song_url)
                                    continue
                            else:
                                self.player[msg.guild.id]['queue'].append({'title': song_url, 'author': msg})
                                continue
                        emb = discord.Embed(color=msg.guild.me.color, description=f"**{counter - 1}** şarkı listeye eklendi [{msg.author.mention}]")
                        return await msg.send(embed=emb, delete_after=60)
                    elif 'playlist' in parts:
                        try:
                            res = []
                            r = await self.spotify.get_playlist_tracks(parts[-1])
                            res.extend(r['items'])
                            counter = 0
                            for i in res:
                                counter += 1
                                song_url = i['track']['name'] + ' ' + i['track']['artists'][0]['name']
                                if counter == 199:
                                    break
                                if counter == 1:
                                    if msg.guild.id in self.player:
                                        if self.player[msg.guild.id]['queue']:
                                            self.player[msg.guild.id]['queue'].append({'title': song_url, 'author': msg})
                                            continue
                                        else:
                                            await self.çal(msg=msg, song_url=song_url)
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
                                        await self.çal(msg=msg, song_url=song_url)
                                        continue
                                else:
                                    self.player[msg.guild.id]['queue'].append({'title': song_url, 'author': msg})
                                    continue
                            emb = discord.Embed(color=msg.guild.me.color, description=f"**{counter - 1}** şarkı listeye eklendi [{msg.author.mention}]")
                            return await msg.send(embed=emb, delete_after=60)
                        except Exception:
                            return await msg.send("Spotify tarafından bir hata oluştu", delete_after=10)
                    else:
                        await msg.send("Bu desteklenen bir Spotify URI'si değil.", delete_after=25)
            except Exception:
                return await msg.send("Spotify tarafından bir hata oluştu", delete_after=10)

    async def done(self, msg, msgId=None):
        if msgId:
            try:
                await msgId.delete()
            except Exception:
                pass
        
        if msg.voice_client is None:
            return

        if self.player[msg.guild.id]['reset'] is True:
            self.player[msg.guild.id]['reset'] = False
            return await self.loop_song(msg)

        if msg.guild.id in self.player and self.player[msg.guild.id]['repeat'] is True:
            return await self.loop_song(msg)

        await self.clear_data(msg)
        await asyncio.sleep(3.5)
        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            queue_data = self.player[msg.guild.id]['queue'].pop(0)
            return await self.start_song(msg=queue_data['author'], song=queue_data['title'])

        else:
            await self.voice_check(msg)

    async def start_song(self, msg, song, spotify=False, member=None, sayı=None):
        async with msg.channel.typing():
            try:
                new_opts = ytdl_format_options.copy()
                audio_name = await self.filename_generator()

                self.player['audio_files'].append(audio_name)
                new_opts['outtmpl'] = new_opts['outtmpl'].format(audio_name)

                ytdl = youtube_dl.YoutubeDL(new_opts)
                download1 = await Downloader.video_url(song, ytdl=ytdl, loop=self.bot.loop)
                if download1 == None:
                    emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, şarkı indirilemedi sırada şarkı varsa devam edilecek")
                    await msg.send(embed=emb, delete_after=25)
                    return await self.done(msg)
                download = download1[0]
                data = download1[1]
                self.player[msg.guild.id]['name'] = audio_name
                if spotify == False:
                    emb = discord.Embed(colour=msg.guild.me.color, title='Şimdi oynuyor',description=f"[{download.title}]({download.youtubeURL}) [{msg.author.mention}]")
                if spotify == True:
                    mesaj = f"**Müzik Süresi:** `{download.duration}saniye`\n"
                    mesaj += f"**Youtube İzlenme Sayısı:** `{download.views:,d}`\n"
                    mesaj += f"**Müzik İndirme Linki:** [downloadURL]({download.url})\n"
                    mesaj += f"**Spotify Sunucu:** `{member.name}`\n"
                    mesaj += f"**Degiştirilen Şarkı Sayısı:** `{sayı}`"
                    emb = discord.Embed(colour=msg.guild.me.color,description=mesaj, title=download.title)
                    emb.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url,url="https://erdemusic.glitch.me")
                    emb.set_image(url=download.thumbnail)
                    emb.set_footer(text=f'Copyright (c) 2020 Erdem Yılmaz',icon_url=msg.author.avatar_url)
                loop = self.bot.loop
                
                if data['queue']:
                    await self.playlist(data, msg)
                    
                try:
                    msgId = await msg.send(embed=emb)
                except Exception:
                    msgId = await msg.send(download.title + f"\n```Bot şuanda düşük performans modunda çalışıyor eğer bu mesajı görüyorsan botu kullandıgın kanalda bota baglantı yerleştir yetkisi verdigin zaman bot artık chatte diğer botlar gibi embed atabilir hale gelicek.\nEğer başka çözemediğin bir sorun varsa bana ulaş.```Sahibim: <@!{owner}>\nDaha Fazla Bilgi: `+bilgi`")
                
                if spotify == True:
                    try:
                        await msgId.add_reaction(emoji="⏹️")
                    except Exception:
                        pass
                self.player[msg.guild.id]['player'] = download
                self.player[msg.guild.id]['author'] = msg
                msg.voice_client.play(download, after=lambda a: loop.create_task(self.done(msg, msgId)))
                msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
                return msg.voice_client
            except Exception as e:
                print(e)

    @command(aliases=["p", "play"])
    async def çal(self, msg, *, song_url):
        if msg.author.voice is None:
            return
        if 'open.spotify.com' in song_url or song_url.startswith('spotify:'):
            return await self.openspotify(msg, song_url)
        if msg.guild.id in self.player:
            if msg.voice_client.is_playing() is True:
                return await self.queue(msg, song_url)

            if self.player[msg.guild.id]['queue']:
                return await self.queue(msg, song_url)

            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await self.start_song(msg, song_url)

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
            return await self.start_song(msg, song_url)

    @çal.before_invoke
    async def before_play(self, msg):
        if msg.author.voice is None:
            emb = discord.Embed(color=discord.Color.red(), description=f'{msg.author.mention}, müzik çalmak için lütfen bir ses kanalına katılın')
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send('Müzik çalmak için lütfen bir ses kanalına katılın', delete_after=25)

        if msg.voice_client is None:
            return await msg.author.voice.channel.connect()

        if msg.voice_client.channel != msg.author.voice.channel:
            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await msg.voice_client.move_to(msg.author.voice.channel)

            if self.player[msg.guild.id]['queue']:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send("Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın", delete_after=25)

    
    @command(aliases=["loop", "repeat"])
    async def tekrar(self, msg):
        if msg.guild.id in self.player:
            if msg.voice_client.is_playing() is True:
                if self.player[msg.guild.id]['repeat'] is True:
                    self.player[msg.guild.id]['repeat'] = False
                    return await msg.message.add_reaction(emoji='⏸️')

                self.player[msg.guild.id]['repeat'] = True
                return await msg.message.add_reaction(emoji='🔁')
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, şu anda çalınan ses yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Şu anda çalınan ses yok", delete_after=25)
        emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bot ses kanalında yok")
        try:
            return await msg.send(embed=emb, delete_after=25)
        except Exception:
            return await msg.send("Bot ses kanalında yok", delete_after=25)

    @command(aliases=['again', 'yeniden'])
    async def reset(self, msg):
        if msg.voice_client is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bot bir ses kanalına bağlı değil")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botta oynatılan ses yok.", delete_after=25)

        if msg.author.voice is None or msg.author.voice.channel != msg.voice_client.channel:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, botla aynı ses kanalında olmalısın")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botla aynı ses kanalında olmalısın", delete_after=25)

        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, oynatılan ses veya sırada şarkı yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Şu anda oynatılan ses veya sırada şarkı yok", delete_after=25)

        self.player[msg.guild.id]['reset'] = True
        msg.voice_client.stop()

    @command(aliases=['shuffle'])
    async def karıştır(self, msg):
        if msg.author.voice is None:
            emb = discord.Embed(color=discord.Color.red(), description=f'{msg.author.mention}, bu komutu kullanmak için lütfen botla aynı ses kanalına katılın')
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send('Bu komutu kullanmak için lütfen botla aynı ses kanalına katılın', delete_after=25)
        
        if msg.voice_client.channel != msg.author.voice.channel:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bu komutu kullanmak için lütfen botla aynı ses kanalına katılın")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Bu komutu kullanmak için lütfen botla aynı ses kanalına katılın", delete_after=25)
                
        if self.player[msg.guild.id]['queue'] and msg.voice_client is not None:
            random.shuffle(self.player[msg.guild.id]['queue'])
            cards = ['\N{BLACK SPADE SUIT}', '\N{BLACK CLUB SUIT}', '\N{BLACK HEART SUIT}', '\N{BLACK DIAMOND SUIT}']
            random.shuffle(cards)
            hand = await msg.send(' '.join(cards))
            await asyncio.sleep(0.6)
            for x in range(10):
                random.shuffle(cards)
                await hand.edit(content=' '.join(cards))
                await asyncio.sleep(0.4)
            await hand.delete()
            emb = discord.Embed(color=msg.guild.me.color, description=f"Listedeki **{len(self.player[msg.guild.id]['queue'])}** tane şarkı karıştırıldı. Karıştıran [{msg.author.mention}]")
            await msg.send(embed=emb, delete_after=60)
        elif msg.voice_client is False and self.player[msg.guild.id]['queue'] is False:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, sırada Şarkı Yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Sırada Şarkı Yok", delete_after=25)
    
    @command(aliases=['lyrics', 'ly'])
    async def şarkısözleri(self, msg, *, song=None):
        if song is None:
            if msg.voice_client is None:
                return await msg.send("Oynatılan müzik yok\n```+ly [şarkı ismi] olarak kullanabilirsiniz```", delete_after=25)
            if msg.voice_client.is_playing() is False:
                return await msg.send("Oynatılan müzik yok\n```+ly [şarkı ismi] olarak kullanabilirsiniz```", delete_after=25)
            return await msg.send(f"-ly {self.player[msg.guild.id]['player'].title}", delete_after=0.1)
        else:
            return await msg.send(f"-ly {song}", delete_after=0.1)

    @command(aliases=["skip", "next", "n"])
    async def geç(self, msg, sarkı: int=None):
        if msg.voice_client is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bot bir ses kanalına bağlı değil")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botta oynatılan ses yok.", delete_after=25)

        if msg.author.voice is None or msg.author.voice.channel != msg.voice_client.channel:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, botla aynı ses kanalında olmalısın")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botla aynı ses kanalında olmalısın", delete_after=25)

        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, oynatılan ses veya sırada şarkı yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Şu anda oynatılan ses veya sırada şarkı yok", delete_after=25)


        if sarkı is not None:
            kontrol = len(self.player[msg.guild.id]['queue'])
            if sarkı > 1 and sarkı <= kontrol:
                self.player[msg.guild.id]['repeat'] = False
                queue_data = self.player[msg.guild.id]['queue'].pop(sarkı - 1)
                msg.voice_client.stop()
                await self.start_song(msg=queue_data['author'], song=queue_data['title'])
                return await msg.message.add_reaction(emoji='⏭️')
            else:
                emb = discord.Embed(Color=discord.Color.red(), description=f"Belirttiğiniz Değer `2-{kontrol}` arasında olmalıdır!")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send(f"Belirttiğiniz Değer `2-{kontrol}` arasında olmalıdır!", delete_after=25)
        else:
            self.player[msg.guild.id]['repeat'] = False
            msg.voice_client.stop()
            return await msg.message.add_reaction(emoji='⏭️')
        
    @command(aliases=['remove'])
    async def çıkar(self, msg, sarkı: int=None):
        if msg.voice_client is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bot bir ses kanalına bağlı değil")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botta oynatılan ses yok.", delete_after=25)

        if msg.author.voice is None or msg.author.voice.channel != msg.voice_client.channel:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, botla aynı ses kanalında olmalısın")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Botla aynı ses kanalında olmalısın", delete_after=25)

        if self.player[msg.guild.id]['queue'] and msg.voice_client.is_playing() is False:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, oynatılan ses veya sırada şarkı yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Şu anda oynatılan ses veya sırada şarkı yok", delete_after=25)

        if sarkı is not None:
            kontrol = len(self.player[msg.guild.id]['queue'])
            if sarkı >= 1 and sarkı <= kontrol:
                data = self.player[msg.guild.id]['queue'].pop(sarkı - 1)
                emb = discord.Embed(color=msg.guild.me.color, description=f"`{data['title']}` adlı şarkı listeden çıkarıldı [{msg.author.mention}]")
                return await msg.send(embed=emb, delete_after=100)
            else:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, belirttiğiniz Değer `1-{kontrol}` arasında olmalıdır!")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send(f"Belirttiğiniz Değer `2-{kontrol}` arasında olmalıdır!", delete_after=25)

        if sarkı is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, lütfen bir değer belirtin\n```Kullanım:\n+çıkar [sayı]\nBilgilendirme: Listedeki şarkıları ve şarkı sayılarını +q komutu ile görebilirsin```")
            try:
                await msg.send(embed=emb, delete_after=25)
            except Exception:
                await msg.send("Lütfen bir değer belirtin\n```Kullanım:\n+çıkar [sayı]\nBilgilendirme: Listedeki şarkıları ve şarkı sayılarını +q komutu ile görebilirsin```")
    
    @command(aliases=["stop"])
    async def dur(self, msg):
        if msg.voice_client is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, bot bir ses kanalına bağlı değil")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Bot bir ses kanalına bağlı değil", delete_after=25)

        if msg.author.voice is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, Bir ses kanalına bağlı degilsin")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send(f"{msg.author.mention}, Bir ses kanalına bağlı degilsin", delete_after=25)

        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_playing() is True or self.player[msg.guild.id]['queue']:
                self.player[msg.guild.id]['queue'].clear()
                self.player[msg.guild.id]['repeat'] = False
                msg.voice_client.stop()
                await msg.message.add_reaction(emoji='☑️')
                self.stopSpotify = True
                await asyncio.sleep(5)
                self.stopSpotify = False
                return 
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, oynatılan ses veya sırada şarkı yok")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Oynatılan ses veya sırada şarkı yok", delete_after=25)

    @command(aliases=['sg', 'dc', 'siktirgit'])
    async def çık(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_playing() is True or self.player[msg.guild.id]['queue']:
                self.player[msg.guild.id]['queue'].clear()
                msg.voice_client.stop()
                return await msg.voice_client.disconnect(), await msg.message.add_reaction(emoji='😔')

            return await msg.voice_client.disconnect(), await msg.message.add_reaction(emoji='😔')

        if msg.author.voice is None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, odayla bağlantısını kesmek için botla aynı ses kanalında olmalısınız")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Odayla bağlantısını kesmek için botla aynı ses kanalında olmalısınız", delete_after=25)

    @command(aliases=["pause"])
    async def duraklat(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_paused() is True:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, şarkı zaten duraklatılmış")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send("Şarkı zaten duraklatılmış", delete_after=25)

            if msg.voice_client.is_paused() is False:
                msg.voice_client.pause()
                return await msg.message.add_reaction(emoji='⏸️')

    @command(aliases=["resume"])
    async def devam(self, msg):
        if msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.is_paused() is False:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, şarkı zaten oynatılıyor")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send("Şarkı zaten oynatılıyor", delete_after=25)

            if msg.voice_client.is_paused() is True:
                msg.voice_client.resume()
                return await msg.message.add_reaction(emoji='▶️')

    @command(name='sıradakiler', aliases=['queue', 'q'])
    async def _queue(self, msg):
        if msg.voice_client is not None:
            if msg.guild.id in self.player:
                if self.player[msg.guild.id]['queue']:
                    kontrol = len(self.player[msg.guild.id]['queue'])
                    if kontrol > 1 and kontrol <= 20:
                        sayac = 1
                        mesaj = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Listede {sarkı_sayısı} tane sarkı var')
                        try:
                            return await msg.send(embed=emb)
                        except Exception:
                            return await msg.send("Botun Bu Komutu Kullanması için `Bağlantı Yerleştir` ve `Tepki Ekle` Yetkisine ihtiyacı vardır.")
                    elif kontrol > 20 and kontrol <= 40:
                        sayac = 1
                        mesaj = ""
                        mesaj1 = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Sayfa 1/2 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][20:40]:
                            mesaj1 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                        emb1.set_footer(text=f'Sayfa 2/2 Şarkı Sayısı {sarkı_sayısı}')
                        embed = await msg.send(embed=emb)
                        await embed.add_reaction('\u25c0')  
                        await embed.add_reaction('\u25b6')
                        pages = [emb, emb1]
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
                            res = await self.bot.wait_for('reaction_add', timeout=200)
                            if res == None:
                                break
                            if res[1].id == msg.author.id:
                                click = str(res[0].emoji)
                    elif kontrol > 40 and kontrol <= 60:
                        sayac = 1
                        mesaj = ""
                        mesaj1 = ""
                        mesaj2 = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Sayfa 1/3 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][20:40]:
                            mesaj1 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                        emb1.set_footer(text=f'Sayfa 2/3 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][40:60]:
                            mesaj2 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                        emb2.set_footer(text=f'Sayfa 3/3 Şarkı Sayısı {sarkı_sayısı}')
                        embed = await msg.send(embed=emb)
                        await embed.add_reaction('\u25c0')  
                        await embed.add_reaction('\u25b6')
                        pages = [emb, emb1, emb2]
                        i = 0
                        click = ""
                        while True:
                            if click == '\u25c0':
                                if i > 0:
                                    i -= 1
                                    await embed.edit(embed=pages[i])
                            elif click == '\u25b6':
                                if i < 2:
                                    i += 1
                                    await embed.edit(embed=pages[i])

                            res = await self.bot.wait_for('reaction_add', timeout=200)
                            if res == None:
                                break
                            if res[1].id == msg.author.id:
                                click = str(res[0].emoji)
                    elif kontrol > 60 and kontrol <= 80:
                        sayac = 1
                        mesaj = ""
                        mesaj1 = ""
                        mesaj2 = ""
                        mesaj3 = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Sayfa 1/4 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][20:40]:
                            mesaj1 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                        emb1.set_footer(text=f'Sayfa 2/4 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][40:60]:
                            mesaj2 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                        emb2.set_footer(text=f'Sayfa 3/4 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][60:80]:
                            mesaj3 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                        emb3.set_footer(text=f'Sayfa 4/4 Şarkı Sayısı {sarkı_sayısı}')
                        embed = await msg.send(embed=emb)
                        await embed.add_reaction('\u25c0')  
                        await embed.add_reaction('\u25b6')
                        pages = [emb, emb1, emb2, emb3]
                        i = 0
                        click = ""
                        while True:
                            if click == '\u25c0':
                                if i > 0:
                                    i -= 1
                                    await embed.edit(embed=pages[i])
                            elif click == '\u25b6':
                                if i < 3:
                                    i += 1
                                    await embed.edit(embed=pages[i])

                            res = await self.bot.wait_for('reaction_add', timeout=200)
                            if res == None:
                                break
                            if res[1].id == msg.author.id:
                                click = str(res[0].emoji)
                    elif kontrol > 80 and kontrol <= 100:
                        sayac = 1
                        mesaj = ""
                        mesaj1 = ""
                        mesaj2 = ""
                        mesaj3 = ""
                        mesaj4 = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Sayfa 1/5 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][20:40]:
                            mesaj1 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                        emb1.set_footer(text=f'Sayfa 2/5 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][40:60]:
                            mesaj2 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                        emb2.set_footer(text=f'Sayfa 3/5 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][60:80]:
                            mesaj3 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                        emb3.set_footer(text=f'Sayfa 4/5 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][80:100]:
                            mesaj4 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                        emb4.set_footer(text=f'Sayfa 5/5 Şarkı Sayısı {sarkı_sayısı}')
                        embed = await msg.send(embed=emb)
                        await embed.add_reaction('\u25c0')  
                        await embed.add_reaction('\u25b6')
                        pages = [emb, emb1, emb2, emb3, emb4]
                        i = 0
                        click = ""
                        while True:
                            if click == '\u25c0':
                                if i > 0:
                                    i -= 1
                                    await embed.edit(embed=pages[i])
                            elif click == '\u25b6':
                                if i < 4:
                                    i += 1
                                    await embed.edit(embed=pages[i])

                            res = await self.bot.wait_for('reaction_add', timeout=200)
                            if res == None:
                                break
                            if res[1].id == msg.author.id:
                                click = str(res[0].emoji)                  
                    elif kontrol > 100 and kontrol <= 120:
                        sayac = 1
                        mesaj = ""
                        mesaj1 = ""
                        mesaj2 = ""
                        mesaj3 = ""
                        mesaj4 = ""
                        mesaj5 = ""
                        for i in self.player[msg.guild.id]['queue'][:20]:
                            mesaj += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                        emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                        emb.set_footer(text=f'Sayfa 1/6 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][20:40]:
                            mesaj1 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                        emb1.set_footer(text=f'Sayfa 2/6 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][40:60]:
                            mesaj2 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                        emb2.set_footer(text=f'Sayfa 3/6 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][60:80]:
                            mesaj3 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                        emb3.set_footer(text=f'Sayfa 4/6 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][80:100]:
                            mesaj4 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                        emb4.set_footer(text=f'Sayfa 5/6 Şarkı Sayısı {sarkı_sayısı}')
                        for i in self.player[msg.guild.id]['queue'][100:120]:
                            mesaj5 += f"**{sayac}.** {i['title']}\n"
                            sayac += 1
                        emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                        emb5.set_footer(text=f'Sayfa 6/6 Şarkı Sayısı {sarkı_sayısı}')
                        embed = await msg.send(embed=emb)
                        await embed.add_reaction('\u25c0')  
                        await embed.add_reaction('\u25b6')
                        pages = [emb, emb1, emb2, emb3, emb4, emb5]
                        i = 0
                        click = ""
                        while True:
                            if click == '\u25c0':
                                if i > 0:
                                    i -= 1
                                    await embed.edit(embed=pages[i])
                            elif click == '\u25b6':
                                if i < 5:
                                    i += 1
                                    await embed.edit(embed=pages[i])

                            res = await self.bot.wait_for('reaction_add', timeout=200)
                            if res == None:
                                break
                            if res[1].id == msg.author.id:
                                click = str(res[0].emoji)
                    elif kontrol > 120 and kontrol <= 140:
                            sayac = 1
                            mesaj = ""
                            mesaj1 = ""
                            mesaj2 = ""
                            mesaj3 = ""
                            mesaj4 = ""
                            mesaj5 = ""
                            mesaj6 = ""
                            for i in self.player[msg.guild.id]['queue'][:20]:
                                mesaj += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                            emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                            emb.set_footer(text=f'Sayfa 1/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][20:40]:
                                mesaj1 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                            emb1.set_footer(text=f'Sayfa 2/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][40:60]:
                                mesaj2 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                            emb2.set_footer(text=f'Sayfa 3/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][60:80]:
                                mesaj3 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                            emb3.set_footer(text=f'Sayfa 4/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][80:100]:
                                mesaj4 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                            emb4.set_footer(text=f'Sayfa 5/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][100:120]:
                                mesaj5 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                            emb5.set_footer(text=f'Sayfa 6/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][120:140]:
                                mesaj6 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb6 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj6)
                            emb6.set_footer(text=f'Sayfa 7/7 Şarkı Sayısı {sarkı_sayısı}')
                            embed = await msg.send(embed=emb)
                            await embed.add_reaction('\u25c0')  
                            await embed.add_reaction('\u25b6')
                            pages = [emb, emb1, emb2, emb3, emb4, emb5, emb6]
                            i = 0
                            click = ""
                            while True:
                                if click == '\u25c0':
                                    if i > 0:
                                        i -= 1
                                        await embed.edit(embed=pages[i])
                                elif click == '\u25b6':
                                    if i < 6:
                                        i += 1
                                        await embed.edit(embed=pages[i])

                                res = await self.bot.wait_for('reaction_add', timeout=200)
                                if res == None:
                                    break
                                if res[1].id == msg.author.id:
                                    click = str(res[0].emoji)
                    elif kontrol > 140 and kontrol <= 160:
                            sayac = 1
                            mesaj = ""
                            mesaj1 = ""
                            mesaj2 = ""
                            mesaj3 = ""
                            mesaj4 = ""
                            mesaj5 = ""
                            mesaj6 = ""
                            mesaj7 = ""
                            for i in self.player[msg.guild.id]['queue'][:20]:
                                mesaj += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                            emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                            emb.set_footer(text=f'Sayfa 1/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][20:40]:
                                mesaj1 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                            emb1.set_footer(text=f'Sayfa 2/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][40:60]:
                                mesaj2 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                            emb2.set_footer(text=f'Sayfa 3/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][60:80]:
                                mesaj3 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                            emb3.set_footer(text=f'Sayfa 4/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][80:100]:
                                mesaj4 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                            emb4.set_footer(text=f'Sayfa 5/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][100:120]:
                                mesaj5 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                            emb5.set_footer(text=f'Sayfa 6/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][120:140]:
                                mesaj6 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb6 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj6)
                            emb6.set_footer(text=f'Sayfa 7/8 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][140:160]:
                                mesaj7 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb7 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj7)
                            emb7.set_footer(text=f'Sayfa 8/8 Şarkı Sayısı {sarkı_sayısı}')
                            embed = await msg.send(embed=emb)
                            await embed.add_reaction('\u25c0')  
                            await embed.add_reaction('\u25b6')
                            pages = [emb, emb1, emb2, emb3, emb4, emb5, emb6, emb7]
                            i = 0
                            click = ""
                            while True:
                                if click == '\u25c0':
                                    if i > 0:
                                        i -= 1
                                        await embed.edit(embed=pages[i])
                                elif click == '\u25b6':
                                    if i < 7:
                                        i += 1
                                        await embed.edit(embed=pages[i])

                                res = await self.bot.wait_for('reaction_add', timeout=200)
                                if res == None:
                                    break
                                if res[1].id == msg.author.id:
                                    click = str(res[0].emoji)
                    
                    
                            sayac = 1
                            mesaj = ""
                            mesaj1 = ""
                            mesaj2 = ""
                            mesaj3 = ""
                            mesaj4 = ""
                            mesaj5 = ""
                            mesaj6 = ""
                            mesaj7 = ""
                            mesaj8 = ""
                            for i in self.player[msg.guild.id]['queue'][:20]:
                                mesaj += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                            emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                            emb.set_footer(text=f'Sayfa 1/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][20:40]:
                                mesaj1 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                            emb1.set_footer(text=f'Sayfa 2/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][40:60]:
                                mesaj2 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                            emb2.set_footer(text=f'Sayfa 3/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][60:80]:
                                mesaj3 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                            emb3.set_footer(text=f'Sayfa 4/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][80:100]:
                                mesaj4 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                            emb4.set_footer(text=f'Sayfa 5/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][100:120]:
                                mesaj5 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                            emb5.set_footer(text=f'Sayfa 6/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][120:140]:
                                mesaj6 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb6 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj6)
                            emb6.set_footer(text=f'Sayfa 7/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][140:160]:
                                mesaj7 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb7 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj7)
                            emb7.set_footer(text=f'Sayfa 7/7 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][160:180]:
                                mesaj8 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb8 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj8)
                            emb8.set_footer(text=f'Sayfa 7/7 Şarkı Sayısı {sarkı_sayısı}')
                            embed = await msg.send(embed=emb)
                            await embed.add_reaction('\u25c0')  
                            await embed.add_reaction('\u25b6')
                            pages = [emb, emb1, emb2, emb3, emb4, emb5, emb6, emb7, emb8]
                            i = 0
                            click = ""
                            while True:
                                if click == '\u25c0':
                                    if i > 0:
                                        i -= 1
                                        await embed.edit(embed=pages[i])
                                elif click == '\u25b6':
                                    if i < 8:
                                        i += 1
                                        await embed.edit(embed=pages[i])

                                res = await self.bot.wait_for('reaction_add', timeout=60)
                                if res == None:
                                    break
                                if res[1].id == msg.author.id:
                                    click = str(res[0].emoji)
                    elif kontrol > 160 and kontrol <= 180:
                            sayac = 1
                            mesaj = ""
                            mesaj1 = ""
                            mesaj2 = ""
                            mesaj3 = ""
                            mesaj4 = ""
                            mesaj5 = ""
                            mesaj6 = ""
                            mesaj7 = ""
                            mesaj8 = ""
                            for i in self.player[msg.guild.id]['queue'][:20]:
                                mesaj += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                            emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                            emb.set_footer(text=f'Sayfa 1/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][20:40]:
                                mesaj1 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                            emb1.set_footer(text=f'Sayfa 2/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][40:60]:
                                mesaj2 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                            emb2.set_footer(text=f'Sayfa 3/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][60:80]:
                                mesaj3 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                            emb3.set_footer(text=f'Sayfa 4/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][80:100]:
                                mesaj4 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                            emb4.set_footer(text=f'Sayfa 5/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][100:120]:
                                mesaj5 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                            emb5.set_footer(text=f'Sayfa 6/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][120:140]:
                                mesaj6 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb6 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj6)
                            emb6.set_footer(text=f'Sayfa 7/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][140:160]:
                                mesaj7 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb7 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj7)
                            emb7.set_footer(text=f'Sayfa 8/9 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][160:180]:
                                mesaj8 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb8 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj8)
                            emb8.set_footer(text=f'Sayfa 9/9 Şarkı Sayısı {sarkı_sayısı}')
                            embed = await msg.send(embed=emb)
                            await embed.add_reaction('\u25c0')  
                            await embed.add_reaction('\u25b6')
                            pages = [emb, emb1, emb2, emb3, emb4, emb5, emb6, emb7, emb8]
                            i = 0
                            click = ""
                            while True:
                                if click == '\u25c0':
                                    if i > 0:
                                        i -= 1
                                        await embed.edit(embed=pages[i])
                                elif click == '\u25b6':
                                    if i < 8:
                                        i += 1
                                        await embed.edit(embed=pages[i])

                                res = await self.bot.wait_for('reaction_add', timeout=200)
                                if res == None:
                                    break
                                if res[1].id == msg.author.id:
                                    click = str(res[0].emoji)
                    elif kontrol > 180 and kontrol <= 200:
                            sayac = 1
                            mesaj = ""
                            mesaj1 = ""
                            mesaj2 = ""
                            mesaj3 = ""
                            mesaj4 = ""
                            mesaj5 = ""
                            mesaj6 = ""
                            mesaj7 = ""
                            mesaj8 = ""
                            mesaj9 = ""
                            for i in self.player[msg.guild.id]['queue'][:20]:
                                mesaj += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            sarkı_sayısı = len(self.player[msg.guild.id]['queue'])
                            emb = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj)
                            emb.set_footer(text=f'Sayfa 1/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][20:40]:
                                mesaj1 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb1 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj1)
                            emb1.set_footer(text=f'Sayfa 2/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][40:60]:
                                mesaj2 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb2 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj2)
                            emb2.set_footer(text=f'Sayfa 3/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][60:80]:
                                mesaj3 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb3 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj3)
                            emb3.set_footer(text=f'Sayfa 4/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][80:100]:
                                mesaj4 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb4 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj4)
                            emb4.set_footer(text=f'Sayfa 5/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][100:120]:
                                mesaj5 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb5 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj5)
                            emb5.set_footer(text=f'Sayfa 6/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][120:140]:
                                mesaj6 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb6 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj6)
                            emb6.set_footer(text=f'Sayfa 7/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][140:160]:
                                mesaj7 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb7 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj7)
                            emb7.set_footer(text=f'Sayfa 8/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][160:180]:
                                mesaj8 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb8 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj8)
                            emb8.set_footer(text=f'Sayfa 9/10 Şarkı Sayısı {sarkı_sayısı}')
                            for i in self.player[msg.guild.id]['queue'][180:200]:
                                mesaj9 += f"**{sayac}.** {i['title']}\n"
                                sayac += 1
                            emb9 = discord.Embed(colour=msg.guild.me.color, title='Sıradakiler', description=mesaj9)
                            emb9.set_footer(text=f'Sayfa 10/10 Şarkı Sayısı {sarkı_sayısı}')
                            embed = await msg.send(embed=emb)
                            await embed.add_reaction('\u25c0')  
                            await embed.add_reaction('\u25b6')
                            pages = [emb, emb1, emb2, emb3, emb4, emb5, emb6, emb7, emb8, emb9]
                            i = 0
                            click = ""
                            while True:
                                if click == '\u25c0':
                                    if i > 0:
                                        i -= 1
                                        await embed.edit(embed=pages[i])
                                elif click == '\u25b6':
                                    if i < 9:
                                        i += 1
                                        await embed.edit(embed=pages[i])

                                res = await self.bot.wait_for('reaction_add', timeout=200)
                                if res == None:
                                    break
                                if res[1].id == msg.author.id:
                                    click = str(res[0].emoji)
        emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, sırada şarkı yok")
        try:
            return await msg.send(embed=emb)
        except Exception:
            return await msg.send("Sırada şarkı yok", delete_after=25)

    @command(name='çalan', aliases=['np'])
    async def song_info(self, msg):
        if msg.voice_client is not None and msg.voice_client.is_playing() is True:
            emb = discord.Embed(colour=msg.guild.me.color, title='Şuanda Oynatılan', description=self.player[msg.guild.id]['player'].title)
            emb.set_footer(text="Coded By Erdem")
            emb.set_thumbnail(url=self.player[msg.guild.id]['player'].thumbnail)
            return await msg.send(embed=emb)
        emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, oynatılan şarkı yok")
        try:
            return await msg.send(embed=emb, delete_after=25)
        except Exception:
            return await msg.send("Oynatılan şarkı yok", delete_after=25)

    @command(aliases=["k", "join"])
    async def katıl(self, msg, *, channel: discord.VoiceChannel = None):
        if msg.voice_client is not None:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, zaten bir ses kanalında")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Zaten bir ses kanalında", delete_after=25)

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
            emb = discord.Embed(color= discord.Color.red(), description=f"{msg.author.mention}, bir ses kanalında değilsin")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Bir ses kanalında değilsin", delete_after=25)

    @katıl.error
    async def join_error(self, msg, error):
        if isinstance(error, commands.BadArgument):
            return msg.send(error)

        if error.args[0] == 'Command raised an exception: Exception: playing':
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın", delete_after=25)


    @command(aliases=['volume', 'v'])
    async def ses(self, msg, vol: int=None):
        if vol is None and msg.author.voice is not None and msg.voice_client is not None:
            if msg.voice_client.channel == msg.author.voice.channel and msg.voice_client.is_playing() is True:
                emb = discord.Embed(color=msg.guild.me.color, title=f"Ses seviyesi **%{round(self.player[msg.guild.id]['volume'] * 100)}**")
                first_embed = await msg.send(embed=emb, delete_after=120)
                await first_embed.add_reaction("\u2795")
                await first_embed.add_reaction("\u2796")
                click = ""
                while True:
                    if click == "\u2795":
                        if self.player[msg.guild.id]['volume'] < 2.0:
                            self.player[msg.guild.id]['volume'] += 0.25
                            msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
                            positive_embed = discord.Embed(color=msg.guild.me.color, title=f"Ses seviyesi **%{round(self.player[msg.guild.id]['volume'] * 100)}**")
                            await first_embed.edit(embed=positive_embed)
                    if click == "\u2796":
                        if self.player[msg.guild.id]['volume'] > 0.0:
                            self.player[msg.guild.id]['volume'] -= 0.25
                            msg.voice_client.source.volume = self.player[msg.guild.id]['volume']
                            negative_embed = discord.Embed(color=msg.guild.me.color, title=f"Ses seviyesi **%{round(self.player[msg.guild.id]['volume'] * 100)}**")
                            await first_embed.edit(embed=negative_embed)
                    try:
                        res = await self.bot.wait_for('reaction_add', timeout=45)
                    except Exception:
                        hata = discord.Embed(color=msg.guild.me.color, title=f"Ses seviyesi **%{round(self.player[msg.guild.id]['volume'] * 100)}**")
                        hata.set_footer(text="butonlar artık işlevsiz")
                        await first_embed.edit(embed=hata)
                        break
                    if res is None:
                        break
                    if res[1].id == msg.author.id:
                        click = str(res[0].emoji)

        if vol == 31:
            await msg.send("Yoksa 31mi hocam işte buna kaza derim", delete_after=60)
            vol = 31
        if vol > 200:
            vol = 200
        vol = vol/100
        if msg.author.voice is not None:
            if msg.voice_client is not None:
                if msg.voice_client.channel == msg.author.voice.channel and msg.voice_client.is_playing() is True:
                    msg.voice_client.source.volume = vol
                    self.player[msg.guild.id]['volume'] = vol
                    return await msg.message.add_reaction(emoji='🔊')
        emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, komutu kullanmak için lütfen botla aynı ses kanalına katılın")
        try:
            return await msg.send(embed=emb, delete_after=25)
        except Exception:
            return await msg.send("Komutu kullanmak için lütfen botla aynı ses kanalına katılın", delete_after=25)

    @ses.error
    async def volume_error(self, msg, error):
        if isinstance(error, commands.MissingPermissions):
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, ses seviyesini değiştirmek için gerekli kanalları veya izinlerini kontrol edin.")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Ses seviyesini değiştirmek için gerekli kanalları veya izinlerini kontrol edin.", delete_after=25)

    @staticmethod
    async def spotify_check(member):
        index = 0
        devammı = True
        for i in member.activities:
            try:
                if i.title:
                    devammı = False
                    break
                index += 1
            except Exception:
                index += 1
                continue
        return devammı, index
    
    @command(aliases=["sp"])
    async def spotify(self, msg, *member: discord.Member):
        if len(member) == 0:
            member = msg.author
        index = 0
        devammı = False
        for i in member.activities:
            try:
                if i.title:
                    devammı = True
                    break
                index += 1
            except Exception:
                index += 1
                continue
            
        if devammı is False:
            emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, spotify dinlemiyorsun.")
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send("Spotify dinlemiyorsun.", delete_after=25)
            
            
        elif devammı is True:
            title = "."
            count = 0
            try:
                while True:
                    if title != ".":
                        await asyncio.sleep(1)
                    
                    if self.stopSpotify is True:
                        self.stopSpotify = False
                        break

                    if member.activity == None:
                        await asyncio.sleep(1.5)
                        if member.activity == None:
                            await asyncio.sleep(5)
                            if member.activity == None:
                                await asyncio.sleep(10)
                                if member.activity == None:
                                    emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention} [{member.mention}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.")
                                    try:
                                        await msg.send(embed=emb, delete_after=60)
                                    except Exception:
                                        await msg.send(f"{msg.author.mention} [{member.name}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.", delete_after=60)
                                    break
                    elif member.activity != None:
                        result = await self.spotify_check(member)
                        if result[0]:
                            await asyncio.sleep(1.5)
                            result = await self.spotify_check(member)
                            if result[0]:
                                await asyncio.sleep(5)
                                result = await self.spotify_check(member)
                                if result[0]:
                                    await asyncio.sleep(10)
                                    result = await self.spotify_check(member)
                                    if result[0]:
                                        emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention} [{member.mention}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.")
                                        try:
                                            await msg.send(embed=emb, delete_after=60)
                                        except Exception:
                                            await msg.send(f"{msg.author.mention} [{member.name}] Kullanıcısı artık spotify dinlemiyor döngüden çıkıldı.", delete_after=60)
                                        break
                                    else:
                                        index = result[1]
                                else:
                                    index = result[1]
                            else:
                                index = result[1]
                        else:
                            index = result[1]
                                           
                    try:
                        if member.activities[index].title != title:
                            title = member.activities[index].title
                            song = f"{member.activities[index].title} {member.activities[index].artist}"

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
                    except Exception:
                        hata = await self.spotify_check(member)
                        index = hata[1]
                        continue
            except Exception:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention} bir hata meydana geldi döngüden çıkılıyor!")
                try:
                    await msg.send(embed=emb, delete_after=25)
                except Exception:
                    await msg.send(f"{msg.author.mention} Bir Hata Meydana Geldi Döngüden Çıkılıyor!", delete_after=25)

    @spotify.before_invoke
    async def before_play(self, msg):
        if msg.author.voice is None:
            emb = discord.Embed(color=discord.Color.red(), description='Müzik çalmak için lütfen bir ses kanalına katılın')
            try:
                return await msg.send(embed=emb, delete_after=25)
            except Exception:
                return await msg.send('Müzik çalmak için lütfen bir ses kanalına katılın', delete_after=25)

        if msg.voice_client is None:
            return await msg.author.voice.channel.connect()

        if msg.voice_client.channel != msg.author.voice.channel:
            if msg.voice_client.is_playing() is False and not self.player[msg.guild.id]['queue']:
                return await msg.voice_client.move_to(msg.author.voice.channel)

            if self.player[msg.guild.id]['queue']:
                emb = discord.Embed(color=discord.Color.red(), description=f"{msg.author.mention}, sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın")
                try:
                    return await msg.send(embed=emb, delete_after=25)
                except Exception:
                    return await msg.send("Sıraya şarkı eklemek için lütfen botla aynı ses kanalına katılın", delete_after=25)


def setup(bot):
    bot.add_cog(MusicPlayer(bot))
