"""
Tareas periódicas del bot
"""
from discord.ext import tasks
from datetime import datetime
from config import CANAL_SPAM_ID, obtener_mensaje_sin_repetir


spam_periodico = None


def setup_tasks(bot):
    """Configura las tareas periódicas del bot"""
    global spam_periodico
    
    @tasks.loop(hours=12)
    async def spam_periodico_task():
        """Envía un mensaje random al canal de spam periódicamente"""
        try:
            canal = bot.get_channel(CANAL_SPAM_ID)
            if canal:
                mensaje = obtener_mensaje_sin_repetir()
                await canal.send(mensaje)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Mensaje automático enviado: {mensaje[:50]}...")
        except Exception as e:
            print(f"Error en spam_periodico: {e}")

    @spam_periodico_task.before_loop
    async def antes_de_spam():
        """Espera a que el bot esté listo antes de iniciar el loop"""
        await bot.wait_until_ready()
        print("Sistema de spam periódico iniciado (PAUSADO por defecto)")
    
    spam_periodico = spam_periodico_task
    print("✅ Tareas periódicas configuradas")