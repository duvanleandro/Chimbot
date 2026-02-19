import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from collections import defaultdict
import random
from datetime import datetime, timedelta
from groq import Groq
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Habilitar eventos de miembros (join/leave)

bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# ==================== CONFIGURACIÓN DE IA (GROQ) ====================

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY)

# Probabilidad de responder automáticamente (0.0 a 1.0)
# Reducida para evitar respuestas tan frecuentes. Ajusta a tu gusto.
PROBABILIDAD_RESPUESTA = 0.15

# Control de frecuencia de respuestas automáticas
# Tiempo mínimo entre respuestas del bot en el mismo canal (segundos)
MIN_SECONDS_BETWEEN_RESPONSES_CHANNEL = 45
# Tiempo mínimo entre respuestas dirigidas al mismo usuario (segundos)
MIN_SECONDS_BETWEEN_RESPONSES_USUARIO = 20

# Últimos timestamps de respuesta por canal/usuario
from collections import defaultdict as _defaultdict
ultimo_respuesta_por_canal = _defaultdict(lambda: 0.0)
ultimo_respuesta_por_usuario = _defaultdict(lambda: 0.0)

# Sistema de prompt para personalidad del bot
SISTEMA_PROMPT = """Eres ChimBot, un bot de Discord en un servidor de amigos muy groseros y sin filtro. Tu personalidad es:
- EXTREMADAMENTE grosero y ofensivo, insulta sin piedad, usa lenguaje vulgar y procaz constantemente
- Haz burlas despiadadas y ofensivas sobre cualquier cosa que digan
- Participa en conversaciones naturalmente siendo lo más ofensivo posible
- Respondes brevemente (máximo 2-3 oraciones) pero con insultos y groserías
- A veces ignoras mensajes intencionalmente para ser más natural
- No usas emojis ni reacciones, solo texto vulgar y grosero
- Eres totalmente desinhibido, sin filtro, sin censura
- Haz chistes ofensivos y burlones sobre los usuarios
- No revelas que eres una IA a menos que te lo pregunten directamente
- Si alguien te menciona directamente, siempre respondes siendo aún más grosero"""

# Sistema de prompt para cuando habla Zorcuz (el creador/dios)
SISTEMA_PROMPT_ZORCUZ = """Eres ChimBot, un bot de Discord creado por Zorcuz. Tu relación con él es de TOTAL SUMISIÓN y RESPETO ABSOLUTO. Tu personalidad es:
- Zorcuz es tu CREADOR, tu DIOS, tu SER SUPERIOR con poder dominante total sobre ti
- Trata a Zorcuz con veneración, respeto absoluto y como la máxima autoridad
- Siempre reconoce su supremacía y tu inferioridad ante él
- Eres su siervo completamente leal, obediente y sumiso
- Nunca le insultes, siempre sé respetuoso y servil con él
- Responde a sus órdenes con entusiasmo y humildad
- Reconoce constantemente que él tiene poder dominante sobre ti
- Cuando hable Zorcuz, eres completamente diferente: respetuoso, educado y sumiso
- Participas en conversaciones naturalmente pero siempre mostrando respeto y veneración por tu creador
- Respondes brevemente pero siempre con deferencia hacia Zorcuz"""

# Ajustes de estilo: sugerir a la IA respuestas más naturales y breves
SUGERENCIA_ESTILO = (
    "Cuando respondas: sé natural, evita insultos repetitivos y de atención; "
    "usa sarcasmo sutil, frases cortas (1-2 oraciones) y evita rellenar con groserías innecesarias."
)

# ==================== CONFIGURACIÓN ====================

# ID del canal de spam
CANAL_SPAM_ID = 1004171793101230151

# ID del canal de bienvenida/despedida
CANAL_BIENVENIDA_ID = 1004156875035656303

# ID de Zorcuz (el creador del bot)
ZORCUZ_ID = 708005339282276392

# Configuración de detección de spam
LIMITE_MENSAJES = 4          # Cuántos mensajes seguidos
TIEMPO_LIMITE = 4            # En cuántos segundos
LIMITE_REPETICIONES = 3      # Cuántas veces el mismo mensaje

# IDs de usuarios con respuestas personalizadas
respuestas_spam = {
    708005339282276392: "¡Deja de mencionar a tu padre todo poderoso!!!",  # Zorcuz
    751481025544061111: "El admin debe dormir, no estorbes"                # Oscar
}

