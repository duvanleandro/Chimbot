"""
Tareas periódicas del bot
"""
from discord.ext import tasks
from datetime import datetime
from config import CANAL_SPAM_ID

spam_periodico = None

def setup_tasks(bot):
    """Configura las tareas periódicas del bot"""
    global spam_periodico
    
    @tasks.loop(hours=12)
    async def spam_periodico_task():
        """Envía mensajes al canal de spam periódicamente"""
        from config.dashboard_config import obtener_mensajes_spam, cargar_config
        
        try:
            config = cargar_config()
            
            # Verificar si debe estar activo
            if not config["spam"]["activo"]:
                return
            
            canal = bot.get_channel(CANAL_SPAM_ID)
            if not canal:
                print("[ERROR] No se encontró el canal de spam")
                return
            
            mensajes = obtener_mensajes_spam()
            
            # Si usa IA
            if mensajes == ["IA_GENERADO"]:
                from utils.ai import obtener_respuesta_groq
                
                prompt = "Genera un mensaje corto y divertido para un servidor de Discord de gaming. Sé creativo y casual."
                mensaje_ia = await obtener_respuesta_groq(prompt)
                
                if mensaje_ia:
                    await canal.send(mensaje_ia)
                    print(f"[SPAM IA] Mensaje generado y enviado")
                return
            
            # Si usa mensajes estáticos
            for mensaje in mensajes:
                await canal.send(mensaje)
                print(f"[SPAM] Enviado: {mensaje[:50]}...")
        
        except Exception as e:
            print(f"Error en spam_periodico: {e}")
    
    # Cambiar frecuencia dinámicamente
    async def actualizar_frecuencia():
        from config.dashboard_config import cargar_config
        config = cargar_config()
        spam_periodico_task.change_interval(hours=config["spam"]["frecuencia_horas"])
    
    @spam_periodico_task.before_loop
    async def antes_de_spam():
        """Espera a que el bot esté listo"""
        await bot.wait_until_ready()
        await actualizar_frecuencia()
        print("Sistema de spam periódico listo")
    
    spam_periodico = spam_periodico_task
    
    # Auto-iniciar si estaba activo
    from config.dashboard_config import esta_spam_activo
    if esta_spam_activo():
        spam_periodico.start()
        print("✅ Spam iniciado automáticamente")
    
    print("✅ Tareas periódicas configuradas")