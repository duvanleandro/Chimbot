from flask import Flask, render_template, request, jsonify
from threading import Thread
import asyncio

app = Flask(__name__)

# Variable global para almacenar la referencia al bot
bot_instance = None

def set_bot(bot):
    """Establece la referencia al bot de Discord"""
    global bot_instance
    bot_instance = bot

@app.route('/')
def index():
    """Página principal - muestra que el bot está activo"""
    return "ChimBot está activo! 🤖"

@app.route('/dashboard')
def dashboard():
    """Dashboard de control del bot"""
    return render_template('dashboard.html')

@app.route('/api/debug')
def debug_info():
    """Endpoint de debug para ver información del bot"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    info = {
        "bot_listo": bot_instance.is_ready(),
        "bot_user": str(bot_instance.user) if bot_instance.user else None,
        "servidores": []
    }
    
    for guild in bot_instance.guilds:
        info["servidores"].append({
            "id": guild.id,
            "id_str": str(guild.id),
            "nombre": guild.name,
            "canales_texto": len(guild.text_channels),
            "miembros": guild.member_count
        })
    
    return jsonify(info)

@app.route('/api/servidores')
def obtener_servidores():
    """API: Obtiene la lista de servidores donde está el bot"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    servidores = []
    for guild in bot_instance.guilds:
        servidores.append({
            "id": str(guild.id),  # ← CAMBIAR A STRING
            "nombre": guild.name,
            "icono": str(guild.icon.url) if guild.icon else None,
            "miembros": guild.member_count
        })
    
    return jsonify(servidores)

@app.route('/api/canales/<servidor_id>')
def obtener_canales(servidor_id):
    """API: Obtiene los canales de texto de un servidor"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    # Convertir a int
    try:
        servidor_id = int(servidor_id)
    except ValueError:
        return jsonify({"error": "ID de servidor inválido"}), 400
    
    guild = bot_instance.get_guild(servidor_id)
    if not guild:
        ids_disponibles = [str(g.id) for g in bot_instance.guilds]
        return jsonify({
            "error": "Servidor no encontrado",
            "servidor_buscado": servidor_id,
            "servidores_disponibles": ids_disponibles
        }), 404
    
    canales = []
    for channel in guild.text_channels:
        canales.append({
            "id": str(channel.id),  # ← CAMBIAR A STRING
            "nombre": channel.name,
            "categoria": channel.category.name if channel.category else "Sin categoría",
            "posicion": channel.position
        })
    
    canales.sort(key=lambda x: (x['categoria'], x['posicion']))
    
    return jsonify(canales)

@app.route('/api/usuarios/<servidor_id>')
def obtener_usuarios(servidor_id):
    """API: Obtiene los usuarios de un servidor"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    try:
        servidor_id = int(servidor_id)
    except ValueError:
        return jsonify({"error": "ID de servidor inválido"}), 400
    
    guild = bot_instance.get_guild(servidor_id)
    if not guild:
        return jsonify({"error": "Servidor no encontrado"}), 404
    
    usuarios = []
    for member in guild.members:
        if not member.bot:
            usuarios.append({
                "id": str(member.id),  # ← CAMBIAR A STRING
                "nombre": member.name,
                "display_name": member.display_name,
                "avatar": str(member.avatar.url) if member.avatar else None
            })
    
    usuarios.sort(key=lambda x: x['display_name'].lower())
    
    return jsonify(usuarios)

@app.route('/api/mensajes/<canal_id>')
def obtener_mensajes(canal_id):
    """API: Obtiene los últimos mensajes de un canal"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    try:
        canal_id = int(canal_id)
    except ValueError:
        return jsonify({"error": "ID de canal inválido"}), 400
    
    canal = bot_instance.get_channel(canal_id)
    if not canal:
        return jsonify({"error": "Canal no encontrado"}), 404
    
    # Obtener mensajes de forma asíncrona
    try:
        async def get_messages():
            mensajes = []
            async for message in canal.history(limit=10):
                mensajes.append({
                    "id": str(message.id),
                    "autor": message.author.display_name,
                    "autor_avatar": str(message.author.avatar.url) if message.author.avatar else None,
                    "contenido": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "adjuntos": [attachment.url for attachment in message.attachments]
                })
            return mensajes
        
        future = asyncio.run_coroutine_threadsafe(
            get_messages(),
            bot_instance.loop
        )
        mensajes = future.result(timeout=5)
        
        # Invertir para mostrar del más antiguo al más reciente
        mensajes.reverse()
        
        return jsonify(mensajes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/enviar', methods=['POST'])
def enviar_mensaje():
    """API: Envía un mensaje a un canal"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    data = request.json
    canal_id = data.get('canal_id')
    mensaje = data.get('mensaje')
    
    if not canal_id or not mensaje:
        return jsonify({"error": "Faltan parámetros"}), 400
    
    canal = bot_instance.get_channel(int(canal_id))
    if not canal:
        return jsonify({"error": "Canal no encontrado"}), 404
    
    # Enviar mensaje de forma asíncrona
    try:
        future = asyncio.run_coroutine_threadsafe(
            canal.send(mensaje),
            bot_instance.loop
        )
        future.result(timeout=5)
        return jsonify({"success": True, "mensaje": "Mensaje enviado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def obtener_estadisticas():
    """API: Obtiene estadísticas generales del bot"""
    if not bot_instance:
        return jsonify({"error": "Bot no inicializado"}), 500
    
    total_canales = sum(len(guild.text_channels) for guild in bot_instance.guilds)
    total_usuarios = sum(guild.member_count for guild in bot_instance.guilds)
    
    return jsonify({
        "servidores": len(bot_instance.guilds),
        "canales": total_canales,
        "usuarios": total_usuarios,
        "latencia": round(bot_instance.latency * 1000, 2)  # en ms
    })

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive(bot):
    """Inicia el servidor Flask y guarda referencia al bot"""
    set_bot(bot)
    server = Thread(target=run, daemon=True)
    server.start()