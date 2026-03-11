"""
Sistema de música del bot
"""
import discord
from discord.ext import commands
import asyncio
import yt_dlp
from collections import deque
import random

# Opciones de yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


class MusicPlayer:
    """Reproductor de música para un servidor"""
    
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = deque()
        self.current = None
        self.voice_client = None
        self.loop_mode = False
        self.autoplay = False
        self.message = None
        self.skip_votes = set()
        self.update_task = None
        self.last_channel = None
        
    async def join_channel(self, channel):
        """Conecta el bot al canal de voz"""
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()
        
    async def add_to_queue(self, url, requested_by):
        """Agrega una canción a la cola"""
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                song = {
                    'url': info['url'],
                    'title': info.get('title', 'Desconocido'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url', url),
                    'requested_by': requested_by
                }
                
                self.queue.append(song)
                return song
        except Exception as e:
            print(f"[ERROR MÚSICA] {e}")
            return None
    
    def format_duration(self, seconds):
        """Formatea la duración en mm:ss"""
        if not seconds:
            return "?"
        mins, secs = divmod(int(seconds), 60)
        return f"{mins}:{secs:02d}"
    
    async def get_related_song(self):
        """Obtiene una canción relacionada usando yt-dlp"""
        if not self.current:
            return None
        
        try:
            current_url = self.current.get('webpage_url')
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': 5,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(current_url, download=False)
                
                related_videos = []
                
                if 'entries' in info and info['entries']:
                    related_videos = info['entries']
                
                if not related_videos:
                    title = self.current['title']
                    search_query = f"ytsearch5:{title}"
                    
                    search_info = ydl.extract_info(search_query, download=False)
                    if 'entries' in search_info:
                        related_videos = search_info['entries']
                
                if related_videos:
                    filtered = [v for v in related_videos if v.get('id') != info.get('id')]
                    
                    if filtered:
                        selected = random.choice(filtered[:3])
                        video_url = f"https://www.youtube.com/watch?v={selected['id']}"
                        return video_url
            
            return None
            
        except Exception as e:
            print(f"[ERROR AUTOPLAY] {e}")
            return None
    
    async def start_update_task(self):
        """Inicia la tarea de actualización periódica del HUD"""
        if self.update_task and not self.update_task.done():
            return
        
        async def update_loop():
            try:
                last_message_id = None
                
                while self.voice_client and self.voice_client.is_connected():
                    await asyncio.sleep(30)
                    
                    if self.message and self.last_channel:
                        try:
                            async for msg in self.last_channel.history(limit=1):
                                current_last_message_id = msg.id
                                break
                            else:
                                continue
                            
                            if last_message_id is None:
                                last_message_id = current_last_message_id
                            elif current_last_message_id != last_message_id:
                                last_message_id = current_last_message_id
                                
                                try:
                                    await self.message.delete()
                                except:
                                    pass
                                
                                embed = self.create_embed()
                                view = self.create_buttons()
                                self.message = await self.last_channel.send(embed=embed, view=view)
                                
                                last_message_id = self.message.id
                        
                        except Exception as e:
                            print(f"[ERROR CHECKING MESSAGES] {e}")
                            
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"[ERROR UPDATE TASK] {e}")
        
        self.update_task = asyncio.create_task(update_loop())
    
    async def stop_update_task(self):
        """Detiene la tarea de actualización periódica"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def play_next(self):
        """Reproduce la siguiente canción"""
        self.skip_votes.clear()
        
        if self.loop_mode and self.current:
            self.queue.appendleft(self.current)
        
        # Autoplay: buscar canción relacionada si la cola está vacía
        if not self.queue and self.autoplay and self.current:
            print("[AUTOPLAY] Buscando canción relacionada...")
            related_url = await self.get_related_song()
            
            if related_url:
                bot_user = self.bot.user
                song = await self.add_to_queue(related_url, bot_user)
                
                if song:
                    print(f"[AUTOPLAY] Agregada: {song['title']}")
        
        if not self.queue:
            self.current = None
            
            await self.stop_update_task()
            
            if self.message:
                await self.update_control_message()
                
                await asyncio.sleep(5)
                if not self.current and self.message:
                    try:
                        await self.message.delete()
                        self.message = None
                    except:
                        pass
            
            return
        
        self.current = self.queue.popleft()
        
        try:
            # Crear fuente de audio con control de volumen
            audio_source = discord.FFmpegPCMAudio(self.current['url'], **FFMPEG_OPTIONS)
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=1.0)  # ← CAMBIO AQUÍ
            
            def after_playing(error):
                if error:
                    print(f"[ERROR REPRODUCCIÓN] {error}")
                
                coro = self.play_next()
                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"[ERROR] {e}")
            
            self.voice_client.play(audio_source, after=after_playing)
            
            if self.message:
                await self.update_control_message()
            
            await self.start_update_task()
            
        except Exception as e:
            print(f"[ERROR AL REPRODUCIR] {e}")
            await self.play_next()
    
    async def pause(self):
        """Pausa la reproducción"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await self.update_control_message()
    
    async def resume(self):
        """Reanuda la reproducción"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await self.update_control_message()
    
    async def skip(self, user_id=None):
        """Salta a la siguiente canción (con sistema de votos)"""
        from config import ZORCUZ_ID
        
        if not self.current or not self.voice_client:
            return False, "No hay nada reproduciéndose"
        
        # Si es Zorcuz, skip directo
        if user_id == ZORCUZ_ID:
            if self.voice_client.is_playing():
                self.voice_client.stop()
            return True, "Canción saltada por el dios Zorcuz"
        
        # Si es el que pidió la canción, skip directo
        if user_id == self.current['requested_by'].id:
            if self.voice_client.is_playing():
                self.voice_client.stop()
            return True, "Canción saltada por quien la pidió"
        
        # Si no hay canciones en cola y autoplay está desactivado, no permitir skip por votos
        if not self.queue and not self.autoplay:
            return False, "No hay más canciones en la cola (activa Autoplay para continuar)"
        
        # Sistema de votos para otros usuarios
        if user_id:
            self.skip_votes.add(user_id)
        
        if self.voice_client.channel:
            users_in_channel = len([m for m in self.voice_client.channel.members if not m.bot])
            votes_needed = max(2, users_in_channel // 2)
            
            if len(self.skip_votes) >= votes_needed:
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                
                # Mensaje especial si autoplay está activo y cola vacía
                if not self.queue and self.autoplay:
                    return True, f"Canción saltada por votación ({len(self.skip_votes)}/{votes_needed} votos) - Autoplay buscando siguiente..."
                else:
                    return True, f"Canción saltada por votación ({len(self.skip_votes)}/{votes_needed} votos)"
            else:
                return False, f"Voto registrado ({len(self.skip_votes)}/{votes_needed} votos necesarios)"
        
        return False, "Error al procesar skip"
    
    async def stop(self):
        """Detiene la reproducción y limpia la cola"""
        self.queue.clear()
        self.current = None
        self.skip_votes.clear()
        if self.voice_client:
            self.voice_client.stop()
        await self.update_control_message()
    
    async def disconnect(self):
        """Desconecta el bot del canal de voz"""
        await self.stop()
        
        await self.stop_update_task()
        
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
            self.message = None
    
    def toggle_loop(self):
        """Activa/desactiva el modo loop"""
        self.loop_mode = not self.loop_mode
        return self.loop_mode
    
    def toggle_autoplay(self):
        """Activa/desactiva el autoplay"""
        self.autoplay = not self.autoplay
        return self.autoplay
    
    def create_embed(self):
        """Crea el embed de control"""
        if not self.current:
            embed = discord.Embed(
                title="🎵 Reproductor de Música",
                description="No hay nada reproduciéndose",
                color=discord.Color.blue()
            )
            return embed
        
        embed = discord.Embed(
            title="🎵 Reproduciendo",
            description=f"**{self.current['title']}**",
            color=discord.Color.green() if not self.voice_client.is_paused() else discord.Color.orange()
        )
        
        if self.current.get('thumbnail'):
            embed.set_thumbnail(url=self.current['thumbnail'])
        
        duration = self.format_duration(self.current.get('duration', 0))
        embed.add_field(name="⏱️ Duración", value=duration, inline=True)
        embed.add_field(
            name="👤 Solicitado por", 
            value=self.current['requested_by'].mention, 
            inline=True
        )
        
        if self.queue:
            queue_text = "\n".join([
                f"{i+1}. {song['title'][:50]}" 
                for i, song in enumerate(list(self.queue)[:5])
            ])
            if len(self.queue) > 5:
                queue_text += f"\n... y {len(self.queue) - 5} más"
            embed.add_field(name=f"📋 Cola ({len(self.queue)})", value=queue_text, inline=False)
        
        status = []
        if self.loop_mode:
            status.append("🔁 Loop")
        if self.autoplay:
            status.append("🎲 Autoplay")
        
        if status:
            embed.set_footer(text=" | ".join(status))
        
        return embed
    
    def create_buttons(self):
        """Crea los botones de control"""
        view = MusicControlView(self)
        return view
    
    async def update_control_message(self, channel=None):
        """Actualiza el mensaje de control"""
        embed = self.create_embed()
        view = self.create_buttons()
        
        if channel:
            self.last_channel = channel
        
        if self.message:
            try:
                await self.message.edit(embed=embed, view=view)
            except discord.NotFound:
                if self.last_channel:
                    self.message = await self.last_channel.send(embed=embed, view=view)
                else:
                    self.message = None
            except Exception as e:
                print(f"[ERROR ACTUALIZAR HUD] {e}")
                if self.last_channel:
                    try:
                        self.message = await self.last_channel.send(embed=embed, view=view)
                    except:
                        self.message = None
                else:
                    self.message = None
        elif channel or self.last_channel:
            target_channel = channel or self.last_channel
            self.message = await target_channel.send(embed=embed, view=view)
        
        return embed, view


class MusicControlView(discord.ui.View):
    """Vista con botones de control de música"""
    
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player
    
    @discord.ui.button(emoji="⏸️", label="Pausar", style=discord.ButtonStyle.primary, custom_id="pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.player.voice_client and self.player.voice_client.is_playing():
                await self.player.pause()
                button.emoji = "▶️"
                button.label = "Reanudar"
            elif self.player.voice_client and self.player.voice_client.is_paused():
                await self.player.resume()
                button.emoji = "⏸️"
                button.label = "Pausar"
            
            await interaction.response.edit_message(embed=self.player.create_embed(), view=self)
        except discord.NotFound:
            await interaction.response.send_message("⚠️ El panel de control expiró. Usa `$nowplaying` para obtener uno nuevo.", ephemeral=True)
        except Exception as e:
            print(f"[ERROR BOTÓN PAUSE] {e}")
            await interaction.response.send_message("❌ Error al procesar el botón", ephemeral=True)
    
    @discord.ui.button(emoji="⏭️", label="Skip", style=discord.ButtonStyle.primary, custom_id="skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            success, message = await self.player.skip(interaction.user.id)
            await interaction.response.send_message(f"{'✅' if success else '🗳️'} {message}", ephemeral=True)
        except Exception as e:
            print(f"[ERROR BOTÓN SKIP] {e}")
            await interaction.response.send_message("❌ Error al procesar skip", ephemeral=True)
    
    @discord.ui.button(emoji="📋", label="Cola", style=discord.ButtonStyle.success, custom_id="queue")
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(
                title="📋 Cola de Reproducción",
                color=discord.Color.blue()
            )
            
            if self.player.current:
                embed.add_field(
                    name="🎵 Reproduciendo ahora",
                    value=f"**{self.player.current['title']}**\nDuración: {self.player.format_duration(self.player.current.get('duration', 0))}\nSolicitado por: {self.player.current['requested_by'].mention}",
                    inline=False
                )
            
            if self.player.queue:
                queue_text = "\n".join([
                    f"{i+1}. **{song['title'][:50]}** ({self.player.format_duration(song.get('duration', 0))})\n   Solicitado por: {song['requested_by'].mention}"
                    for i, song in enumerate(list(self.player.queue)[:10])
                ])
                
                if len(self.player.queue) > 10:
                    queue_text += f"\n\n*... y {len(self.player.queue) - 10} canciones más*"
                
                embed.add_field(name=f"Siguiente ({len(self.player.queue)} en cola)", value=queue_text, inline=False)
            else:
                if not self.player.current:
                    embed.description = "La cola está vacía"
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[ERROR BOTÓN COLA] {e}")
            await interaction.response.send_message("❌ Error al mostrar la cola", ephemeral=True)
    
    @discord.ui.button(emoji="🔁", label="Loop", style=discord.ButtonStyle.secondary, custom_id="loop")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            loop_enabled = self.player.toggle_loop()
            button.style = discord.ButtonStyle.success if loop_enabled else discord.ButtonStyle.secondary
            await interaction.response.edit_message(embed=self.player.create_embed(), view=self)
        except discord.NotFound:
            await interaction.response.send_message("⚠️ El panel de control expiró. Usa `$nowplaying` para obtener uno nuevo.", ephemeral=True)
        except Exception as e:
            print(f"[ERROR BOTÓN LOOP] {e}")
            await interaction.response.send_message("❌ Error al cambiar loop", ephemeral=True)
    
    @discord.ui.button(emoji="🎲", label="Autoplay", style=discord.ButtonStyle.secondary, custom_id="autoplay")
    async def autoplay_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            autoplay_enabled = self.player.toggle_autoplay()
            button.style = discord.ButtonStyle.success if autoplay_enabled else discord.ButtonStyle.secondary
            
            await interaction.response.send_message(
                "🎲 Autoplay activado (reproducirá canciones relacionadas automáticamente)" if autoplay_enabled else "🎲 Autoplay desactivado",
                ephemeral=True
            )
        except Exception as e:
            print(f"[ERROR BOTÓN AUTOPLAY] {e}")
            await interaction.response.send_message("❌ Error al cambiar autoplay", ephemeral=True)
    
    @discord.ui.button(emoji="⏹️", label="Detener", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.player.disconnect()
            await interaction.response.send_message("⏹️ Reproducción detenida y desconectado", ephemeral=True)
        except Exception as e:
            print(f"[ERROR BOTÓN STOP] {e}")
            await interaction.response.send_message("❌ Error al detener", ephemeral=True)


music_players = {}


def get_player(bot, guild_id):
    """Obtiene o crea un reproductor para un servidor"""
    if guild_id not in music_players:
        music_players[guild_id] = MusicPlayer(bot, guild_id)
    return music_players[guild_id]