"""
Comandos de música del bot
"""
import discord
from discord.ext import commands
from .music import get_player
import re


def setup_music_commands(bot):
    """Registra todos los comandos de música"""
    
    @bot.command(name='play', aliases=['p'])
    async def play(ctx, *, url_or_search: str = None):
        """Reproduce una canción de YouTube"""
        # Verificar que el usuario esté en un canal de voz
        if not ctx.author.voice:
            await ctx.send("❌ Debes estar en un canal de voz para usar este comando", delete_after=5)
            return
        
        # Si no hay URL, mostrar ayuda
        if not url_or_search:
            await ctx.send("❌ Debes proporcionar una URL de YouTube o búsqueda\nEjemplo: `$play https://youtube.com/watch?v=...`", delete_after=5)
            return
        
        player = get_player(bot, ctx.guild.id)
        
        # Conectar al canal de voz si no está conectado
        if not player.voice_client or not player.voice_client.is_connected():
            await player.join_channel(ctx.author.voice.channel)
        
        # Borrar comando del usuario
        try:
            await ctx.message.delete()
        except:
            pass
        
        async with ctx.typing():
            # Si no es una URL, buscar en YouTube
            if not re.match(r'https?://', url_or_search):
                url_or_search = f"ytsearch:{url_or_search}"
            
            song = await player.add_to_queue(url_or_search, ctx.author)
            
            if not song:
                await ctx.send("❌ No se pudo agregar la canción", delete_after=5)
                return
            
            # Si no está reproduciendo nada, empezar
            if not player.voice_client.is_playing() and not player.voice_client.is_paused():
                await player.play_next()
                
                # Crear mensaje de control SI NO EXISTE
                if not player.message:
                    embed, view = await player.update_control_message(channel=ctx.channel)
            else:
                # Notificar que se agregó a la cola (SIN auto-borrar)
                embed = discord.Embed(
                    title="✅ Agregado a la cola",
                    description=f"**{song['title']}**",
                    color=discord.Color.green()
                )
                embed.add_field(name="Posición", value=f"#{len(player.queue)}", inline=True)
                embed.add_field(name="Duración", value=player.format_duration(song.get('duration', 0)), inline=True)
                
                if song.get('thumbnail'):
                    embed.set_thumbnail(url=song['thumbnail'])
                
                # NO tiene delete_after - se queda permanentemente
                await ctx.send(embed=embed)
    
    @bot.command(name='pause')
    async def pause(ctx):
        """Pausa la reproducción"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.voice_client or not player.voice_client.is_playing():
            await ctx.send("❌ No hay nada reproduciéndose", delete_after=5)
            return
        
        await player.pause()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("⏸️ Pausado", delete_after=5)
    
    @bot.command(name='resume', aliases=['unpause'])
    async def resume(ctx):
        """Reanuda la reproducción"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.voice_client or not player.voice_client.is_paused():
            await ctx.send("❌ No hay nada pausado", delete_after=5)
            return
        
        await player.resume()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("▶️ Reanudado", delete_after=5)
    
    @bot.command(name='skip', aliases=['s', 'next'])
    async def skip(ctx):
        """Salta a la siguiente canción"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.voice_client or not player.voice_client.is_playing():
            await ctx.send("❌ No hay nada reproduciéndose", delete_after=5)
            return
        
        success, message = await player.skip(ctx.author.id)
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send(f"{'✅' if success else '🗳️'} {message}", delete_after=5)
    
    @bot.command(name='stop', aliases=['leave', 'disconnect'])
    async def stop(ctx):
        """Detiene la reproducción y desconecta el bot"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.voice_client:
            await ctx.send("❌ No estoy en un canal de voz", delete_after=5)
            return
        
        await player.disconnect()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("⏹️ Reproducción detenida", delete_after=5)
    
    @bot.command(name='queue', aliases=['q', 'lista'])
    async def queue(ctx):
        """Muestra la cola de reproducción"""
        player = get_player(bot, ctx.guild.id)
        
        embed = discord.Embed(
            title="📋 Cola de Reproducción",
            color=discord.Color.blue()
        )
        
        if player.current:
            embed.add_field(
                name="🎵 Reproduciendo ahora",
                value=f"**{player.current['title']}**\nDuración: {player.format_duration(player.current.get('duration', 0))}\nSolicitado por: {player.current['requested_by'].mention}",
                inline=False
            )
        
        if player.queue:
            queue_text = "\n".join([
                f"{i+1}. **{song['title'][:40]}** ({player.format_duration(song.get('duration', 0))})\n   Por: {song['requested_by'].mention}"
                for i, song in enumerate(list(player.queue)[:10])
            ])
            
            if len(player.queue) > 10:
                queue_text += f"\n\n*... y {len(player.queue) - 10} canciones más*"
            
            embed.add_field(name=f"Siguiente ({len(player.queue)} en cola)", value=queue_text, inline=False)
        else:
            if not player.current:
                embed.description = "La cola está vacía"
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Mensaje se auto-borra después de 30 segundos
        await ctx.send(embed=embed, delete_after=30)
    
    @bot.command(name='nowplaying', aliases=['np', 'current', 'now'])
    async def nowplaying(ctx):
        """Muestra la canción actual"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.current:
            await ctx.send("❌ No hay nada reproduciéndose", delete_after=5)
            return
        
        embed, view = await player.update_control_message()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send(embed=embed, view=view, delete_after=60)
    
    @bot.command(name='loop', aliases=['repeat'])
    async def loop(ctx):
        """Activa/desactiva el modo loop"""
        player = get_player(bot, ctx.guild.id)
        
        loop_enabled = player.toggle_loop()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        if loop_enabled:
            await ctx.send("🔁 Loop activado", delete_after=5)
        else:
            await ctx.send("🔁 Loop desactivado", delete_after=5)
        
        if player.message:
            await player.update_control_message()
    
    @bot.command(name='clear', aliases=['clean'])
    async def clear(ctx):
        """Limpia la cola de reproducción"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.queue:
            await ctx.send("❌ La cola ya está vacía", delete_after=5)
            return
        
        cantidad = len(player.queue)
        player.queue.clear()
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send(f"🗑️ Se limpiaron {cantidad} canciones de la cola", delete_after=5)
    
    @bot.command(name='shuffle', aliases=['mix'])
    async def shuffle(ctx):
        """Mezcla la cola de reproducción"""
        import random
        
        player = get_player(bot, ctx.guild.id)
        
        if len(player.queue) < 2:
            await ctx.send("❌ No hay suficientes canciones para mezclar", delete_after=5)
            return
        
        queue_list = list(player.queue)
        random.shuffle(queue_list)
        player.queue = type(player.queue)(queue_list)
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send("🔀 Cola mezclada", delete_after=5)
    
    @bot.command(name='volume', aliases=['vol'])
    async def volume(ctx, volumen: int = None):
        """Ajusta el volumen (0-100)"""
        player = get_player(bot, ctx.guild.id)
        
        if not player.voice_client or not player.voice_client.source:
            await ctx.send("❌ No hay nada reproduciéndose", delete_after=5)
            return
        
        # Verificar que sea PCMVolumeTransformer
        if not isinstance(player.voice_client.source, discord.PCMVolumeTransformer):
            await ctx.send("❌ Control de volumen no disponible", delete_after=5)
            return
        
        if volumen is None:
            await ctx.send(f"🔊 Volumen actual: {int(player.voice_client.source.volume * 100)}%", delete_after=5)
            return
        
        if volumen < 0 or volumen > 100:
            await ctx.send("❌ El volumen debe estar entre 0 y 100", delete_after=5)
            return
        
        player.voice_client.source.volume = volumen / 100
        
        # Borrar comando
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send(f"🔊 Volumen ajustado a {volumen}%", delete_after=5)
        
    print("✅ Comandos de música registrados")