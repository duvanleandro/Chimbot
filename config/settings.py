"""
Configuración general del bot
"""

# IDs de canales
CANAL_SPAM_ID = 1004171793101230151
CANAL_BIENVENIDA_ID = 1004156875035656303
CANAL_MEMES_ID = 1457786102181265675

# IDs de usuarios especiales
ZORCUZ_ID = 708005339282276392

# Configuración de spam
LIMITE_MENSAJES = 4
TIEMPO_LIMITE = 4
LIMITE_REPETICIONES = 3

# Configuración de IA
PROBABILIDAD_RESPUESTA = 0.02
MIN_SECONDS_BETWEEN_RESPONSES_CHANNEL = 45
MIN_SECONDS_BETWEEN_RESPONSES_USUARIO = 20

# Respuestas personalizadas para spam de menciones
RESPUESTAS_SPAM = {
    708005339282276392: "¡Deja de mencionar a tu padre todo poderoso!!!",
    751481025544061111: "El admin debe dormir, no estorbes"
}

# Respuesta genérica para menciones excesivas
RESPUESTA_GENERICA_MENCIONES = "oiga hijueputa de {mention}, deja de joder a {target}! Ya van {count} veces, haga algo con su vida."

# Diccionario de respuestas para comandos
RESPUESTAS = {
    'general': {
        'usuario': [
            '`$help personas` - Muestra un mensaje para algunos usuarios especificos',
            '`$testspam` - Envía un mensaje de prueba al canal de spam',
            '`$statusspam` - Ver estado del sistema de spam',
            '`$meme` - Envía un meme random de subreddits en español',
        ],
        'admin': [
            '`$borrar <cantidad>` - Borra mensajes del canal (1-100)',
            '`$activarspam` - Activa el spam automático',
            '`$desactivarspam` - Desactiva el spam automático',
            '`$permisos` - Ver permisos del bot en el servidor y canal',
            '',
            '**COMANDOS POR IA (etiqueta @chimbot):**',
            '`@chimbot borra X mensajes` - Borra X mensajes (requiere admin)',
            '`@chimbot activa/activa el spam` - Activa spam automático',
            '`@chimbot desactiva/detén el spam` - Desactiva spam automático',
            '`@chimbot status del spam` - Ver estado del spam',
            '`@chimbot envía un mensaje de prueba` - Test del spam',
        ]
    },
    'personas': {
        'dios': 'DiosGodCoperPedraza lo mejor del mundo, alabado seas',
        'oscar': 'pendiente por poner',
        'reno': 'me encanta la verga bien peluda y grande en mi culo',
        'motta': 'pendiente por poner',
        'diego': 'diego = dIEGo = d IEG o = o GEI d = GEI = Diego es igual a un jodido maricon',
        'cardenas': 'Por detras me difaman por delante me la maman',
        'johan': 'me encanta que me den por el culo asi asi bien rico bien asi'
    }
}