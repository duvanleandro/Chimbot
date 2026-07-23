"""
Módulo de configuración del bot
"""
from .settings import *
from .personalidades import USUARIOS_PERSONALIDADES
from .prompts import SISTEMA_PROMPT, SISTEMA_PROMPT_ZORCUZ
from .mensajes import mensajes_random, mensajes_disponibles, obtener_mensaje_sin_repetir
from .insultos import INSULTOS_GRUPO
from .dashboard_config import (
    cargar_config,
    guardar_config,
    obtener_mensajes_spam,
    esta_spam_activo,
    esta_ia_activa,
    obtener_probabilidad_ia
)