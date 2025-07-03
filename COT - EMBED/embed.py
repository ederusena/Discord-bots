import discord
from discord.ext import commands
from config import CHAVEEMBED # Certifique-se de que o arquivo config.py contém seu token

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Modal para coletar informações para o embed
class EmbedModal(discord.ui.Modal, title="Criar Embed"):
    def __init__(self):
        super().__init__()

        self.add_item(discord.ui.TextInput(label="Miniatura (Link da imagem)", required=False))
        self.add_item(discord.ui.TextInput(label="Imagem (Link da imagem)", required=False))
        self.add_item(discord.ui.TextInput(label="Título", required=True))
        self.add_item(discord.ui.TextInput(label="Descrição", style=discord.TextStyle.long, required=True))
        self.add_item(discord.ui.TextInput(label="Subtexto", style=discord.TextStyle.long, required=False))

    async def on_submit(self, interaction: discord.Interaction):
        # Armazena os dados do modal
        self.data = {
            "thumbnail": self.children[0].value,
            "image": self.children[1].value,
            "title": self.children[2].value,
            "description": self.children[3].value,
            "subtext": self.children[4].value,
        }

        # A cor é fixa e será sempre preta
        color = discord.Color.default()

        # Cria o embed com as informações fornecidas
        embed = discord.Embed(title=self.data["title"], description=self.data["description"], color=color)

        if self.data["thumbnail"]:
            embed.set_thumbnail(url=self.data["thumbnail"])
        if self.data["image"]:
            embed.set_image(url=self.data["image"])
        if self.data["subtext"]:
            embed.add_field(name="Subtexto", value=self.data["subtext"], inline=False)

        print(self.data)
        
        # Envia o embed para o canal
        if interaction.channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("Embed enviado com sucesso!", ephemeral=True)
        else:
            await interaction.response.send_message("Não tenho permissão para enviar mensagens neste canal.", ephemeral=True)
        await interaction.response.send_message("Embed enviado com sucesso!", ephemeral=True)

# Comando para abrir o modal
@bot.tree.command(name="criarembed")
async def create_embed_command(interaction: discord.Interaction):
    """Comando para criar um embed com informações personalizadas."""
    await interaction.response.send_modal(EmbedModal())

# Sincroniza os comandos de barra ao iniciar o bot
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot {bot.user} está online e pronto para uso!")

bot.run(CHAVEEMBED)
