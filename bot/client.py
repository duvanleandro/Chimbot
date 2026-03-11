"""
Configuración del cliente del bot de Discord
"""
import discord
from discord.ext import commands

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# Crear instancia del bot
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)