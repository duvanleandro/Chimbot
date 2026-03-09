"""
Funciones de moderación y detección de spam
"""
import discord
from datetime import timedelta
from collections import defaultdict
from config import LIMITE_MENSAJES, TIEMPO_LIMITE, LIMITE_REPETICIONES

# Contadores globales
spam_contador = defaultdict(lambda: {'mensajes': [], 'ultimos_textos': []})


def detectar_spam_rapido(user_id, timestamp):
    """Detecta si un usuario está enviando mensajes demasiado rápido"""
    data = spam_contador[user_id]
    data['mensajes'].append(timestamp)
    tiempo_limite = timestamp - TIEMPO_LIMITE
    data['mensajes'] = [t for t in data['mensajes'] if t > tiempo_limite]
    return len(data['mensajes']) >= LIMITE_MENSAJES


def detectar_spam_repetido(user_id, texto):
    """Detecta si un usuario está enviando el mismo mensaje repetidamente"""
    data = spam_contador[user_id]
    data['ultimos_textos'].append(texto.lower().strip())
    
    if len(data['ultimos_textos']) > 10:
        data['ultimos_textos'].pop(0)
    
    if len(data['ultimos_textos']) >= LIMITE_REPETICIONES:
        ultimo_texto = data['ultimos_textos'][-1]
        count = data['ultimos_textos'].count(ultimo_texto)
        return count >= LIMITE_REPETICIONES
    
    return False


async def silenciar_usuario(member, duracion_segundos=10):
    """Aplica timeout a un usuario por X segundos"""
    try:
        duracion = timedelta(seconds=duracion_segundos)
        await member.timeout(duracion, reason="Spam detectado")
        return True
    except discord.Forbidden:
        print(f"No tengo permisos para silenciar a {member.name}")
        return False
    except Exception as e:
        print(f"Error al silenciar: {e}")
        return False