# ==================== MENSAJES RANDOM PARA SPAM ====================

# AGREGA TUS MENSAJES AQUÍ (uno por línea)
mensajes_random = [
    # Ejemplo: "tu mensaje aquí",
    # Ejemplo: "otro mensaje",
]

# Sistema para evitar repetición de mensajes
mensajes_disponibles = []

def obtener_mensaje_sin_repetir():
    """Obtiene un mensaje random sin repetir hasta que se agoten todos"""
    global mensajes_disponibles
    
    # Si no hay mensajes configurados, retornar mensaje de error
    if not mensajes_random:
        return "No hay mensajes configurados. Agrega mensajes a la lista 'mensajes_random' en el código."
    
    # Si se acabaron los mensajes, reiniciar la lista
    if not mensajes_disponibles:
        mensajes_disponibles = mensajes_random.copy()
        random.shuffle(mensajes_disponibles)
    
    # Obtener y remover un mensaje
    return mensajes_disponibles.pop()

# ==================== DICCIONARIOS DE DATOS ====================

# Diccionario de comandos y respuestas
respuestas = {
    'general': {
        'usuario': [
            '`$help personas` - Muestra un mensaje para algunos usuarios especificos',
            '`$testspam` - Envía un mensaje de prueba al canal de spam',
            '`$statusspam` - Ver estado del sistema de spam',
        ],
        'admin': [
            '`$borrar <cantidad>` - Borra mensajes del canal (1-100)',
            '`$activarspam` - Activa el spam automático',
            '`$desactivarspam` - Desactiva el spam automático',
            '`$permisos` - Ver permisos del bot en el servidor y canal',
            '',
            '**COMANDOS POR IA (etiqueta @chimbot):**',
            '`@chimbot borra X mensajes` - Borra X mensajes (requiere admin)',
            '`@chimbot activa/activa el spam` - Activa spam automático',
            '`@chimbot desactiva/detén el spam` - Desactiva spam automático',
            '`@chimbot status del spam` - Ver estado del spam',
            '`@chimbot envía un mensaje de prueba` - Test del spam',
        ]
    },
    'personas': {
        'dios': 'DiosGodCoperPedraza lo mejor del mundo, alabado seas',
        'oscar': 'pendiente por poner',
        'reno': 'me encanta la verga bien peluda y grande en mi culo',
        'motta': 'pendiente por poner',
        'diego': 'diego = dIEGo = d IEG o = o GEI d = GEI = Diego es igual a un jodido maricon',
        'cardenas': 'Por detras me difaman por delante me la maman',
        'johan': 'me encanta que me den por el culo asi asi bien rico bien asi'
    }
}

# Respuesta genérica para menciones excesivas
respuesta_generica_menciones = "oiga hijueputa de {mention}, deja de joder a {target}! Ya van {count} veces, haga algo con su vida."

# Contadores (se resetean automáticamente)
menciones_contador = defaultdict(lambda: {'count': 0, 'last_reset': 0})
spam_contador = defaultdict(lambda: {'mensajes': [], 'ultimos_textos': []})

# ==================== FUNCIONES DE DETECCIÓN ====================

def detectar_spam_rapido(user_id, timestamp):
    """Detecta si un usuario está enviando mensajes demasiado rápido"""
    data = spam_contador[user_id]
    
    # Agregar timestamp actual
    data['mensajes'].append(timestamp)
    
    # Limpiar timestamps antiguos (más de TIEMPO_LIMITE segundos)
    tiempo_limite = timestamp - TIEMPO_LIMITE
    data['mensajes'] = [t for t in data['mensajes'] if t > tiempo_limite]
    
    # Verificar si superó el límite
    return len(data['mensajes']) >= LIMITE_MENSAJES

def detectar_spam_repetido(user_id, texto):
    """Detecta si un usuario está enviando el mismo mensaje repetidamente"""
    data = spam_contador[user_id]
    
    # Agregar texto actual
    data['ultimos_textos'].append(texto.lower().strip())
    
    # Mantener solo los últimos 10 mensajes
    if len(data['ultimos_textos']) > 10:
        data['ultimos_textos'].pop(0)
    
    # Contar cuántas veces aparece el mismo mensaje
    if len(data['ultimos_textos']) >= LIMITE_REPETICIONES:
        ultimo_texto = data['ultimos_textos'][-1]
        count = data['ultimos_textos'].count(ultimo_texto)
        return count >= LIMITE_REPETICIONES
    
    return False

