import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Loged as{0}!'.format(self.user))
    async def on_message(self, message):
        print('Message from{0.author}: {0.content}'.format(message))

client = MyClient()
client.run('MTEyMjI1ODk0NzkzNjYyMDY1Ng.GT9O9Y.hj-mPoLlVAxXMP4mZP5c5pt1ZtlGpT-lZ_zQJs')
