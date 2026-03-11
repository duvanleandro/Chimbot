"""
Rutas de la API del dashboard
"""
import discord
from flask import jsonify, request
import asyncio
from web.app import get_bot


def register_api_routes(app):
    """Registra todas las rutas de la API"""
    
    @app.route('/api/debug')
    def debug_info():
        """Endpoint de debug para ver información del bot"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        info = {
            "bot_listo": bot.is_ready(),
            "bot_user": str(bot.user) if bot.user else None,
            "servidores": []
        }
        
        for guild in bot.guilds:
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
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        servidores = []
        for guild in bot.guilds:
            servidores.append({
                "id": str(guild.id),
                "nombre": guild.name,
                "icono": str(guild.icon.url) if guild.icon else None,
                "miembros": guild.member_count
            })
        
        return jsonify(servidores)

    @app.route('/api/canales/<servidor_id>')
    def obtener_canales(servidor_id):
        """API: Obtiene los canales de texto de un servidor"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        guild = bot.get_guild(servidor_id)
        if not guild:
            ids_disponibles = [str(g.id) for g in bot.guilds]
            return jsonify({
                "error": "Servidor no encontrado",
                "servidor_buscado": servidor_id,
                "servidores_disponibles": ids_disponibles
            }), 404
        
        canales = []
        for channel in guild.text_channels:
            canales.append({
                "id": str(channel.id),
                "nombre": channel.name,
                "categoria": channel.category.name if channel.category else "Sin categoría",
                "posicion": channel.position
            })
        
        canales.sort(key=lambda x: (x['categoria'], x['posicion']))
        
        return jsonify(canales)

    @app.route('/api/usuarios/<servidor_id>')
    def obtener_usuarios(servidor_id):
        """API: Obtiene los usuarios de un servidor"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        guild = bot.get_guild(servidor_id)
        if not guild:
            return jsonify({"error": "Servidor no encontrado"}), 404
        
        usuarios = []
        for member in guild.members:
            if not member.bot:
                usuarios.append({
                    "id": str(member.id),
                    "nombre": member.name,
                    "display_name": member.display_name,
                    "avatar": str(member.avatar.url) if member.avatar else None
                })
        
        usuarios.sort(key=lambda x: x['display_name'].lower())
        
        return jsonify(usuarios)

    @app.route('/api/mensajes/<canal_id>')
    def obtener_mensajes(canal_id):
        """API: Obtiene los últimos mensajes de un canal"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        try:
            canal_id = int(canal_id)
        except ValueError:
            return jsonify({"error": "ID de canal inválido"}), 400
        
        canal = bot.get_channel(canal_id)
        if not canal:
            return jsonify({"error": "Canal no encontrado"}), 404
        
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
                bot.loop
            )
            mensajes = future.result(timeout=5)
            
            mensajes.reverse()
            
            return jsonify(mensajes)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/enviar', methods=['POST'])
    def enviar_mensaje():
        """API: Envía un mensaje a un canal"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        data = request.json
        canal_id = data.get('canal_id')
        mensaje = data.get('mensaje')
        
        if not canal_id or not mensaje:
            return jsonify({"error": "Faltan parámetros"}), 400
        
        canal = bot.get_channel(int(canal_id))
        if not canal:
            return jsonify({"error": "Canal no encontrado"}), 404
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                canal.send(mensaje),
                bot.loop
            )
            future.result(timeout=5)
            return jsonify({"success": True, "mensaje": "Mensaje enviado"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/stats')
    def obtener_estadisticas():
        """API: Obtiene estadísticas generales del bot"""
        bot = get_bot()
        if not bot:
            return jsonify({"error": "Bot no inicializado"}), 500
        
        total_canales = sum(len(guild.text_channels) for guild in bot.guilds)
        total_usuarios = sum(guild.member_count for guild in bot.guilds)
        
        return jsonify({
            "servidores": len(bot.guilds),
            "canales": total_canales,
            "usuarios": total_usuarios,
            "latencia": round(bot.latency * 1000, 2)
        })
    
 # ========================================
    # ENDPOINTS DE MÚSICA
    # ========================================
    
    @app.route('/api/music/<servidor_id>')
    def obtener_estado_musica(servidor_id):
        """API: Obtiene el estado actual del reproductor de música"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        # Si no existe el reproductor, devolver estado por defecto
        if servidor_id not in music_players:
            return jsonify({
                "connected": False,
                "current": None,
                "queue": [],
                "loop": False,
                "autoplay": False,
                "paused": False,
                "volume": 100
            })
        
        try:
            player = music_players[servidor_id]
            
            # Estado actual
            current_song = None
            if player.current:
                current_song = {
                    "title": player.current['title'],
                    "duration": player.current.get('duration', 0),
                    "thumbnail": player.current.get('thumbnail'),
                    "requested_by": player.current['requested_by'].display_name,
                    "url": player.current.get('webpage_url')
                }
            
            # Cola
            queue_list = []
            for i, song in enumerate(list(player.queue)):
                queue_list.append({
                    "index": i,
                    "title": song['title'],
                    "duration": song.get('duration', 0),
                    "requested_by": song['requested_by'].display_name
                })
            
            # Verificar si está conectado
            is_connected = player.voice_client is not None and player.voice_client.is_connected()
            
            # Verificar si está pausado
            is_paused = player.voice_client.is_paused() if (player.voice_client and player.voice_client.source) else False
            
            # Obtener volumen
            volume = 100
            if player.voice_client and player.voice_client.source and hasattr(player.voice_client.source, 'volume'):
                volume = int(player.voice_client.source.volume * 100)
            
            return jsonify({
                "connected": is_connected,
                "current": current_song,
                "queue": queue_list,
                "loop": player.loop_mode,
                "autoplay": player.autoplay,
                "paused": is_paused,
                "volume": volume
            })
        
        except Exception as e:
            print(f"[ERROR API MUSIC] {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/skip', methods=['POST'])
    def skip_cancion(servidor_id):
        """API: Salta la canción actual"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            
            if not player.voice_client or not player.voice_client.is_playing():
                return jsonify({"error": "No hay nada reproduciéndose"}), 400
            
            # Skip con permisos de admin
            player.voice_client.stop()
            
            return jsonify({"success": True, "message": "Canción saltada desde dashboard"})
        except Exception as e:
            print(f"[ERROR API SKIP] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/pause', methods=['POST'])
    def pausar_musica(servidor_id):
        """API: Pausa/reanuda la reproducción"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            
            if not player.voice_client:
                return jsonify({"error": "Bot no conectado"}), 400
            
            if player.voice_client.is_playing():
                player.voice_client.pause()
                return jsonify({"success": True, "paused": True})
            elif player.voice_client.is_paused():
                player.voice_client.resume()
                return jsonify({"success": True, "paused": False})
            else:
                return jsonify({"error": "No hay nada reproduciéndose"}), 400
        except Exception as e:
            print(f"[ERROR API PAUSE] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/stop', methods=['POST'])
    def detener_musica(servidor_id):
        """API: Detiene la reproducción y desconecta el bot"""
        from bot.music import music_players
        import asyncio
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            bot = get_bot()
            
            future = asyncio.run_coroutine_threadsafe(
                player.disconnect(),
                bot.loop
            )
            future.result(timeout=5)
            return jsonify({"success": True, "message": "Reproducción detenida"})
        except Exception as e:
            print(f"[ERROR API STOP] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/loop', methods=['POST'])
    def toggle_loop_musica(servidor_id):
        """API: Activa/desactiva el modo loop"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            loop_enabled = player.toggle_loop()
            
            return jsonify({"success": True, "loop": loop_enabled})
        except Exception as e:
            print(f"[ERROR API LOOP] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/autoplay', methods=['POST'])
    def toggle_autoplay_musica(servidor_id):
        """API: Activa/desactiva el autoplay"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            autoplay_enabled = player.toggle_autoplay()
            
            return jsonify({"success": True, "autoplay": autoplay_enabled})
        except Exception as e:
            print(f"[ERROR API AUTOPLAY] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/volume', methods=['POST'])
    def ajustar_volumen(servidor_id):
        """API: Ajusta el volumen del reproductor"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        data = request.json
        volumen = data.get('volume', 100)
        
        if volumen < 0 or volumen > 100:
            return jsonify({"error": "El volumen debe estar entre 0 y 100"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            
            if not player.voice_client or not player.voice_client.source:
                return jsonify({"error": "No hay nada reproduciéndose"}), 400
            
            # Verificar que sea PCMVolumeTransformer
            if isinstance(player.voice_client.source, discord.PCMVolumeTransformer):
                player.voice_client.source.volume = volumen / 100
                return jsonify({"success": True, "volume": volumen})
            else:
                return jsonify({"error": "Control de volumen no disponible"}), 400
                
        except Exception as e:
            print(f"[ERROR API VOLUME] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/remove/<int:index>', methods=['DELETE'])
    def eliminar_cancion_cola(servidor_id, index):
        """API: Elimina una canción específica de la cola"""
        from bot.music import music_players
        from collections import deque  # ← IMPORTANTE
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            
            if index < 0 or index >= len(player.queue):
                return jsonify({"error": "Índice inválido"}), 400
            
            # Convertir deque a lista, eliminar, y volver a deque
            queue_list = list(player.queue)
            removed_song = queue_list.pop(index)
            player.queue = deque(queue_list)
            
            return jsonify({
                "success": True, 
                "removed": removed_song['title'],
                "message": f"Canción eliminada de la cola"
            })
        except Exception as e:
            print(f"[ERROR API REMOVE] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/clear', methods=['POST'])
    def limpiar_cola(servidor_id):
        """API: Limpia toda la cola de reproducción"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        try:
            player = music_players[servidor_id]
            cantidad = len(player.queue)
            player.queue.clear()
            
            return jsonify({"success": True, "message": f"{cantidad} canciones eliminadas de la cola"})
        except Exception as e:
            print(f"[ERROR API CLEAR] {e}")
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/music/<servidor_id>/add', methods=['POST'])
    def agregar_cancion(servidor_id):
        """API: Agrega una canción a la cola"""
        from bot.music import music_players, get_player
        import re
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        data = request.json
        url_or_search = data.get('query')
        
        if not url_or_search:
            return jsonify({"error": "Debes proporcionar una URL o búsqueda"}), 400
        
        try:
            bot = get_bot()
            player = get_player(bot, servidor_id)
            
            # Si no es una URL, buscar en YouTube
            if not re.match(r'https?://', url_or_search):
                url_or_search = f"ytsearch:{url_or_search}"
            
            # Agregar a la cola
            future = asyncio.run_coroutine_threadsafe(
                player.add_to_queue(url_or_search, bot.user),
                bot.loop
            )
            song = future.result(timeout=10)
            
            if not song:
                return jsonify({"error": "No se pudo agregar la canción"}), 400
            
            # Si no está reproduciendo, iniciar
            if player.voice_client and not player.voice_client.is_playing() and not player.voice_client.is_paused():
                future = asyncio.run_coroutine_threadsafe(
                    player.play_next(),
                    bot.loop
                )
                future.result(timeout=5)
            
            return jsonify({
                "success": True,
                "message": f"Agregada: {song['title']}",
                "song": {
                    "title": song['title'],
                    "duration": song.get('duration', 0)
                }
            })
        except Exception as e:
            print(f"[ERROR API ADD] {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/reorder', methods=['POST'])
    def reordenar_cola(servidor_id):
        """API: Reordena la cola moviendo una canción"""
        from bot.music import music_players
        from collections import deque
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        data = request.json
        from_index = data.get('from')
        to_index = data.get('to')
        
        if from_index is None or to_index is None:
            return jsonify({"error": "Faltan parámetros"}), 400
        
        try:
            player = music_players[servidor_id]
            queue_list = list(player.queue)
            
            if from_index < 0 or from_index >= len(queue_list):
                return jsonify({"error": "Índice 'from' inválido"}), 400
            
            if to_index < 0 or to_index >= len(queue_list):
                return jsonify({"error": "Índice 'to' inválido"}), 400
            
            # Mover canción
            song = queue_list.pop(from_index)
            queue_list.insert(to_index, song)
            
            # Actualizar cola
            player.queue = deque(queue_list)
            
            return jsonify({
                "success": True,
                "message": f"Canción movida de posición {from_index + 1} a {to_index + 1}"
            })
        except Exception as e:
            print(f"[ERROR API REORDER] {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/music/<servidor_id>/seek', methods=['POST'])
    def seek_cancion(servidor_id):
        """API: Adelanta o atrasa la canción actual (limitado)"""
        from bot.music import music_players
        
        try:
            servidor_id = int(servidor_id)
        except ValueError:
            return jsonify({"error": "ID de servidor inválido"}), 400
        
        if servidor_id not in music_players:
            return jsonify({"error": "No hay reproductor activo"}), 404
        
        data = request.json
        seconds = data.get('seconds', 0)
        
        try:
            player = music_players[servidor_id]
            
            # Discord/FFmpeg no soporta seek nativo de forma fácil
            # La única forma es reiniciar la canción desde un punto específico
            # Por simplicidad, implementaremos skip forward/backward
            
            return jsonify({
                "error": "Función de seek no disponible (limitación de FFmpeg/Discord)",
                "info": "FFmpeg no permite adelantar/atrasar canciones en reproducción sin reiniciar desde el principio"
            }), 501
            
        except Exception as e:
            print(f"[ERROR API SEEK] {e}")
            return jsonify({"error": str(e)}), 500
    
    print("✅ Rutas de API registradas")