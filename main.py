"""
ChimBot - Bot de Discord con Dashboard Web
Entry point principal
"""
import os
from dotenv import load_dotenv
from bot import init_bot
from web.app import keep_alive  # ← Importar directamente desde web.app

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal"""
    # Inicializar bot
    bot = init_bot()
    
    # Iniciar webserver (dashboard)
    keep_alive(bot)
    
    # Iniciar bot de Discord
    TOKEN = os.getenv('TOKEN')
    if not TOKEN:
        print("❌ ERROR: No se encontró el TOKEN en las variables de entorno")
        return
    
    print("🚀 Iniciando ChimBot...")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()