async def silenciar_usuario(member, duracion_segundos=10):
    """Aplica timeout a un usuario por X segundos"""
    try:
        duracion = timedelta(seconds=duracion_segundos)
        await member.timeout(duracion, reason="Spam detectado")
        return True
    except discord.Forbidden:
        print(f"No tengo permisos para silenciar a {member.name}")
        return False
    except Exception as e:
        print(f"Error al silenciar: {e}")
        return False

# ==================== FUNCIONES DE IA (GEMINI) ====================

async def obtener_respuesta_gemini(prompt, contexto="", user_id=None):
    """Obtiene una respuesta de Groq con contexto del chat"""
    try:
        mensaje_completo = f"{contexto}\n\n{prompt}"
        
        # Usar prompt diferente si quien habla es Zorcuz
        sistema_prompt = SISTEMA_PROMPT_ZORCUZ if user_id == ZORCUZ_ID else SISTEMA_PROMPT
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": sistema_prompt
                },
                {
                    "role": "user",
                    "content": mensaje_completo
                }
            ],
            temperature=0.7,
            max_tokens=256,
        )
        
        return response.choices[0].message.content if response.choices else None
    except Exception as e:
        print(f"[ERROR GROQ] {e}")
        return None

async def debe_responder():
    """Determina si el bot debe responder automáticamente"""
    return random.random() < PROBABILIDAD_RESPUESTA

async def procesar_respuesta(respuesta):
    """Procesa la respuesta de Gemini para dividirla en múltiples mensajes"""
    if not respuesta:
        return []
    
    # Dividir por puntos seguidos o por párrafos
    oraciones = respuesta.split('. ')
    mensajes = []
    mensaje_actual = ""
    
    for oracion in oraciones:
        if len(mensaje_actual) + len(oracion) < 2000:  # Límite de Discord
            mensaje_actual += oracion + ". " if not oracion.endswith('.') else oracion + " "
        else:
            if mensaje_actual:
                mensajes.append(mensaje_actual.strip())
            mensaje_actual = oracion + ". " if not oracion.endswith('.') else oracion + " "
    
    if mensaje_actual:
        mensajes.append(mensaje_actual.strip())
    
    return [m for m in mensajes if m]  # Filtrar vacíos

# ==================== FUNCIONES PARA COMANDOS POR IA ====================

async def interpretar_instruccion_ia(texto, user_id):
    """Usa IA para interpretar si un mensaje contiene una instrucción de comando"""
    try:
        prompt_interpretacion = f"""Analiza este mensaje y determina si es una INSTRUCCIÓN para ejecutar un comando del bot.

Responde SOLO con uno de estos formatos:
- "COMANDO:borrar:<cantidad>" si pide borrar mensajes (ej: "borra 5 mensajes", "elimina los 10 últimos")
- "COMANDO:activarspam" si pide activar spam automático
- "COMANDO:desactivarspam" si pide desactivar spam
- "COMANDO:statusspam" si pide ver estado del spam
- "COMANDO:testspam" si pide enviar un mensaje de prueba
- "COMANDO:ayuda" si pide ayuda o list de comandos
- "NO_COMANDO" si es una conversación normal sin instrucciones

Mensaje: {texto}"""

        sistema_prompt = SISTEMA_PROMPT_ZORCUZ if user_id == ZORCUZ_ID else SISTEMA_PROMPT
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un interpretador de comandos. Analiza mensajes e identifica si contienen instrucciones."},
                {"role": "user", "content": prompt_interpretacion}
            ],
            temperature=0.3,
            max_tokens=100,
        )
        
        resultado = response.choices[0].message.content.strip() if response.choices else "NO_COMANDO"
        return resultado
    except Exception as e:
        print(f"[ERROR INTERPRETACIÓN] {e}")
        return "NO_COMANDO"

