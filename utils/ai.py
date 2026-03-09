"""
Funciones relacionadas con IA (Groq)
"""
import os
import random
from groq import Groq
from config import SISTEMA_PROMPT, SISTEMA_PROMPT_ZORCUZ, INSULTOS_GRUPO, ZORCUZ_ID, PROBABILIDAD_RESPUESTA
from .helpers import obtener_info_usuario, obtener_roles_usuario

# Cliente de Groq (inicialización lazy)
groq_client = None


def get_groq_client():
    """Obtiene el cliente de Groq (inicialización lazy)"""
    global groq_client
    if groq_client is None:
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY no encontrada en las variables de entorno")
        groq_client = Groq(api_key=GROQ_API_KEY)
    return groq_client


async def obtener_respuesta_gemini(prompt, contexto="", user_id=None, member=None):
    """Obtiene una respuesta de Groq con contexto del chat"""
    try:
        # Obtener info del usuario si existe
        info_usuario = obtener_info_usuario(user_id) if user_id else None

        # Obtener roles del usuario si es posible
        roles = await obtener_roles_usuario(member) if member else []
        
        # Agregar info del usuario al contexto si existe
        if info_usuario:
            contexto += f"\n\nINFO DEL USUARIO QUE HABLA: {info_usuario}"

        # Agregar roles del usuario al contexto si existen
        if roles:
            contexto += f"\nROLES: {', '.join(roles)}"
            if "veneco" in [r.lower() for r in roles]:
                contexto += "\nIMPORTANTE: Este usuario es 'veneco' o venezolano, puedes insultarlo diciendo 'veneco'"
        
        mensaje_completo = f"{contexto}\n\n{prompt}"
        
        # Usar prompt diferente si quien habla es Zorcuz
        sistema_prompt = SISTEMA_PROMPT_ZORCUZ if user_id == ZORCUZ_ID else SISTEMA_PROMPT.format(
            insultos=", ".join(INSULTOS_GRUPO)
        )
        
        client = get_groq_client()  # ← CAMBIO AQUÍ
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sistema_prompt},
                {"role": "user", "content": mensaje_completo}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        
        return response.choices[0].message.content if response.choices else None
    except Exception as e:
        print(f"[ERROR GROQ] {e}")
        return None


async def debe_responder():
    """Determina si el bot debe responder automáticamente"""
    return random.random() < PROBABILIDAD_RESPUESTA


async def procesar_respuesta(respuesta):
    """Procesa la respuesta de Groq para dividirla en múltiples mensajes"""
    if not respuesta:
        return []
    
    oraciones = respuesta.split('. ')
    mensajes = []
    mensaje_actual = ""
    
    for oracion in oraciones:
        if len(mensaje_actual) + len(oracion) < 2000:
            mensaje_actual += oracion + ". " if not oracion.endswith('.') else oracion + " "
        else:
            if mensaje_actual:
                mensajes.append(mensaje_actual.strip())
            mensaje_actual = oracion + ". " if not oracion.endswith('.') else oracion + " "
    
    if mensaje_actual:
        mensajes.append(mensaje_actual.strip())
    
    return [m for m in mensajes if m]


async def interpretar_instruccion_ia(texto, user_id):
    """Usa IA para interpretar si un mensaje contiene una instrucción de comando"""
    try:
        prompt_interpretacion = f"""Analiza este mensaje y determina si es una INSTRUCCIÓN para ejecutar un comando del bot.

Responde SOLO con uno de estos formatos:
- "COMANDO:borrar:<cantidad>" si pide borrar mensajes (ej: "borra 5 mensajes", "elimina los 10 últimos")
- "COMANDO:activarspam" si pide activar spam automático
- "COMANDO:desactivarspam" si pide desactivar spam
- "COMANDO:statusspam" si pide ver estado del spam
- "COMANDO:testspam" si pide enviar un mensaje de prueba
- "COMANDO:ayuda" si pide ayuda o list de comandos
- "NO_COMANDO" si es una conversación normal sin instrucciones

Mensaje: {texto}"""

        sistema_prompt = SISTEMA_PROMPT_ZORCUZ if user_id == ZORCUZ_ID else "Eres un interpretador de comandos."
        
        client = get_groq_client()  # ← CAMBIO AQUÍ
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sistema_prompt},
                {"role": "user", "content": prompt_interpretacion}
            ],
            temperature=0.3,
            max_tokens=100,
        )
        
        resultado = response.choices[0].message.content.strip() if response.choices else "NO_COMANDO"
        return resultado
    except Exception as e:
        print(f"[ERROR INTERPRETACIÓN] {e}")
        return "NO_COMANDO"