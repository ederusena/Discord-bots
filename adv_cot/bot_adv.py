import discord
import asyncio  # Necessário para a função sleep
from discord.ext import commands
from datetime import datetime, timedelta  # Importar para manipulação de datas

from dotenv import load_dotenv
import os

# Carregar o .env
load_dotenv()

# Acessar o token
DISCORD_TOKEN = os.getenv("MTMxMjkyODE2OTA2MTM4NDE5Mg.Gnn7Lp.TfIFOKrOFr4DK8JWqBkm4UL9XjPGWSs_wWtl94")

# Exemplo de uso do token
print(f"O token é: {DISCORD_TOKEN}")


# Intents são necessárias para conseguir pegar informações de membros e eventos de mensagens
intents = discord.Intents.default()
intents.members = True  # Necessário para gerenciar cargos de membros

# Definir o prefixo dos comandos e passar os intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Defina o ID do canal específico onde o bot vai monitorar as mensagens
MONITOR_CHANNEL_ID = 1305634673074110566  # Substitua pelo ID do seu canal

# Defina um dicionário que mapeia os IDs dos cargos aos tempos de duração (em dias)
ROLE_DURATION = {
    1305654442326102066: 7,    # O cargo com ID 1305654442326102066 será removido após 7 dias
    1305654205440069663: 14,   # O cargo com ID 1305654205440069663 será removido após 14 dias
    1305654275086487603: 25    # O cargo com ID 1305654275086487603 será removido após 25 dias
}

@bot.event
async def on_ready():
    print(f'Bot está pronto. Logado como {bot.user}')

@bot.event
async def on_message(message):
    # Verifica se a mensagem foi enviada no canal específico e não foi enviada pelo bot
    if message.channel.id == MONITOR_CHANNEL_ID and not message.author.bot:
        # Verifica se há menção de um usuário e de um cargo na mensagem
        if message.mentions and message.role_mentions:
            mentioned_user = message.mentions[0]  # Pega o primeiro usuário mencionado
            mentioned_role = None  # Inicialmente, o cargo não é definido

            # Iterar sobre os cargos mencionados na ordem e encontrar o primeiro cargo permitido
            for role in message.role_mentions:
                if role.id in ROLE_DURATION:  # Verifica se o cargo está no dicionário ROLE_DURATION
                    mentioned_role = role
                    break  # Pega o primeiro cargo permitido e interrompe o loop

            # Verifica se encontrou um cargo permitido
            if mentioned_role:
                # Adiciona o primeiro cargo permitido ao primeiro usuário mencionado
                await mentioned_user.add_roles(mentioned_role)

                # Obtem a duração do cargo
                role_duration_days = ROLE_DURATION.get(mentioned_role.id)

                # Converte dias para segundos
                role_duration_seconds = role_duration_days * 86400

                # Calcula a data de expiração
                expiration_date = datetime.now() + timedelta(days=role_duration_days)
                formatted_expiration_date = expiration_date.strftime("%d/%m/%y")  # Formata a data

                await message.channel.send(f"**{mentioned_role.name} foi atribuído a** {mentioned_user.mention}.\n"
                                           f"-# <:relogio:1285856612736827502> Esta advertência expira em: {formatted_expiration_date}.")

                # Espera o tempo definido para o cargo específico
                await asyncio.sleep(role_duration_seconds)

                # Remove o cargo após o tempo estipulado
                await mentioned_user.remove_roles(mentioned_role)
                await message.channel.send(f"**🔔 A {mentioned_role.name} de {mentioned_user.mention} acaba de expirar.**")
            else:
                # Caso nenhum cargo permitido seja mencionado
                await message.channel.send("❌ **Nenhum cargo permitido foi mencionado.**", ephemeral=True)
        else:
            await message.channel.send("🔎 **Por favor, mencione um usuário e um cargo válido.**", ephemeral=True)  # Isso faz com que a mensagem seja ephémera))
    
    # Permite que outros comandos do bot sejam processados
    await bot.process_commands(message)

# Rodar o bot
bot.run("MTMxMjkyODE2OTA2MTM4NDE5Mg.Gnn7Lp.TfIFOKrOFr4DK8JWqBkm4UL9XjPGWSs_wWtl94")