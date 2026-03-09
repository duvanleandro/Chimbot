"""
Comandos del bot de Discord
"""
import discord
from discord.ext import commands
from config import (
    RESPUESTAS, CANAL_SPAM_ID, CANAL_MEMES_ID, ZORCUZ_ID,
    mensajes_random, obtener_mensaje_sin_repetir
)
from utils import obtener_meme_shitpost


def setup_commands(bot):
    """Registra todos los comandos del bot"""
    
    @bot.command(name='help')
    async def ayuda(ctx, categoria=None):
        """Comando de ayuda con subcategorías: user, admin"""
        es_admin = ctx.author.guild_permissions.administrator
        
        if categoria is None:
            mensaje = "**OPCIONES DE AYUDA:**\n\n"
            mensaje += "`$help user` - Ver comandos de usuario\n"
            if es_admin:
                mensaje += "`$help admin` - Ver comandos de administrador\n"
            await ctx.send(mensaje)
        
        elif categoria.lower() == 'user':
            mensaje = "**COMANDOS DE USUARIO:**\n"
            mensaje += '\n'.join(RESPUESTAS['general']['usuario'])
            await ctx.send(mensaje)
        
        elif categoria.lower() == 'admin':
            if es_admin:
                mensaje = "**COMANDOS DE ADMINISTRADOR:**\n"
                mensaje += '\n'.join(RESPUESTAS['general']['admin'])
                await ctx.send(mensaje)
            else:
                await ctx.send("No tienes permisos para ver los comandos de administrador.")
        
        elif categoria.lower() == 'personas':
            comandos = '\n'.join([f'`${cmd}`' for cmd in RESPUESTAS['personas'].keys()])
            mensaje = "**COMANDOS DE PERSONAS:**\n" + comandos
            await ctx.send(mensaje)
        
        else:
            await ctx.send("Categoría no encontrada. Usa `$help` para ver las opciones disponibles.")

    @bot.command(name='testspam')
    async def test_spam(ctx):
        """Comando para probar el sistema de spam manualmente"""
        if not mensajes_random:
            await ctx.send("**ERROR:** No hay mensajes configurados.")
            return
        
        canal = bot.get_channel(CANAL_SPAM_ID)
        if canal:
            mensaje = obtener_mensaje_sin_repetir()
            await canal.send(mensaje)
            await ctx.send(f"Mensaje de prueba enviado a <#{CANAL_SPAM_ID}>")
        else:
            await ctx.send("No se encontró el canal de spam.")

    @bot.command(name='activarspam')
    @commands.has_permissions(administrator=True)
    async def activar_spam(ctx):
        """Activa el sistema de spam automático (solo admins)"""
        from .tasks import spam_periodico
        
        if not mensajes_random:
            await ctx.send("**ERROR:** No hay mensajes configurados.")
            return
        
        if spam_periodico.is_running():
            await ctx.send("El spam automático ya está activo.")
        else:
            spam_periodico.start()
            await ctx.send("Spam automático **ACTIVADO**.")

    @bot.command(name='desactivarspam')
    @commands.has_permissions(administrator=True)
    async def desactivar_spam(ctx):
        """Desactiva el sistema de spam automático (solo admins)"""
        from .tasks import spam_periodico
        
        if spam_periodico.is_running():
            spam_periodico.cancel()
            await ctx.send("Spam automático **DESACTIVADO**.")
        else:
            await ctx.send("El spam automático ya está desactivado.")

    @bot.command(name='statusspam')
    async def status_spam(ctx):
        """Muestra el estado del sistema de spam"""
        from .tasks import spam_periodico
        
        estado = "**ACTIVO**" if spam_periodico.is_running() else "**INACTIVO**"
        info = f"""**Estado del Sistema de Spam:**
{estado}
Mensajes configurados: {len(mensajes_random)}
Canal: <#{CANAL_SPAM_ID}>"""
        await ctx.send(info)

    @bot.command(name='borrar')
    @commands.has_permissions(manage_messages=True)
    async def borrar_mensajes(ctx, cantidad: int):
        """Borra una cantidad específica de mensajes del canal"""
        if cantidad <= 0:
            await ctx.send("digame como borro 0 mensajes. Estupido.", delete_after=5)
            return
        
        if cantidad > 100:
            await ctx.send("No sea abusivo, solo puedo borrar 100 mensajes", delete_after=5)
            return
        
        try:
            await ctx.message.delete()
            mensajes_borrados = await ctx.channel.purge(limit=cantidad)
            confirmacion = await ctx.send(f"Se borraron **{len(mensajes_borrados)}** mensajes.")
            await confirmacion.delete(delay=3)
        except discord.Forbidden:
            await ctx.send("No tengo permisos para borrar mensajes.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"Error al borrar mensajes: {e}", delete_after=5)

    @bot.command(name='permisos')
    async def ver_permisos(ctx):
        """Muestra todos los permisos que tiene el bot"""
        permisos_servidor = ctx.guild.me.guild_permissions
        
        permisos_importantes = {
            'Administrador': 'administrator',
            'Gestionar mensajes': 'manage_messages',
            'Silenciar miembros': 'moderate_members',
            'Ver canal': 'view_channel',
            'Enviar mensajes': 'send_messages',
        }
        
        mensaje = "**Permisos en el servidor:**\n"
        for nombre, permiso in permisos_importantes.items():
            tiene = getattr(permisos_servidor, permiso, False)
            emoji = "✅" if tiene else "❌"
            mensaje += f"{emoji} {nombre}\n"
        
        await ctx.send(mensaje)

    @bot.command(name='meme')
    async def enviar_meme(ctx):
        """Comando para enviar meme random de subreddits en español"""
        # Verificar si está en el canal de memes
        if ctx.channel.id != CANAL_MEMES_ID:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(
                f"{ctx.author.mention} Este comando solo se puede usar en <#{CANAL_MEMES_ID}>",
                delete_after=5
            )
            return
        
        # Si está en el canal correcto, enviar el meme
        async with ctx.typing():
            url, titulo = await obtener_meme_shitpost()
            if url:
                embed = discord.Embed(
                    title=titulo if len(titulo) < 256 else titulo[:253] + "...",
                    color=discord.Color.random()
                )
                embed.set_image(url=url)
                embed.set_footer(text="Meme rancio del reddit")
                await ctx.send(embed=embed)
            else:
                await ctx.send("Ombe, no se pudo conseguir un meme, que jartera tan triple hijueputa")

    # Comandos de personas
    def crear_comando_persona(nombre):
        async def comando(ctx):
            await ctx.send(RESPUESTAS['personas'][nombre])
        return comando

    for nombre in RESPUESTAS['personas'].keys():
        bot.command(name=nombre)(crear_comando_persona(nombre))
    
    print("✅ Comandos registrados")