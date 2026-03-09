"""
Módulo de utilidades compartidas
"""
from .ai import obtener_respuesta_gemini, debe_responder, procesar_respuesta, interpretar_instruccion_ia
from .moderation import detectar_spam_rapido, detectar_spam_repetido, silenciar_usuario
from .helpers import obtener_info_usuario, obtener_roles_usuario, obtener_meme_shitpost, obtener_copypasta