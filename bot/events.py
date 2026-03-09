"""
Eventos del bot de Discord
"""
import discord
import asyncio
import random
from collections import defaultdict
from config import (
    CANAL_SPAM_ID, CANAL_BIENVENIDA_ID, ZORCUZ_ID,
    RESPUESTAS_SPAM, RESPUESTA_GENERICA_MENCIONES, mensajes_random
)
from utils import (
    obtener_respuesta_gemini, debe_responder, procesar_respuesta,
    detectar_spam_rapido, detectar_spam_repetido, silenciar_usuario,
    interpretar_instruccion_ia
)

# Contadores globales
menciones_contador = defaultdict(lambda: {'count': 0, 'last_reset': 0})


def setup_events(bot):
    """Registra todos los eventos del bot"""
    
    @bot.event
    async def on_ready():
        """Se ejecuta cuando el bot se conecta"""
        print(f'\n✅ Bot conectado como {bot.user}')
        print(f'📋 Comandos cargados: {len(bot.commands)}')
        print(f'🔗 Servidores: {len(bot.guilds)}')
        print(f'💬 Canal de spam: {CANAL_SPAM_ID}')
        print("="*50 + "\n")

    @bot.event
    async def on_member_join(member):
        """Se ejecuta cuando un usuario entra al servidor"""
        canal = bot.get_channel(CANAL_BIENVENIDA_ID)
        if canal:
            embed = discord.Embed(
                title="¡Bienvenido!",
                description=f"Hola {member.mention}, disfruta tu nueva casa.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            await canal.send(embed=embed)

    @bot.event
    async def on_member_remove(member):
        """Se ejecuta cuando un usuario sale del servidor"""
        canal = bot.get_channel(CANAL_BIENVENIDA_ID)
        if canal:
            embed = discord.Embed(
                title="Un miembro se fue",
                description=f"{member.mention} abandonó el servidor. Igual nadie lo quería",
                color=discord.Color.red()
            )
            await canal.send(embed=embed)

    @bot.event
    async def on_command_error(ctx, error):
        """Manejo de errores de comandos"""
        if isinstance(error, discord.ext.commands.CommandNotFound):
            await ctx.send("Comando no encontrado. Usa `$help` para ver comandos.")
        elif isinstance(error, discord.ext.commands.MissingPermissions):
            await ctx.send("No tienes permisos para usar este comando.")
        else:
            print(f'Error: {error}')

    @bot.event
    async def on_message(message):
        """Evento principal que procesa todos los mensajes"""
        
        if message.author == bot.user:
            return
        
        # Detección de spam (excepto en canal de spam)
        if message.channel.id != CANAL_SPAM_ID:
            user_id = message.author.id
            timestamp = message.created_at.timestamp()
            
            if detectar_spam_rapido(user_id, timestamp):
                silenciado = await silenciar_usuario(message.author, 10)
                
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                
                if silenciado:
                    await message.channel.send(
                        f"{message.author.mention} **SILENCIADO por 10 segundos** por spam.",
                        delete_after=5
                    )
            
            if message.content and detectar_spam_repetido(user_id, message.content):
                silenciado = await silenciar_usuario(message.author, 10)
                
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                
                if silenciado:
                    await message.channel.send(
                        f"{message.author.mention} **SILENCIADO por 10 segundos** por mensajes repetidos.",
                        delete_after=5
                    )
        
        # Detección de menciones excesivas
        if message.mentions:
            tiempo_actual = message.created_at.timestamp()
            
            for usuario_mencionado in message.mentions:
                if usuario_mencionado == message.author or usuario_mencionado == bot.user:
                    continue
                
                user_id = usuario_mencionado.id
                
                if tiempo_actual - menciones_contador[user_id]['last_reset'] > 5:
                    menciones_contador[user_id] = {'count': 0, 'last_reset': tiempo_actual}
                
                menciones_contador[user_id]['count'] += 1
                menciones_contador[user_id]['last_reset'] = tiempo_actual
                
                if menciones_contador[user_id]['count'] >= 3:
                    if user_id in RESPUESTAS_SPAM:
                        await message.channel.send(RESPUESTAS_SPAM[user_id])
                    else:
                        respuesta = RESPUESTA_GENERICA_MENCIONES.format(
                            mention=message.author.mention,
                            target=usuario_mencionado.mention,
                            count=menciones_contador[user_id]['count']
                        )
                        await message.channel.send(respuesta)
                    
                    menciones_contador[user_id] = {'count': 0, 'last_reset': tiempo_actual}
        
        # Respuestas automáticas con IA
        es_mencion_directa = bot.user in message.mentions
        
        if es_mencion_directa:
            texto_limpio = message.content.replace(f"<@{bot.user.id}>", "").strip()
            comando_detectado = await interpretar_instruccion_ia(texto_limpio, message.author.id)
            
            if comando_detectado != "NO_COMANDO":
                fue_ejecutado = await ejecutar_comando_ia(message, comando_detectado, message.author.id, bot)
                if fue_ejecutado:
                    return
            
            async with message.channel.typing():
                respuesta = await obtener_respuesta_gemini(
                    texto_limpio,
                    f"Alguien te mencionó en Discord",
                    user_id=message.author.id,
                    member=message.author
                )
                
                if respuesta:
                    mensajes = await procesar_respuesta(respuesta)
                    for msg in mensajes:
                        try:
                            await message.reply(msg)
                        except discord.errors.HTTPException:
                            await message.channel.send(msg)
                    print(f"[IA] Respuesta a mención de {message.author.name}")
        
        elif await debe_responder() and not message.author.bot and message.channel.id != CANAL_SPAM_ID:
            async with message.channel.typing():
                respuesta = await obtener_respuesta_gemini(
                    message.content,
                    f"{message.author.name} está hablando en el chat",
                    user_id=message.author.id,
                    member=message.author
                )
                
                if respuesta and len(respuesta) > 10:
                    mensajes = await procesar_respuesta(respuesta)
                    
                    for msg in mensajes[:random.randint(1, min(3, len(mensajes)))]:
                        await message.channel.send(msg)
                        await asyncio.sleep(0.5)
                    print(f"[IA AUTO] Respuesta a {message.author.name}")
        
        await bot.process_commands(message)
    
    print("✅ Eventos registrados")


async def ejecutar_comando_ia(message, comando_str, user_id, bot):
    """Ejecuta comandos extraídos por la IA"""
    from .tasks import spam_periodico
    from config import CANAL_SPAM_ID, mensajes_random, obtener_mensaje_sin_repetir
    
    es_admin = message.author.guild_permissions.administrator
    es_zorcuz = user_id == ZORCUZ_ID
    puede_ejecutar_admin = es_admin or es_zorcuz
    
    try:
        if comando_str == "NO_COMANDO":
            return False
        
        if comando_str.startswith("COMANDO:borrar:"):
            if not puede_ejecutar_admin:
                await message.channel.send("No tienes permisos para usar comandos de administrador.")
                return True
            
            try:
                cantidad = int(comando_str.split(':')[2])
                if cantidad <= 0 or cantidad > 100:
                    await message.channel.send("Debes especificar una cantidad entre 1 y 100.")
                    return True
                
                mensajes_borrados = await message.channel.purge(limit=cantidad)
                confirmacion = await message.channel.send(f"Se borraron **{len(mensajes_borrados)}** mensajes.")
                await confirmacion.delete(delay=3)
                print(f"[COMANDO IA] {message.author} borró {len(mensajes_borrados)} mensajes")
                return True
            except ValueError:
                await message.channel.send("Cantidad inválida.")
                return True
        
        elif comando_str == "COMANDO:activarspam":
            if not puede_ejecutar_admin:
                await message.channel.send("No tienes permisos para usar comandos de administrador.")
                return True
            
            if not mensajes_random:
                await message.channel.send("No hay mensajes configurados.")
                return True
            
            if spam_periodico.is_running():
                await message.channel.send("El spam automático ya está activo.")
            else:
                spam_periodico.start()
                await message.channel.send("Spam automático **ACTIVADO**.")
                print(f"[COMANDO IA] Spam activado por {message.author}")
            return True
        
        elif comando_str == "COMANDO:desactivarspam":
            if not puede_ejecutar_admin:
                await message.channel.send("No tienes permisos para usar comandos de administrador.")
                return True
            
            if spam_periodico.is_running():
                spam_periodico.cancel()
                await message.channel.send("Spam automático **DESACTIVADO**.")
                print(f"[COMANDO IA] Spam desactivado por {message.author}")
            else:
                await message.channel.send("El spam automático ya está desactivado.")
            return True
        
        elif comando_str == "COMANDO:statusspam":
            estado = "**ACTIVO**" if spam_periodico.is_running() else "**INACTIVO**"
            info = f"""**Estado del Sistema de Spam:**
{estado}
Mensajes configurados: {len(mensajes_random)}
Canal: <#{CANAL_SPAM_ID}>"""
            await message.channel.send(info)
            return True
        
        elif comando_str == "COMANDO:testspam":
            canal = bot.get_channel(CANAL_SPAM_ID)
            if not canal:
                await message.channel.send("No se encontró el canal de spam.")
                return True
            
            if not mensajes_random:
                await message.channel.send("No hay mensajes configurados.")
                return True
            
            mensaje = obtener_mensaje_sin_repetir()
            await canal.send(mensaje)
            await message.channel.send(f"Mensaje de prueba enviado a <#{CANAL_SPAM_ID}>")
            print(f"[COMANDO IA] Test spam enviado por {message.author}")
            return True
        
        elif comando_str == "COMANDO:ayuda":
            mensaje = "**OPCIONES DE AYUDA:**\n\n"
            mensaje += "`$help user` - Ver comandos de usuario\n"
            if puede_ejecutar_admin:
                mensaje += "`$help admin` - Ver comandos de administrador\n"
            await message.channel.send(mensaje)
            return True
        
        return False
    
    except Exception as e:
        print(f"[ERROR EJECUCIÓN COMANDO IA] {e}")
        await message.channel.send(f"Error al ejecutar comando: {e}")
        return True