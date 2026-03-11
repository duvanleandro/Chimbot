"""
Comandos del bot de Discord
"""
import discord
from discord.ext import commands
from config import (
    RESPUESTAS, CANAL_SPAM_ID, CANAL_MEMES_ID, ZORCUZ_ID,
    mensajes_random, obtener_mensaje_sin_repetir
)
from utils import obtener_meme_shitpost, obtener_copypasta


def setup_commands(bot):
    """Registra todos los comandos del bot"""
    
    @bot.command(name='help')
    async def ayuda(ctx, categoria=None):
        """Comando de ayuda con subcategorías: user, admin, music"""
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
        
        elif categoria.lower() == 'music':
            mensaje = "**🎵 COMANDOS DE MÚSICA:**\n\n"
            for cmd, desc in RESPUESTAS['music'].items():
                mensaje += f"{cmd} {desc}\n"
            await ctx.send(mensaje)
        
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
            await ctx.send("No sea abusivo, solo puedo borrar 100 mensajes a la vez", delete_after=5)
            return
        
        try:
            # Borrar el comando primero
            await ctx.message.delete()
            
            # Obtener mensajes a borrar
            mensajes_a_borrar = []
            async for message in ctx.channel.history(limit=cantidad):
                # Discord solo permite borrar mensajes de menos de 14 días
                if (discord.utils.utcnow() - message.created_at).days < 14:
                    mensajes_a_borrar.append(message)
            
            if not mensajes_a_borrar:
                confirmacion = await ctx.send("No hay mensajes para borrar (deben ser de menos de 14 días)")
                await confirmacion.delete(delay=5)
                return
            
            # Borrar en lotes de 100 (límite de Discord)
            total_borrados = 0
            
            # Si hay 2 o más mensajes, usar bulk_delete (más rápido)
            if len(mensajes_a_borrar) >= 2:
                # Dividir en chunks de 100
                for i in range(0, len(mensajes_a_borrar), 100):
                    chunk = mensajes_a_borrar[i:i+100]
                    try:
                        await ctx.channel.delete_messages(chunk)
                        total_borrados += len(chunk)
                    except discord.HTTPException as e:
                        print(f"[ERROR AL BORRAR CHUNK] {e}")
                        # Si falla bulk delete, intentar uno por uno
                        for msg in chunk:
                            try:
                                await msg.delete()
                                total_borrados += 1
                            except:
                                pass
            else:
                # Si es solo 1 mensaje, borrarlo directamente
                for msg in mensajes_a_borrar:
                    try:
                        await msg.delete()
                        total_borrados += 1
                    except:
                        pass
            
            confirmacion = await ctx.send(f"Se borraron **{total_borrados}** mensajes.")
            await confirmacion.delete(delay=3)
            
        except discord.Forbidden:
            await ctx.send("No tengo permisos para borrar mensajes.", delete_after=5)
        except discord.HTTPException as e:
            print(f"[ERROR AL BORRAR] {e}")
            await ctx.send(f"Hubo un error al borrar algunos mensajes. Se borraron los que se pudieron.", delete_after=5)
        except Exception as e:
            print(f"[ERROR INESPERADO] {e}")
            await ctx.send(f"Error inesperado al borrar mensajes.", delete_after=5)

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
            await ctx.send(
                f"{ctx.author.mention} ombe gonorrea, usa ese comando en <#{CANAL_MEMES_ID}>",
                delete_after=8
            )
            
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            
            return
        
        # Si está en el canal correcto, enviar el meme
        async with ctx.typing():
            url, titulo, tipo = await obtener_meme_shitpost()
            
            if url:
                if tipo == 'image':
                    # Para imágenes: usar embed
                    embed = discord.Embed(
                        title=titulo if len(titulo) < 256 else titulo[:253] + "...",
                        color=discord.Color.random()
                    )
                    embed.set_image(url=url)
                    embed.set_footer(text="Meme rancio del reddit 🔥")
                    await ctx.send(embed=embed)
                    
                elif tipo in ['reddit_video', 'video', 'external_video']:
                    # Para videos: enviar el título como mensaje normal y el video debajo
                    titulo_corto = titulo if len(titulo) < 200 else titulo[:197] + "..."
                    await ctx.send(f"**{titulo_corto}**\n{url}")
                else:
                    # Fallback: enviar URL directamente
                    await ctx.send(url)
            else:
                await ctx.send("Ombe, no se pudo conseguir un meme nuevo, todos ya los he enviado. Espera un rato gonorrea")
        
    @bot.command(name='historia')
    async def enviar_historia(ctx):
        """Comando para enviar copypasta random de r/copypasta_es"""
        from config import CANAL_MEMES_ID
        import asyncio
        
        # Verificar si está en el canal correcto
        if ctx.channel.id != CANAL_MEMES_ID:
            await ctx.send(
                f"{ctx.author.mention} ombe, usa ese comando en <#{CANAL_MEMES_ID}>",
                delete_after=8
            )
            
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            
            return
        
        # Si está en el canal correcto, enviar el copypasta
        async with ctx.typing():
            try:
                titulo, texto, url = await obtener_copypasta()
                
                if titulo and texto:
                    # Dividir el copypasta si es muy largo (Discord límite: 2000 caracteres)
                    header = f"**📖 {titulo}**\n\n"
                    
                    # Si el texto completo cabe en un mensaje
                    if len(header + texto) <= 1900:
                        await ctx.send(f"{header}{texto}\n\n*Fuente: <{url}>*")
                    else:
                        # Enviar el título primero
                        await ctx.send(header)
                        
                        # Dividir el texto en chunks de ~1900 caracteres
                        chunks = []
                        texto_restante = texto
                        
                        while len(texto_restante) > 0:
                            if len(texto_restante) <= 1900:
                                chunks.append(texto_restante)
                                break
                            
                            # Buscar un punto o salto de línea cerca del límite
                            corte = texto_restante[:1900].rfind('\n')
                            if corte == -1:
                                corte = texto_restante[:1900].rfind('. ')
                            if corte == -1:
                                corte = 1900
                            
                            chunks.append(texto_restante[:corte])
                            texto_restante = texto_restante[corte:].strip()
                        
                        # Enviar cada chunk
                        for i, chunk in enumerate(chunks):
                            if i == len(chunks) - 1:
                                # Último chunk: agregar fuente
                                await ctx.send(f"{chunk}\n\n*Fuente: <{url}>*")
                            else:
                                await ctx.send(chunk)
                            
                            # Pequeña pausa entre mensajes
                            await asyncio.sleep(0.5)
                else:
                    await ctx.send("Ombe, no se pudo conseguir una historia nueva, todas ya las he enviado. Espera un rato gonorrea")
            
            except Exception as e:
                print(f"[ERROR EN COMANDO HISTORIA] {e}")
                import traceback
                traceback.print_exc()
                await ctx.send("Ombe parce, hubo un error consiguiendo la historia. Intenta de nuevo gonorrea")

    # Comandos de personas
    def crear_comando_persona(nombre):
        async def comando(ctx):
            await ctx.send(RESPUESTAS['personas'][nombre])
        return comando

    for nombre in RESPUESTAS['personas'].keys():
        bot.command(name=nombre)(crear_comando_persona(nombre))
    
    print("✅ Comandos registrados")