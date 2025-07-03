import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from security import CHAVEROBO

# IDs dos canais para enviar os embeds
ADVOCATE_CHANNEL_ID = 1314325058243793097  # Canal: registro de advogados
PM_CHANNEL_ID = 1314325058243793097  # Canal: registro de EB
FIREMAN_CHANNEL_ID = 1314325058243793097  # Replace with actual Fireman registration channel ID

# ID dos cargos
ADVOCATE_ROLE_ID = 1313996060695466150  # Cargo: ⚖️・Jurídico
FIREMAN_ROLE_ID = 1314768497129029663  # Replace with actual Fireman role ID

# Cargos a serem removidos ao registrar como advogado
# ROLES_TO_REMOVE = [
#     1289031240258945038
# ]

# Configuração dos intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Necessário para acessar informações de membros

# Inicialização do bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Função para extrair o ID do apelido no formato '[CARGO] Nome | ID'
def extrair_id_apelido(apelido: str) -> str:
    try:
        return apelido.split('|')[-1].strip()  # Extrai a parte após o '|'
    except IndexError:
        return None  # Caso não siga o padrão, retorna None

# Função para localizar o membro pelo ID no apelido
async def localizar_membro_por_id(guild: discord.Guild, id_busca: str) -> discord.Member:
    for member in guild.members:
        if member.nick:  # Verifica se o membro tem apelido
            id_no_apelido = extrair_id_apelido(member.nick)
            if id_no_apelido == id_busca:
                return member  # Retorna o membro cujo ID foi encontrado
    return None  # Retorna None se nenhum membro for encontrado

# Criação do Modal com TextInput para registro
class WelcomeModal(Modal):
    def __init__(self, registration_type: str):
        super().__init__(title="Preencha suas informações")
        self.registration_type = registration_type

        # Campos do modal
        if registration_type == 'adv':
            self.qra = TextInput(label="QUAL SEU NOME?", placeholder="Insira seu nome")
            self.passaporte = TextInput(label="SEU PASSAPORTE (ID)?", placeholder="Insira seu passaporte")
            self.cargo = TextInput(label="SEU CARGO NA OAB?", placeholder="Insira seu cargo")
        elif registration_type == 'pm':
            self.qra = TextInput(label="SEU QRA?", placeholder="Insira seu QRA")
            self.passaporte = TextInput(label="SEU PASSAPORTE (ID)?", placeholder="Insira seu passaporte")
            self.cargo = TextInput(label="CARGO", placeholder="Insira seu cargo")
            self.recrutador = TextInput(label="QUEM TE RECRUTOU?", placeholder="Coloque o ID do Recrutador")
            self.add_item(self.recrutador)
        elif registration_type == 'fireman':
            self.qra = TextInput(label="SEU NOME?", placeholder="Insira seu nome completo")
            self.passaporte = TextInput(label="SEU PASSAPORTE (ID)?", placeholder="Insira seu passaporte")
            self.cargo = TextInput(label="SEU CARGO NO CORPO DE BOMBEIROS?", placeholder="Insira seu cargo")

        # Adicionar os campos ao modal
        self.add_item(self.qra)
        self.add_item(self.passaporte)
        self.add_item(self.cargo)

    async def on_submit(self, interaction: discord.Interaction):
        # Determina o prefixo baseado no tipo de registro
        prefixes = {
            'adv': '[ADV]',
            'pm': '[REC]',
            'fireman': '[BOMB]'
        }
        prefix = prefixes.get(self.registration_type, '[REG]')
        await self.process_submission(interaction, prefix)

    async def process_submission(self, interaction: discord.Interaction, prefix: str):
        try:
            # Obtendo os valores dos campos
            qra = self.qra.value
            passaporte = self.passaporte.value
            cargo = self.cargo.value
            recrutador = getattr(self, 'recrutador', None).value if hasattr(self, 'recrutador') else "N/A"

            # Formatação do novo apelido
            novo_apelido = f"{prefix} {qra} | {passaporte}"

            # Alteração do apelido do usuário
            try:
                await interaction.user.edit(nick=novo_apelido)
            except discord.Forbidden:
                await interaction.response.send_message("⚠ Não tenho permissão para alterar o apelido.", ephemeral=True)
                return

            await interaction.response.send_message(f"QRA alterado para: {novo_apelido}", ephemeral=True)

            # Processamento específico para cada tipo de registro
            if self.registration_type == 'adv':
                role = interaction.guild.get_role(ADVOCATE_ROLE_ID)
                if role:
                    try:
                        await interaction.user.add_roles(role)
                        
                        # Remover os cargos especificados
                        # roles_to_remove = [interaction.guild.get_role(role_id) for role_id in ROLES_TO_REMOVE]
                        # await interaction.user.remove_roles(*roles_to_remove)
                    except discord.Forbidden:
                        await interaction.followup.send("⚠ Não tenho permissão para adicionar cargos.", ephemeral=True)
                        return

                # Enviar embed para advogados
                embed = discord.Embed(title="Registro Completo - Advogado", timestamp=discord.utils.utcnow())
                embed.add_field(name="**QRA**", value=qra, inline=False)
                embed.add_field(name="**Passaporte (ID)**", value=passaporte, inline=False)
                embed.add_field(name="**Cargo**", value=cargo, inline=False)
                embed.set_thumbnail(url="https://camc.oabrj.org.br/camc/home/img/logo_oabrj-01.png")

                channel = bot.get_channel(ADVOCATE_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)

            elif self.registration_type == 'pm':
                # Adicionar cargos de PM
                role_1 = interaction.guild.get_role(1313996060871364654)
                role_2 = interaction.guild.get_role(1313996060871364653)
                role_3 = interaction.guild.get_role(1313996060913438903)

                try:
                    if role_1:
                        await interaction.user.add_roles(role_1)
                    if role_2:
                        await interaction.user.add_roles(role_2)
                    if role_3:
                        await interaction.user.add_roles(role_3)
                except discord.Forbidden:
                    await interaction.followup.send("⚠ Não tenho permissão para adicionar cargos.", ephemeral=True)
                    return

                # Extração do ID a partir do campo "Recrutador" para PM
                id_recrutador = extrair_id_apelido(recrutador)
                if not id_recrutador:
                    await interaction.followup.send("⚠ O ID do recrutador não foi encontrado.", ephemeral=True)
                    return

                # Localiza o membro correspondente ao ID fornecido no campo recrutador
                membro_recrutador = await localizar_membro_por_id(interaction.guild, id_recrutador)
                if not membro_recrutador:
                    await interaction.followup.send("⚠ Não foi possível localizar o recrutador pelo ID fornecido.", ephemeral=True)
                    return

                # Enviar embed para PM
                embed = discord.Embed(title="Registro Completo - Exército", timestamp=discord.utils.utcnow())
                embed.add_field(name="**QRA**", value=qra, inline=False)
                embed.add_field(name="**Passaporte (ID)**", value=passaporte, inline=False)
                embed.add_field(name="**Cargo**", value=cargo, inline=False)
                embed.add_field(name="**Recrutador**", value=f"{membro_recrutador.mention}", inline=False)
                embed.set_thumbnail(url="https://i.ibb.co/yXF0QCS/imagem-2024-12-09-112651378-removebg-preview.png")

                channel = bot.get_channel(PM_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)

            elif self.registration_type == 'fireman':
                # Adicionar cargo de Bombeiro
                role = interaction.guild.get_role(FIREMAN_ROLE_ID)
                
                try:
                    if role:
                        await interaction.user.add_roles(role)
                except discord.Forbidden:
                    await interaction.followup.send("⚠ Não tenho permissão para adicionar cargos.", ephemeral=True)
                    return

                # Extração do ID a partir do campo "Recrutador" para Bombeiros
                id_recrutador = extrair_id_apelido(recrutador)
                if not id_recrutador:
                    await interaction.followup.send("⚠ O ID do recrutador não foi encontrado.", ephemeral=True)
                    return

                # Localiza o membro correspondente ao ID fornecido no campo recrutador
                membro_recrutador = await localizar_membro_por_id(interaction.guild, id_recrutador)
                if not membro_recrutador:
                    await interaction.followup.send("⚠ Não foi possível localizar o recrutador pelo ID fornecido.", ephemeral=True)
                    return

                # Enviar embed para Bombeiros
                embed = discord.Embed(title="Registro Completo - Corpo de Bombeiros", timestamp=discord.utils.utcnow())
                embed.add_field(name="**Nome**", value=qra, inline=False)
                embed.add_field(name="**Passaporte (ID)**", value=passaporte, inline=False)
                embed.add_field(name="**Cargo**", value=cargo, inline=False)
                embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Estado_do_Rio_de_Janeiro.svg/1200px-Bras%C3%A3o_do_Corpo_de_Bombeiros_Militar_do_Estado_do_Rio_de_Janeiro.svg.png")

                channel = bot.get_channel(FIREMAN_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"⚠ Ocorreu um erro: {str(e)}", ephemeral=True)

