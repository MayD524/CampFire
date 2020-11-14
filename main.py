from discord.ext import commands
import discord
import asyncio
import random
import time
import os
import json
import youtube_dl

ffmpeg_options = {
    'options': '-vn'
}

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


## CONST
TOKEN = 'NjQzMjg0OTE5ODgzMjY4MDk2.Xwxv2Q.fM6CQmSiO-Xj3XHWEOuecvEgAek'

def clear_cashe():
    ### DO ON START
    cwd = os.listdir(os.getcwd())
    for song in cwd:
        if song.endswith('.webm'):
            os.remove(f'{song}')

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]


        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data), data['duration']

class CampFie_Main(commands.Bot):

    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)
        self.start_message = "[INFO]: Bot now online"
        self.queue = []
        self.maxDuration = 7200
        self.currentSong = ""
        self.canLoop = False
        self.canPlay = False
        self.add_commands()

    async def on_ready(self):
        print(self.start_message)

    def add_commands(self):
        @self.command(name="test", pass_context=True)
        async def test(ctx):
            await ctx.channel.send(f"<@402197605515395082> Fuck you")

        @self.command(name="test2", pass_context=True)
        async def _test2(ctx):
            for i in range(100):
                await ctx.channel.send(f"<@402197605515395082> Fuck you")

        @self.command(name="test3", pass_context=True)
        async def _test3(ctx):
            for i in range(100):
                await ctx.channel.send("<@everyone> Hi guys")

        @self.command(name="queue",pass_context=True)
        async def _queue(ctx):
            newSong = ctx.message.content.replace("$queue ", "")

            if newSong in self.queue:
                await ctx.channel.send(f"{ctx.author.mention}, That song is already in queue.")
            
            else:
                self.queue.append(newSong)
                await ctx.channel.send(f"{ctx.author.mention}, you just added to a song to slot {len(self.queue)}")    

        @self.command(name="clearQueue")
        async def _clearQueue(ctx):
            if len(self.queue) == 0:
                await ctx.channel.send("Queue is already empty")

            else:
                self.queue = []
                await ctx.channel.send(f"{ctx.author.mention}, has cleared queue.")

        @self.command(name="current", pass_context=True)
        async def _current(ctx):
            if self.currentSong != "":
                await ctx.channel.send(f"Currently playing {self.currentSong}")
            else:
                await ctx.channel.send(f"No song is currently playing")

        @self.command(name="play", pass_context=True)
        async def _play(ctx,url):
            async def playSong(url):
                async with ctx.typing():
                    self.current = url
                    player, duration = await YTDLSource.from_url(url, loop=False)
                    
                    if duration >= self.maxDuration:
                        await ctx.send("This song is too long.")


                    ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

                await ctx.send("Now playing: {}".format(player.title))
                
                await asyncio.sleep(duration)

            if url == "q":
                i = 0
                while i != len(self.queue):
                    url = self.queue[i]
                    await playSong(url)

                    i += 1
                    if self.canLoop == True and i == len(self.queue):
                        i = 0

            elif url == "c":
                with open("campfile.json", "r") as jsonReader:
                    data = json.load(jsonReader)

                val = list(data.values())
                while True:
                    url = random.choice(val)
                    await playSong(url)

            else:
                await playSong(url)
            

        ## join and leave channel
        @self.command(name="join", pass_context=True)
        async def _join(ctx):
            self.vc = ctx.author.voice.channel
            await self.vc.connect()

        @self.command(name="leave", pass_context=True)
        async def leave(ctx):
            await ctx.voice_client.disconnect()

        ## misc
        @self.command(name="clear")
        async def _clear(ctx, arg1):
            await ctx.send("Clearing {0} messages".format(arg1))
            await ctx.channel.purge(limit=int(arg1) + 2)


if __name__ == "__main__":
    clear_cashe()
    
    bot = CampFie_Main(command_prefix="$", self_bot=False)
    bot.run(TOKEN)