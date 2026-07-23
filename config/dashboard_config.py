"""
Configuración persistente del dashboard
"""
import json
import os

CONFIG_FILE = "dashboard_config.json"

DEFAULT_CONFIG = {
    "spam": {
        "activo": False,
        "frecuencia_horas": 12,
        "usar_ia": False,
        "mensajes": [
            {"texto": "Hola Chimboland 🎮", "repeticiones": 1},
            {"texto": "¿Qué más pues?", "repeticiones": 1}
        ]
    },
    "ia": {
        "respuestas_activas": True,
        "probabilidad": 0.02
    },
    "usuarios_favoritos": [
        {"id": "708005339282276392", "nombre": "Zorcuz", "apodo": "Dios"}
    ]
}

def cargar_config():
    """Carga la configuración desde el archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()

def guardar_config(config):
    """Guarda la configuración en el archivo JSON"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def obtener_mensajes_spam():
    """Obtiene los mensajes configurados para spam"""
    config = cargar_config()
    mensajes = []
    
    if config["spam"]["usar_ia"]:
        # Si usa IA, generar mensaje con Groq
        return ["IA_GENERADO"]  # Señal especial
    
    # Si usa mensajes estáticos
    for msg_config in config["spam"]["mensajes"]:
        for _ in range(msg_config["repeticiones"]):
            mensajes.append(msg_config["texto"])
    
    return mensajes

def esta_spam_activo():
    """Verifica si el spam está activo"""
    config = cargar_config()
    return config["spam"]["activo"]

def esta_ia_activa():
    """Verifica si la IA está activa"""
    config = cargar_config()
    return config["ia"]["respuestas_activas"]

def obtener_probabilidad_ia():
    """Obtiene la probabilidad de respuesta de IA"""
    config = cargar_config()
    return config["ia"]["probabilidad"]