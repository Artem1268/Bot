import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Loged as{0}!'.format(self.user))
    async def on_message(self, message):
        print('Message from{0.author}: {0.content}'.format(message))

client = MyClient()
client.run('MTEyMjI1ODk0NzkzNjYyMDY1Ng.G_f0ej.gggsiuw4WpiDDNiSVflxhMJcLixsSpl6Rgo08M')


