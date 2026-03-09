"""
Rutas de vistas HTML del dashboard
"""
from flask import render_template


def register_view_routes(app):
    """Registra todas las rutas de vistas HTML"""
    
    @app.route('/')
    def index():
        """Página principal - muestra que el bot está activo"""
        return "ChimBot está activo! 🤖"

    @app.route('/dashboard')
    def dashboard():
        """Dashboard de control del bot"""
        return render_template('dashboard.html')
    
    print("✅ Rutas de vistas registradas")