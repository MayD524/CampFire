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


## Token
TOKEN = "TOKEN"

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

class CampFire_Main(commands.Bot):

    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)
        self.start_message = "[INFO]: Bot now online"
        self.queue = []
        self.maxDuration = 7200
        self.canLoop = False
        self.add_commands()

    async def on_ready(self):
        print(self.start_message)

    def add_commands(self):
    
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
                
                await asyncio.sleep(duration + 0.3)

            async def play_Queue(queue=None, mode=None, loop=False):
                i = 0
                if loop == True:
                    while True:
                        if mode == "random":
                            song = random.choice(queue)
                            
                        else:
                            if i == len(queue):
                                i = 0
                            else:
                                song = queue[i]
                                i += 1

                        await playSong(song)


                elif loop == False:
                    while i != len(queue):
                        song = queue[i]
                        await playSong(song)

            ## plays queue -> loops through list of all urls
            if url == "q":
                await play_Queue(queue=self.queue,loop=False)

            ## plays campfile.json
            elif url == "c":
                with open("campfile.json", "r") as jsonReader:
                    data = json.load(jsonReader)

                val = list(data.values())
                await play_Queue(queue=val,mode="random",loop=True)

            ## plays user song
            else:
                self.queue.append(url)
                await play_Queue(queue=self.queue,loop=False)
        
        ## pause, resume and stop functions
        @self.command(name="pause",pass_context=True)
        async def _pause(ctx):
            if ctx.voice_client and ctx.voice_client.is_playing():
                ctx.voice_client.pause()
            else:
                await ctx.send("I am not currently playing any songs")

        @self.command(name="resume",pass_context=True)
        async def _resume(ctx):
            if ctx.voice_client and not ctx.voice_client.is_playing():
                ctx.voice_client.resume()
            else:
                await ctx.send("No songs are currently paused")

        @self.command(name="volume", pass_context=True)
        async def _volume(ctx,volume:int):
            ## Changes the players volume
            if ctx.voice_client is None:
                return await ctx.send("Not connect to a voice channel")

            if volume > 200 or volume < 0:
                return await ctx.send("That is not a valid input.")
            ctx.voice_client.source.volume = volume / 100
            await ctx.send("Changed volume to {}%".format(volume))

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

## SCRIPT STARTS HERE
if __name__ == "__main__":
    
    bot = CampFire_Main(command_prefix="$", self_bot=False)
    bot.run(TOKEN)