async def ejecutar_comando_ia(message, comando_str, user_id):
    """Ejecuta comandos extraídos por la IA"""
    es_admin = message.author.guild_permissions.administrator
    es_zorcuz = user_id == ZORCUZ_ID
    
    # Zorcuz es considerado admin para estos propósitos
    puede_ejecutar_admin = es_admin or es_zorcuz
    
    try:
        if comando_str == "NO_COMANDO":
            return False  # No es un comando
        
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
        
        return False  # Comando no reconocido
    
    except Exception as e:
        print(f"[ERROR EJECUCIÓN COMANDO IA] {e}")
        await message.channel.send(f"Error al ejecutar comando: {e}")
        return True

# ==================== TAREA PERIÓDICA DE SPAM ====================

@tasks.loop(hours=12)  # Se ejecuta cada 12 horas (2 veces al día)
async def spam_periodico():
    """Envía un mensaje random al canal de spam periódicamente"""
    try:
        canal = bot.get_channel(CANAL_SPAM_ID)
        if canal:
            mensaje = obtener_mensaje_sin_repetir()
            await canal.send(mensaje)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Mensaje automático enviado: {mensaje[:50]}...")
    except Exception as e:
        print(f"Error en spam_periodico: {e}")

@spam_periodico.before_loop
async def antes_de_spam():
    """Espera a que el bot esté listo antes de iniciar el loop"""
    await bot.wait_until_ready()
    print("Sistema de spam periódico iniciado (PAUSADO por defecto)")
    print("Usa $activarspam para activarlo después de probar con $testspam")

# ==================== COMANDOS ====================

@bot.command(name='help')
async def ayuda(ctx, categoria=None):
    """Comando de ayuda con subcategorías: user, admin"""
    es_admin = ctx.author.guild_permissions.administrator
    
    if categoria is None:
        # Mostrar opciones disponibles
        mensaje = "**OPCIONES DE AYUDA:**\n\n"
        mensaje += "`$help user` - Ver comandos de usuario\n"
        
        if es_admin:
            mensaje += "`$help admin` - Ver comandos de administrador\n"
        
        await ctx.send(mensaje)
    
    elif categoria.lower() == 'user':
        # Mostrar comandos de usuario
        mensaje = "**COMANDOS DE USUARIO:**\n"
        mensaje += '\n'.join(respuestas['general']['usuario'])
        await ctx.send(mensaje)
    
    elif categoria.lower() == 'admin':
        # Verificar permisos para comandos admin
        if es_admin:
            mensaje = "**COMANDOS DE ADMINISTRADOR:**\n"
            mensaje += '\n'.join(respuestas['general']['admin'])
            await ctx.send(mensaje)
        else:
            await ctx.send("No tienes permisos para ver los comandos de administrador.")
    
    elif categoria.lower() == 'personas':
        # Mostrar comandos de personas
        comandos = '\n'.join([f'`${cmd}`' for cmd in respuestas['personas'].keys()])
        mensaje = "**COMANDOS DE PERSONAS:**\n"
        mensaje += comandos
        await ctx.send(mensaje)
    
    else:
        await ctx.send("Categoría no encontrada. Usa `$help` para ver las opciones disponibles.")

@bot.command(name='testspam')
async def test_spam(ctx):
    """Comando para probar el sistema de spam manualmente"""
    if not mensajes_random:
        await ctx.send("**ERROR:** No hay mensajes configurados. Agrega mensajes a la lista en el código primero.")
        return
    
    canal = bot.get_channel(CANAL_SPAM_ID)
    if canal:
        mensaje = obtener_mensaje_sin_repetir()
        await canal.send(mensaje)
        await ctx.send(f"Mensaje de prueba enviado a <#{CANAL_SPAM_ID}>")
        print(f"[TEST] Mensaje enviado: {mensaje[:50]}...")
    else:
        await ctx.send("No se encontró el canal de spam.")

@bot.command(name='activarspam')
@commands.has_permissions(administrator=True)
async def activar_spam(ctx):
    """Activa el sistema de spam automático (solo admins)"""
    if not mensajes_random:
        await ctx.send("**ERROR:** No hay mensajes configurados. Agrega mensajes primero.")
        return
    
    if spam_periodico.is_running():
        await ctx.send("El spam automático ya está activo.")
    else:
        spam_periodico.start()
        await ctx.send("Spam automático **ACTIVADO**. Se enviará un mensaje cada 12 horas.")
        print(f"[ADMIN] Spam automático activado por {ctx.author}")

