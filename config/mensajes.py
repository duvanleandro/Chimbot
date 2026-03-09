"""
Mensajes para el sistema de spam periódico
"""
import random

mensajes_random = ["pene"]
mensajes_disponibles = []

def obtener_mensaje_sin_repetir():
    """Obtiene un mensaje random sin repetir hasta que se agoten todos"""
    global mensajes_disponibles
    
    if not mensajes_random:
        return "No hay mensajes configurados. Agrega mensajes a la lista 'mensajes_random' en el código."
    
    if not mensajes_disponibles:
        mensajes_disponibles = mensajes_random.copy()
        random.shuffle(mensajes_disponibles)
    
    return mensajes_disponibles.pop()