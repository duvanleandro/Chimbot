"""
Aplicación Flask para el dashboard
"""
from flask import Flask
from threading import Thread

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Variable global para el bot
bot_instance = None


def set_bot(bot):
    """Establece la referencia al bot de Discord"""
    global bot_instance
    bot_instance = bot


def get_bot():
    """Obtiene la referencia al bot de Discord"""
    return bot_instance


def run():
    """Ejecuta el servidor Flask"""
    app.run(host='0.0.0.0', port=8080, debug=False)


def keep_alive(bot):
    """Inicia el servidor Flask y guarda referencia al bot"""
    set_bot(bot)
    
    # Importar y registrar rutas DESPUÉS de tener el bot
    from .routes.api import register_api_routes
    from .routes.views import register_view_routes
    
    register_api_routes(app)
    register_view_routes(app)
    
    # Iniciar servidor en thread separado
    server = Thread(target=run, daemon=True)
    server.start()
    print("✅ Dashboard web iniciado en http://localhost:8080/dashboard")