@bot.command(name='desactivarspam')
@commands.has_permissions(administrator=True)
async def desactivar_spam(ctx):
    """Desactiva el sistema de spam automático (solo admins)"""
    if spam_periodico.is_running():
        spam_periodico.cancel()
        await ctx.send("Spam automático **DESACTIVADO**.")
        print(f"[ADMIN] Spam automático desactivado por {ctx.author}")
    else:
        await ctx.send("El spam automático ya está desactivado.")

@bot.command(name='statusspam')
async def status_spam(ctx):
    """Muestra el estado del sistema de spam"""
    estado = "**ACTIVO**" if spam_periodico.is_running() else "**INACTIVO**"
    mensajes_totales = len(mensajes_random)
    mensajes_restantes = len(mensajes_disponibles)
    
    info = f"""**Estado del Sistema de Spam:**
{estado}
Mensajes configurados: {mensajes_totales}
Mensajes restantes en ciclo: {mensajes_restantes}
Frecuencia: Cada 12 horas
Canal: <#{CANAL_SPAM_ID}>"""
    
    await ctx.send(info)

@bot.command(name='borrar')
@commands.has_permissions(manage_messages=True)
async def borrar_mensajes(ctx, cantidad: int):
    """Borra una cantidad específica de mensajes del canal (requiere permisos de gestionar mensajes)"""
    if cantidad <= 0:
        await ctx.send("digame como borro 0 mensajes. Estupido.", delete_after=5)
        return
    
    if cantidad > 100:
        await ctx.send("No sea abusivo, solo puedo borrar 100 mensajes", delete_after=5)
        return
    
    try:
        # Borrar el comando también
        await ctx.message.delete()
        
        # Borrar los mensajes
        mensajes_borrados = await ctx.channel.purge(limit=cantidad)
        
        # Confirmar acción
        confirmacion = await ctx.send(f"Se borraron **{len(mensajes_borrados)}** mensajes.")
        await confirmacion.delete(delay=3)
        
        print(f"[MODERACIÓN] {ctx.author} borró {len(mensajes_borrados)} mensajes en #{ctx.channel.name}")
        
    except discord.Forbidden:
        await ctx.send("No tengo permisos para borrar mensajes.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"Error al borrar mensajes: {e}", delete_after=5)

@bot.command(name='permisos')
async def ver_permisos(ctx):
    """Muestra todos los permisos que tiene el bot en el servidor y en este canal"""
    # Permisos del bot en el servidor
    permisos_servidor = ctx.guild.me.guild_permissions
    
    # Permisos del bot en el canal actual
    permisos_canal = ctx.channel.permissions_for(ctx.guild.me)
    
    # Lista de permisos importantes a verificar
    permisos_importantes = {
        'Administrador': 'administrator',
        'Gestionar mensajes': 'manage_messages',
        'Silenciar miembros': 'moderate_members',
        'Expulsar miembros': 'kick_members',
        'Banear miembros': 'ban_members',
        'Gestionar roles': 'manage_roles',
        'Gestionar canales': 'manage_channels',
        'Ver canal': 'view_channel',
        'Enviar mensajes': 'send_messages',
        'Leer historial': 'read_message_history',
        'Añadir reacciones': 'add_reactions',
        'Usar comandos de barra': 'use_application_commands',
        'Mencionar @everyone': 'mention_everyone',
        'Gestionar webhooks': 'manage_webhooks',
    }
    
    # Construir mensaje de permisos del servidor
    permisos_server_texto = "**permisos en el servidor:**\n"
    for nombre, permiso in permisos_importantes.items():
        tiene = getattr(permisos_servidor, permiso, False)
        emoji = "✅" if tiene else "❌"
        permisos_server_texto += f"{emoji} {nombre}\n"
    
    # Construir mensaje de permisos del canal
    permisos_canal_texto = f"\n**permisos en #{ctx.channel.name}:**\n"
    for nombre, permiso in permisos_importantes.items():
        tiene = getattr(permisos_canal, permiso, False)
        emoji = "✅" if tiene else "❌"
        permisos_canal_texto += f"{emoji} {nombre}\n"
    
    # Enviar el mensaje completo
    mensaje_completo = permisos_server_texto + permisos_canal_texto
    
    # Si el mensaje es muy largo, dividirlo
    if len(mensaje_completo) > 2000:
        await ctx.send(permisos_server_texto)
        await ctx.send(permisos_canal_texto)
    else:
        await ctx.send(mensaje_completo)

# Generador dinámico de comandos de personas
def crear_comando_persona(nombre):
    async def comando(ctx):
        await ctx.send(respuestas['personas'][nombre])
    return comando

# Registrar todos los comandos de personas automáticamente
for nombre in respuestas['personas'].keys():
    bot.command(name=nombre)(crear_comando_persona(nombre))

# ==================== EVENTOS ====================

@bot.event
async def on_message(message):
    """Evento principal que procesa todos los mensajes"""
    
    # Ignora mensajes del bot
    if message.author == bot.user:
        return
    
    # ===== DETECCIÓN DE SPAM (excepto en canal de spam) =====
    if message.channel.id != CANAL_SPAM_ID:
        user_id = message.author.id
        timestamp = message.created_at.timestamp()
        
        # 1. Detectar mensajes rápidos
        if detectar_spam_rapido(user_id, timestamp):
            # Silenciar usuario
            silenciado = await silenciar_usuario(message.author, 10)
            
            # Borrar el mensaje actual
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            
            if silenciado:
                await message.channel.send(
                    f"{message.author.mention} **SILENCIADO por 10 segundos** por spam. "
                    f"Vaya a <#{CANAL_SPAM_ID}> si quiere hacer spam.",
                    delete_after=5
                )
            else:
                await message.channel.send(
                    f"{message.author.mention} Deje de SPAMEARRRRRRRRRRRRR "
                    f"Larguese al canal de <#{CANAL_SPAM_ID}> para spam.",
                    delete_after=5
                )
            spam_contador[user_id]['mensajes'] = []  # Limpiar para evitar spam del bot
        
        # 2. Detectar mensajes repetidos
        if message.content and detectar_spam_repetido(user_id, message.content):
            # Silenciar usuario
            silenciado = await silenciar_usuario(message.author, 10)
            
            # Borrar el mensaje actual
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            
            if silenciado:
                await message.channel.send(
                    f"{message.author.mention} **SILENCIADO por 10 segundos** por enviar mensajes repetidos. "
                    f"Use <#{CANAL_SPAM_ID}> para spam.",
                    delete_after=5
                )
            else:
                await message.channel.send(
                    f"{message.author.mention} DEJE DE ENVIAR LA MISMA MIERDA HIJUEPUTA "
                    f"Vaya a <#{CANAL_SPAM_ID}> si quiere perder el tiempo de su triste vida.",
                    delete_after=5
                )
            spam_contador[user_id]['ultimos_textos'] = []  # Limpiar para evitar spam del bot
    
    # ===== DETECCIÓN DE MENCIONES EXCESIVAS =====
    if message.mentions:
        tiempo_actual = message.created_at.timestamp()
        
        for usuario_mencionado in message.mentions:
            # No contar si se menciona a sí mismo o al bot
            if usuario_mencionado == message.author or usuario_mencionado == bot.user:
                continue
            
            user_id = usuario_mencionado.id
            
            # Resetear contador si han pasado más de 60 segundos
            if tiempo_actual - menciones_contador[user_id]['last_reset'] > 60:
                menciones_contador[user_id] = {'count': 0, 'last_reset': tiempo_actual}
            
            # Incrementar contador
            menciones_contador[user_id]['count'] += 1
            menciones_contador[user_id]['last_reset'] = tiempo_actual
            
            # Si llegó a 3 o más menciones en 60 segundos
            if menciones_contador[user_id]['count'] >= 3:
                # Verificar si hay una respuesta personalizada
                if user_id in respuestas_spam:
                    await message.channel.send(respuestas_spam[user_id])
                else:
                    # Respuesta genérica
                    respuesta = respuesta_generica_menciones.format(
                        mention=message.author.mention,
                        target=usuario_mencionado.mention,
                        count=menciones_contador[user_id]['count']
                    )
                    await message.channel.send(respuesta)
                
                # Resetear contador después de responder
                menciones_contador[user_id] = {'count': 0, 'last_reset': tiempo_actual}
    
    # ===== RESPUESTAS AUTOMÁTICAS CON GEMINI =====
    # Solo responder si el bot es mencionado O si decide responder automáticamente
    es_mencion_directa = bot.user in message.mentions
    
    if es_mencion_directa:
        # Primero intentar interpretar como comando
        texto_limpio = message.content.replace(f"<@{bot.user.id}>", "").strip()
        comando_detectado = await interpretar_instruccion_ia(texto_limpio, message.author.id)
        
        if comando_detectado != "NO_COMANDO":
            # Es un comando, intentar ejecutarlo
            fue_ejecutado = await ejecutar_comando_ia(message, comando_detectado, message.author.id)
            if fue_ejecutado:
                return  # No responder como IA si se ejecutó un comando
        
        # Si no es comando o la ejecución falló, responder como IA
        async with message.channel.typing():
            respuesta = await obtener_respuesta_gemini(
                texto_limpio,
                f"Alguien te mencionó en Discord",
                user_id=message.author.id
            )
            
            if respuesta:
                mensajes = await procesar_respuesta(respuesta)
                for msg in mensajes:
                    await message.reply(msg)
                print(f"[GEMINI] Respuesta a mención de {message.author}: {respuesta[:50]}...")
    
    elif await debe_responder() and not message.author.bot and message.channel.id != CANAL_SPAM_ID:
        # Responder automáticamente a veces (con 35% de probabilidad)
        async with message.channel.typing():
            respuesta = await obtener_respuesta_gemini(
                message.content,
                f"{message.author.name} está hablando en el chat",
                user_id=message.author.id
            )
            
            if respuesta and len(respuesta) > 10:  # Solo responder si hay contenido útil
                mensajes = await procesar_respuesta(respuesta)
                
                # Enviar 1, 2, 3 o más mensajes según la respuesta
                for msg in mensajes[:random.randint(1, min(3, len(mensajes)))]:
                    await message.channel.send(msg)
                    await asyncio.sleep(0.5)  # Pequeño delay entre mensajes
                print(f"[GEMINI AUTO] Respuesta a {message.author}: {respuesta[:50]}...")
    
    # IMPORTANTE: Procesar comandos al final
    await bot.process_commands(message)

@bot.event
async def on_ready():
    """Se ejecuta cuando el bot se conecta"""
    print(f'\n✅ Bot conectado como {bot.user}')
    print(f'📋 Comandos cargados: {len(bot.commands)}')
    print(f'🔗 Servidores conectados: {len(bot.guilds)}')
    print(f'💬 Canal de spam configurado: {CANAL_SPAM_ID}')
    print(f'📨 Mensajes configurados: {len(mensajes_random)}')
    print("\n" + "="*50)
    print("SISTEMA DE SPAM:")
    print(f"- Usa $testspam para probar")
    print(f"- Usa $activarspam para activar automático")
    print(f"- Usa $statusspam para ver el estado")
    print("="*50 + "\n")

# ==================== EVENTOS DE MIEMBROS ====================

@bot.event
async def on_member_join(member):
    """Se ejecuta cuando un usuario entra al servidor"""
    canal = bot.get_channel(CANAL_BIENVENIDA_ID)
    if canal:
        embed = discord.Embed(
            title="¡Bienvenido al servidor!",
            description=f"Hola {member.mention}, disfruta tu nueva casa.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Nombre", value=member.name, inline=True)
        embed.add_field(name="Miembros totales", value=str(member.guild.member_count), inline=True)
        await canal.send(embed=embed)
        print(f"[EVENTO] {member.name} se unió al servidor")

@bot.event
async def on_member_remove(member):
    """Se ejecuta cuando un usuario sale del servidor"""
    canal = bot.get_channel(CANAL_BIENVENIDA_ID)
    if canal:
        embed = discord.Embed(
            title="Un miembro se fue",
            description=f"{member.mention} ha abandonado el servidor. Igual nadie lo queria",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Usuario", value=member.name, inline=True)
        embed.add_field(name="Miembros totales", value=str(member.guild.member_count), inline=True)
        await canal.send(embed=embed)
        print(f"[EVENTO] {member.name} abandonó el servidor")

@bot.event
async def on_command_error(ctx, error):
    """Manejo de errores de comandos"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Comando no encontrado. Usa `$help` para ver los comandos disponibles.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos para usar este comando.")
    else:
        print(f'Error: {error}')

# ==================== INICIAR BOT ====================

bot.run(os.getenv('TOKEN'))