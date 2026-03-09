"""
Funciones auxiliares y helpers
"""
import random
import requests
import json
import os
from datetime import datetime, timedelta
from config import USUARIOS_PERSONALIDADES

# Archivo para guardar memes ya enviados
MEMES_CACHE_FILE = "memes_cache.json"


def obtener_info_usuario(user_id):
    """Retorna información personalizada del usuario si existe"""
    if user_id in USUARIOS_PERSONALIDADES:
        info = USUARIOS_PERSONALIDADES[user_id]
        return f"Usuario: {info['nombre']} (apodos: {', '.join(info['apodos'])}). Características: {', '.join(info['caracteristicas'])}"
    return None


async def obtener_roles_usuario(member):
    """Obtiene los roles relevantes del usuario"""
    if not member:
        return []

    roles_relevantes = []
    for rol in member.roles:
        if rol.name.lower() in ['veneco']:
            roles_relevantes.append(rol.name)
    return roles_relevantes


def cargar_cache_memes():
    """Carga el caché de memes desde el archivo"""
    if not os.path.exists(MEMES_CACHE_FILE):
        return []
    
    try:
        with open(MEMES_CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        # Limpiar memes de más de 3 días
        ahora = datetime.now()
        cache_filtrado = [
            meme for meme in cache
            if (ahora - datetime.fromisoformat(meme['fecha'])).days < 3
        ]
        
        # Guardar caché filtrado
        if len(cache_filtrado) != len(cache):
            guardar_cache_memes(cache_filtrado)
        
        return cache_filtrado
    except Exception as e:
        print(f"[ERROR] Al cargar caché de memes: {e}")
        return []


def guardar_cache_memes(cache):
    """Guarda el caché de memes en el archivo"""
    try:
        with open(MEMES_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Al guardar caché de memes: {e}")


def agregar_meme_al_cache(url):
    """Agrega un meme al caché con la fecha actual"""
    cache = cargar_cache_memes()
    cache.append({
        'url': url,
        'fecha': datetime.now().isoformat()
    })
    guardar_cache_memes(cache)


async def obtener_meme_shitpost():
    """Obtiene un meme random de subreddits en español (imágenes y videos)"""
    subreddits = ['MAAU', 'DylanteroYT', 'orslokx', 'yo_elvr', 'bananirou']
    subreddit = random.choice(subreddits)
    
    # Cargar caché de memes ya enviados
    cache = cargar_cache_memes()
    urls_enviadas = {meme['url'] for meme in cache}
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=100"
            headers = {'User-Agent': 'ChimBot/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            memes = []
            for post in data['data']['children']:
                post_data = post['data']
                post_url = post_data.get('url', '')
                
                # Verificar si es imagen
                if any(ext in post_url for ext in ['.jpg', '.png', '.gif', '.jpeg', '.webp']):
                    if post_url not in urls_enviadas:
                        memes.append({
                            'url': post_url,
                            'title': post_data['title'],
                            'type': 'image'
                        })
                
                # Verificar si es video de Reddit (is_video = true)
                elif post_data.get('is_video'):
                    media = post_data.get('media', {})
                    reddit_video = media.get('reddit_video', {})
                    
                    # Obtener URL del video con mejor calidad
                    video_url = reddit_video.get('fallback_url')
                    
                    if video_url and video_url not in urls_enviadas:
                        # Limpiar parámetros de la URL para mejor compatibilidad
                        video_url = video_url.split('?')[0]
                        
                        memes.append({
                            'url': video_url,
                            'title': post_data['title'],
                            'type': 'reddit_video',
                            'has_audio': reddit_video.get('has_audio', False)
                        })
                
                # Verificar si es gif/gifv de imgur
                elif 'imgur.com' in post_url and ('.gifv' in post_url or '.mp4' in post_url):
                    # Convertir gifv a mp4
                    if '.gifv' in post_url:
                        post_url = post_url.replace('.gifv', '.mp4')
                    
                    if post_url not in urls_enviadas:
                        memes.append({
                            'url': post_url,
                            'title': post_data['title'],
                            'type': 'video'
                        })
                
                # Verificar gfycat y redgifs
                elif any(domain in post_url for domain in ['gfycat.com', 'redgifs.com']):
                    if post_url not in urls_enviadas:
                        memes.append({
                            'url': post_url,
                            'title': post_data['title'],
                            'type': 'external_video'
                        })
            
            if memes:
                meme = random.choice(memes)
                agregar_meme_al_cache(meme['url'])
                return meme['url'], meme['title'], meme.get('type', 'image')
            
            # Si no hay memes nuevos, intentar con otro subreddit
            intentos += 1
            if intentos < max_intentos:
                subreddits_restantes = [s for s in ['MAAU', 'DylanteroYT', 'orslokx', 'yo_elvr'] if s != subreddit]
                subreddit = random.choice(subreddits_restantes)
        
        except Exception as e:
            print(f"[ERROR MEME] En r/{subreddit}: {e}")
            intentos += 1
            if intentos < max_intentos:
                subreddits_restantes = [s for s in ['MAAU', 'DylanteroYT', 'orslokx', 'yo_elvr'] if s != subreddit]
                subreddit = random.choice(subreddits_restantes)
    
    return None, None, None

# Archivo para guardar copypastas ya enviados
COPYPASTAS_CACHE_FILE = "copypastas_cache.json"

def cargar_cache_copypastas():
    """Carga el caché de copypastas desde el archivo"""
    if not os.path.exists(COPYPASTAS_CACHE_FILE):
        return []
    
    try:
        with open(COPYPASTAS_CACHE_FILE, 'r') as f:
            cache = json.load(f)
        
        # Validar que cada entrada tenga los campos necesarios
        cache_valido = []
        ahora = datetime.now()
        
        for cp in cache:
            # Verificar que tenga los campos necesarios
            if not isinstance(cp, dict) or 'id' not in cp or 'fecha' not in cp:
                print(f"[WARNING] Entrada inválida en caché de copypastas: {cp}")
                continue
            
            # Filtrar copypastas de más de 3 días
            try:
                if (ahora - datetime.fromisoformat(cp['fecha'])).days < 3:
                    cache_valido.append(cp)
            except Exception as e:
                print(f"[WARNING] Error procesando fecha en caché: {e}")
                continue
        
        # Guardar caché filtrado si hubo cambios
        if len(cache_valido) != len(cache):
            guardar_cache_copypastas(cache_valido)
        
        return cache_valido
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Archivo de caché de copypastas corrupto: {e}")
        # Eliminar archivo corrupto y empezar de nuevo
        try:
            os.remove(COPYPASTAS_CACHE_FILE)
            print(f"[INFO] Caché de copypastas eliminado, se creará uno nuevo")
        except:
            pass
        return []
    except Exception as e:
        print(f"[ERROR] Al cargar caché de copypastas: {e}")
        return []
    
def guardar_cache_copypastas(cache):
    """Guarda el caché de copypastas en el archivo"""
    try:
        with open(COPYPASTAS_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Al guardar caché de copypastas: {e}")

def agregar_copypasta_al_cache(post_id):
    """Agrega un copypasta al caché con la fecha actual"""
    if not post_id:
        print("[WARNING] Intentando agregar copypasta sin ID al caché")
        return
    
    cache = cargar_cache_copypastas()
    cache.append({
        'id': post_id,
        'fecha': datetime.now().isoformat()
    })
    guardar_cache_copypastas(cache)

async def obtener_copypasta():
    """Obtiene un copypasta random de r/copypasta_es"""
    try:
        # Cargar caché de copypastas ya enviados
        cache = cargar_cache_copypastas()
        ids_enviados = {cp.get('id') for cp in cache if cp.get('id')}
        
        url = "https://www.reddit.com/r/copypasta_es/hot.json?limit=100"
        headers = {'User-Agent': 'ChimBot/1.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Filtrar posts de texto (copypastas)
        copypastas = []
        for post in data['data']['children']:
            post_data = post['data']
            
            # Validar que tenga los campos necesarios
            if not all(key in post_data for key in ['id', 'selftext', 'title', 'permalink']):
                continue
            
            post_id = post_data['id']
            
            # Solo posts de texto (selftext no vacío)
            selftext = post_data.get('selftext', '').strip()
            if selftext and post_id not in ids_enviados:
                # Filtrar copypastas muy cortos (menos de 100 caracteres)
                if len(selftext) >= 100:
                    copypastas.append({
                        'id': post_id,
                        'title': post_data['title'],
                        'text': selftext,
                        'url': f"https://reddit.com{post_data['permalink']}"
                    })
        
        if copypastas:
            copypasta = random.choice(copypastas)
            # Agregar al caché
            agregar_copypasta_al_cache(copypasta['id'])
            return copypasta['title'], copypasta['text'], copypasta['url']
        
        # Si no hay copypastas nuevos, devolver None
        print("[INFO] No se encontraron copypastas nuevos")
        return None, None, None
    
    except Exception as e:
        print(f"[ERROR COPYPASTA] {e}")
        import traceback
        traceback.print_exc()
        return None, None, None