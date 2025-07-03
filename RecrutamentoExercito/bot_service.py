import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from security import CHAVEROBO
import servicemanager
import win32serviceutil
import win32service
import win32event
import time
import sys

# IDs dos canais e cargos
ADVOCATE_CHANNEL_ID = 1314325019295350814
PM_CHANNEL_ID = 1314325058243793097
ADVOCATE_ROLE_ID = 1289031240258945044
ROLES_TO_REMOVE = [1289031240258945038]

# Configuração do bot e intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Função para extração de ID no apelido
def extrair_id_apelido(apelido: str) -> str:
    try:
        return apelido.split('|')[-1].strip()
    except IndexError:
        return None

async def localizar_membro_por_id(guild: discord.Guild, id_busca: str) -> discord.Member:
    for member in guild.members:
        if member.nick:
            id_no_apelido = extrair_id_apelido(member.nick)
            if id_no_apelido == id_busca:
                return member
    return None

class WelcomeModal(Modal):
    def __init__(self, is_adv: bool):
        super().__init__(title="Preencha suas informações")
        self.is_adv = is_adv

        # Campos do modal
        self.qra = TextInput(label="QUAL SEU NOME?" if self.is_adv else "SEU QRA?", placeholder="Insira seu nome" if self.is_adv else "Insira seu QRA")
        self.passaporte = TextInput(label="SEU PASSAPORTE (ID)?", placeholder="Insira seu passaporte")
        self.cargo = TextInput(label="SEU CARGO NA OAB?" if self.is_adv else "CARGO", placeholder="Insira seu cargo")
        
        if not self.is_adv:
            self.recrutador = TextInput(label="QUEM TE RECRUTOU?", placeholder="Coloque o ID do Recrutador")
            self.add_item(self.recrutador)

        # Adicionar os campos ao modal
        self.add_item(self.qra)
        self.add_item(self.passaporte)
        self.add_item(self.cargo)

    async def on_submit(self, interaction: discord.Interaction):
        # Determina o prefixo baseado no tipo de registro
        prefix = "[ADV]" if self.is_adv else "[REC]"
        await self.process_submission(interaction, prefix)

    async def process_submission(self, interaction: discord.Interaction, prefix: str):
        try:
            # Obtendo os valores dos campos
            qra = self.qra.value
            passaporte = self.passaporte.value
            cargo = self.cargo.value
            recrutador = self.recrutador.value if not self.is_adv else "N/A"

            # Formatação do novo apelido
            novo_apelido = f"{prefix} {qra} | {passaporte}"

            # Alteração do apelido do usuário
            try:
                await interaction.user.edit(nick=novo_apelido)
            except discord.Forbidden:
                await interaction.response.send_message("⚠ Não tenho permissão para alterar o apelido.", ephemeral=True)
                return

            await interaction.response.send_message(f"QRA alterado para: {novo_apelido}", ephemeral=True)

            # Se for advogado, atribuir o cargo específico e remover os cargos
            if self.is_adv:
                role = interaction.guild.get_role(ADVOCATE_ROLE_ID)  # Obtém o cargo do advogado
                if role:
                    try:
                        await interaction.user.add_roles(role)  # Adiciona o cargo ao usuário
                        
                        # Remover os cargos especificados
                        roles_to_remove = [interaction.guild.get_role(role_id) for role_id in ROLES_TO_REMOVE]
                        await interaction.user.remove_roles(*roles_to_remove)
                        print(f"Cargos removidos: {', '.join(role.name for role in roles_to_remove if role)}")  # Log para verificação
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
                    print(f"Mensagem enviada ao canal: {channel.name} (ID: {channel.id})")  # Log para verificação
                else:
                    await interaction.followup.send(f"Canal não encontrado! (ID: {ADVOCATE_CHANNEL_ID})", ephemeral=True)

            else:
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

                # Enviar embed com as informações preenchidas para PM
                embed = discord.Embed(title="Registro Completo - C.O.T", timestamp=discord.utils.utcnow())
                embed.add_field(name="**QRA**", value=qra, inline=False)
                embed.add_field(name="**Passaporte (ID)**", value=passaporte, inline=False)
                embed.add_field(name="**Cargo**", value=cargo, inline=False)

                # Menciona o recrutador no embed
                embed.add_field(name="**Recrutador**", value=f"{membro_recrutador.mention}", inline=False)

                embed.set_thumbnail(url="https://i.ibb.co/MRxFFFd/imagem-2024-11-04-121912694-removebg-preview.png")
                channel = bot.get_channel(PM_CHANNEL_ID)

                if channel:
                    await channel.send(embed=embed)
                    print(f"Mensagem enviada ao canal: {channel.name} (ID: {channel.id})")  # Log para verificação
                else:
                    await interaction.followup.send(f"Canal não encontrado! (ID: {PM_CHANNEL_ID})", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"⚠ Ocorreu um erro: {str(e)}", ephemeral=True)


class WelcomeView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Define timeout como None para desativar a expiração

    @discord.ui.button(label="Fazer registro de Exército", style=discord.ButtonStyle.blurple, custom_id="register_button_pm", emoji="💀")
    async def button_callback_pm(self, interaction: discord.Interaction, button: Button):
        # Adiciona os dois cargos ao usuário
        role_1 = interaction.guild.get_role(1313996060871364654)
        role_2 = interaction.guild.get_role(1313996060871364653)
        role_3 = interaction.guild.get_role(1313996060913438903)

        try:
            if role_1:
                await interaction.user.add_roles(role_1)  # Adiciona o primeiro cargo
            if role_2:
                await interaction.user.add_roles(role_2)  # Adiciona o segundo cargo
            if role_3:
                await interaction.user.add_roles(role_3)  # Adiciona o segundo cargo
                
            # Enviar o modal de PM
            await interaction.response.send_modal(WelcomeModal(is_adv=False))

        except discord.Forbidden:
            await interaction.response.send_message("⚠ Não tenho permissão para adicionar cargos.", ephemeral=True)

    @discord.ui.button(label="Fazer registro de Advogado", style=discord.ButtonStyle.blurple, custom_id="register_button_adv", emoji="⚖️")
    async def button_callback_adv(self, interaction: discord.Interaction, button: Button):
        # Enviar o modal de advogado
        await interaction.response.send_modal(WelcomeModal(is_adv=True))


@bot.command()
async def registro(ctx):
    class DiscordBotService(win32serviceutil.ServiceFramework):
        _svc_name_ = "DiscordBotService"
        _svc_display_name_ = "Discord Bot Service"
        _svc_description_ = "Executes the Discord bot in the background as a Windows service."

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.stop_requested = False

        def SvcStop(self):
            self.stop_requested = True
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            bot.loop.create_task(bot.close())  # Fecha o bot no evento de parada

        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                servicemanager.PYS_SERVICE_STARTED,
                                (self._svc_name_, ""))
            bot.run(CHAVEROBO)  # Executa o bot

    if __name__ == "__main__":
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(DiscordBotService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(DiscordBotService)