# Criação da view com botões para registro
class WelcomeView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Define timeout como None para desativar a expiração

    @discord.ui.button(label="Alistamento Militar", style=discord.ButtonStyle.green, custom_id="register_button_pm", emoji="🔫")
    async def button_callback_pm(self, interaction: discord.Interaction, button: Button):
        # Enviar o modal de PM
        await interaction.response.send_modal(WelcomeModal(registration_type='pm'))

    @discord.ui.button(label="Registrar Advogado", style=discord.ButtonStyle.secondary, custom_id="register_button_adv", emoji="⚖️")
    async def button_callback_adv(self, interaction: discord.Interaction, button: Button):
        # Enviar o modal de advogado
        await interaction.response.send_modal(WelcomeModal(registration_type='adv'))

    @discord.ui.button(label="Registrar Bombeiro", style=discord.ButtonStyle.danger, custom_id="register_button_fireman", emoji="🚒")
    async def button_callback_fireman(self, interaction: discord.Interaction, button: Button):
        # Enviar o modal de bombeiro
        await interaction.response.send_modal(WelcomeModal(registration_type='fireman'))

# Comando que enviará o embed de boas-vindas com os botões
@bot.command()
async def registro(ctx):
    embed = discord.Embed(
        title="Registro de EB, Advogado e Bombeiro",
        description=(
            "Bem-vindo ao canal de registro!\n"
            "- Este espaço é dedicado ao cadastramento de militares, advogados e bombeiros que atuarão junto à corporação. Aqui, você poderá registrar seus dados profissionais.\n"
            "- Caso tenha dúvidas durante o registro ou precise de assistência, nossa equipe está à disposição para ajudar.\n"
            "**Att, Comando**\n\n"
            "-# 👾 Desenvolvido por [DEV] Escobar 🚬  /  [DEV] Marcelinho :bread: :wine_glass:"
        ),
        color=discord.Color.dark_green()
    )
    embed.set_thumbnail(url="https://i.ibb.co/yXF0QCS/imagem-2024-12-09-112651378-removebg-preview.png")  # Logo COT 
    view = WelcomeView()
    await ctx.send(embed=embed, view=view)

# Iniciar o bot
bot.run(CHAVEROBO)