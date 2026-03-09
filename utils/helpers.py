"""
Funciones auxiliares y helpers
"""
import random
import requests
from config import USUARIOS_PERSONALIDADES


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


async def obtener_meme_shitpost():
    """Obtiene un meme random de subreddits en español"""
    subreddits = ['MAAU', 'DylanteroYT', 'orslokx', 'yo_elvr']
    subreddit = random.choice(subreddits)
    
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
        headers = {'User-Agent': 'ChimBot/1.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Filtrar solo posts con imágenes
        memes = []
        for post in data['data']['children']:
            post_data = post['data']
            if post_data.get('url') and any(ext in post_data['url'] for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                memes.append({
                    'url': post_data['url'],
                    'title': post_data['title']
                })
        
        if memes:
            meme = random.choice(memes)
            return meme['url'], meme['title']
        return None, None
    
    except Exception as e:
        print(f"[ERROR MEME] {e}")
        return None, None