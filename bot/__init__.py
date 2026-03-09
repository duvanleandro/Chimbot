"""
Módulo del bot de Discord
"""
from .client import bot
from .commands import setup_commands
from .events import setup_events
from .tasks import setup_tasks

def init_bot():
    """Inicializa todos los componentes del bot"""
    setup_commands(bot)
    setup_events(bot)
    setup_tasks(bot)
    return bot