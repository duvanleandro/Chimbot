// dashboard.js - Sistema completo del dashboard

// ========================================
// VARIABLES GLOBALES
// ========================================
let currentServerId = null;
let currentServerData = null;
let currentChannelId = null;
let currentConfig = null;
let selectedUsers = [];
let allServerUsers = [];

// ========================================
// INICIALIZACIÓN
// ========================================
window.onload = () => {
    loadServers();
    loadStats();
};

// ========================================
// NAVEGACIÓN DE PÁGINAS
// ========================================
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    
    document.getElementById(`page-${pageName}`).classList.add('active');
    event.target.closest('.nav-item').classList.add('active');
    
    if (pageName === 'servers') {
        loadServers();
    } else if (pageName === 'stats') {
        loadStats();
    }
}

function showDashboardTab(tabName) {
    document.querySelectorAll('.tab-btn-internal').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    document.querySelectorAll('.dashboard-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`dashboard-${tabName}`).classList.add('active');
    
    if (tabName === 'spam') {
        loadSpamConfig();
    } else if (tabName === 'messages') {
        loadChannels();
        loadFavoriteUsers();
    } else if (tabName === 'ia') {
        loadIAConfig();
    }
}

// ========================================
// SERVIDORES
// ========================================
function loadServers() {
    fetch('/api/servidores')
        .then(response => response.json())
        .then(servers => {
            const grid = document.getElementById('servers-grid');
            
            if (servers.length === 0) {
                grid.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No hay servidores disponibles</p>';
                return;
            }

            grid.innerHTML = servers.map(server => `
                <div class="server-card" onclick="enterServer('${server.id}', '${server.nombre}', '${server.icono || ''}', ${server.miembros})">
                    <div class="server-icon">
                        ${server.icono ? `<img src="${server.icono}" alt="${server.nombre}">` : '🏠'}
                    </div>
                    <div class="server-info">
                        <div class="server-name">${server.nombre}</div>
                        <div class="server-members">👥 ${server.miembros} miembros</div>
                    </div>
                    <button class="btn-enter">Entrar</button>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error:', error));
}

function enterServer(serverId, serverName, serverIcon, serverMembers) {
    currentServerId = serverId;
    currentServerData = { id: serverId, name: serverName, icon: serverIcon, members: serverMembers };

    const headerIcon = document.getElementById('server-header-icon');
    if (serverIcon) {
        headerIcon.innerHTML = `<img src="${serverIcon}" alt="${serverName}">`;
    } else {
        headerIcon.innerHTML = '🏠';
    }

    document.getElementById('server-header-name').textContent = serverName;
    document.getElementById('server-header-members').textContent = `${serverMembers} miembros`;

    document.getElementById('page-servers').classList.remove('active');
    document.getElementById('page-server-dashboard').classList.add('active');

    loadSpamConfig();
    loadServerUsers();
}

function backToServers() {
    currentServerId = null;
    currentServerData = null;
    selectedUsers = [];

    document.getElementById('page-server-dashboard').classList.remove('active');
    document.getElementById('page-servers').classList.add('active');
}

// ========================================
// CONFIGURACIÓN DE SPAM
// ========================================
function loadSpamConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            currentConfig = config;
            
            // Estado
            updateSpamStatus(config.spam.activo);
            
            // Frecuencia
            document.getElementById('spam-frecuencia').value = config.spam.frecuencia_horas;
            
            // Modo
            document.querySelector(`input[name="spam-mode"][value="${config.spam.usar_ia ? 'ia' : 'static'}"]`).checked = true;
            updateSpamMode();
            
            // Mensajes
            renderMessagesList(config.spam.mensajes);
        })
        .catch(error => console.error('Error:', error));
}

function updateSpamStatus(activo) {
    const badge = document.getElementById('spam-status-badge');
    const btn = document.getElementById('btn-toggle-spam');
    
    if (activo) {
        badge.textContent = '🟢 Activo';
        badge.className = 'badge badge-active';
        btn.textContent = 'Desactivar Spam';
        btn.className = 'btn-primary';
    } else {
        badge.textContent = '⚫ Inactivo';
        badge.className = 'badge badge-inactive';
        btn.textContent = 'Activar Spam';
        btn.className = 'btn-primary';
    }
}

function renderMessagesList(mensajes) {
    const container = document.getElementById('messages-list');
    
    if (mensajes.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No hay mensajes configurados</p>';
        return;
    }
    
    container.innerHTML = mensajes.map((msg, index) => `
        <div class="message-item" data-index="${index}">
            <div class="message-item-content">
                <input 
                    type="text" 
                    class="message-item-input" 
                    value="${msg.texto}" 
                    placeholder="Escribe el mensaje..."
                    data-index="${index}"
                >
                <div class="message-item-repetitions">
                    <label>Repetir:</label>
                    <input 
                        type="number" 
                        min="1" 
                        max="10" 
                        value="${msg.repeticiones}"
                        data-index="${index}"
                    >
                    <span>veces</span>
                </div>
            </div>
            <div class="message-item-actions">
                <button class="btn-remove-message" onclick="removeMessage(${index})">🗑️</button>
            </div>
        </div>
    `).join('');
}

function updateSpamMode() {
    const mode = document.querySelector('input[name="spam-mode"]:checked').value;
    const staticSection = document.getElementById('static-messages-section');
    
    if (mode === 'static') {
        staticSection.style.display = 'block';
    } else {
        staticSection.style.display = 'none';
    }
}

function addMessage() {
    if (!currentConfig) return;
    
    currentConfig.spam.mensajes.push({ texto: "", repeticiones: 1 });
    renderMessagesList(currentConfig.spam.mensajes);
}

function removeMessage(index) {
    if (!currentConfig) return;
    
    currentConfig.spam.mensajes.splice(index, 1);
    renderMessagesList(currentConfig.spam.mensajes);
}

function toggleSpam() {
    fetch('/api/spam/toggle', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSpamStatus(data.activo);
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
}

function testSpam() {
    alert('Función de prueba aún no implementada. El mensaje se enviará según la configuración actual.');
}

function saveSpamConfig() {
    // Recolectar datos del formulario
    const frecuencia = parseInt(document.getElementById('spam-frecuencia').value);
    const usarIA = document.querySelector('input[name="spam-mode"]:checked').value === 'ia';
    
    const mensajes = [];
    document.querySelectorAll('.message-item').forEach(item => {
        const index = item.dataset.index;
        const texto = item.querySelector('.message-item-input').value;
        const repeticiones = parseInt(item.querySelector('input[type="number"]').value);
        
        if (texto.trim()) {
            mensajes.push({ texto, repeticiones });
        }
    });
    
    currentConfig.spam.frecuencia_horas = frecuencia;
    currentConfig.spam.usar_ia = usarIA;
    currentConfig.spam.mensajes = mensajes;
    
    // Guardar configuración
    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentConfig)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('✅ Configuración guardada correctamente');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ Error al guardar la configuración');
        });
}

// ========================================
// CONFIGURACIÓN DE IA
// ========================================
function loadIAConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            currentConfig = config;
            
            updateIAStatus(config.ia.respuestas_activas);
            
            const probability = Math.round(config.ia.probabilidad * 100);
            document.getElementById('ia-probability').value = probability;
            document.getElementById('ia-probability-value').textContent = probability;
        })
        .catch(error => console.error('Error:', error));
}

function updateIAStatus(activo) {
    const badge = document.getElementById('ia-status-badge');
    const btn = document.getElementById('btn-toggle-ia');
    
    if (activo) {
        badge.textContent = '🟢 Activo';
        badge.className = 'badge badge-active';
        btn.textContent = 'Desactivar IA';
    } else {
        badge.textContent = '⚫ Inactivo';
        badge.className = 'badge badge-inactive';
        btn.textContent = 'Activar IA';
    }
}

function updateIAProbability(value) {
    document.getElementById('ia-probability-value').textContent = value;
}

function toggleIA() {
    fetch('/api/ia/toggle', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateIAStatus(data.activo);
                currentConfig.ia.respuestas_activas = data.activo;
            }
        })
        .catch(error => console.error('Error:', error));
}

function saveIAConfig() {
    const probability = parseInt(document.getElementById('ia-probability').value) / 100;
    
    currentConfig.ia.probabilidad = probability;
    
    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentConfig)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('✅ Configuración de IA guardada');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ Error al guardar');
        });
}

// ========================================
// MENSAJES Y USUARIOS FAVORITOS
// ========================================
function loadChannels() {
    if (!currentServerId) return;

    fetch(`/api/canales/${currentServerId}`)
        .then(response => response.json())
        .then(channels => {
            const select = document.getElementById('channel-select');
            select.innerHTML = '<option value="">-- Selecciona un canal --</option>';
            
            channels.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.id;
                option.textContent = `# ${channel.nombre}`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error:', error));
}

function loadServerUsers() {
    if (!currentServerId) return;

    fetch(`/api/usuarios?servidor_id=${currentServerId}`)
        .then(response => response.json())
        .then(users => {
            allServerUsers = users;
        })
        .catch(error => console.error('Error:', error));
}

function loadFavoriteUsers() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            currentConfig = config;
            renderFavoriteUsers(config.usuarios_favoritos);
        })
        .catch(error => console.error('Error:', error));
}

function renderFavoriteUsers(usuarios) {
    const container = document.getElementById('favorite-users-list');
    
    if (usuarios.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No hay usuarios favoritos</p>';
        return;
    }
    
    container.innerHTML = usuarios.map(user => `
        <div class="favorite-user-item">
            <div class="favorite-user-info">
                <div class="favorite-user-avatar">👤</div>
                <div>
                    <div class="favorite-user-name">${user.nombre} ${user.apodo ? `(${user.apodo})` : ''}</div>
                    <div class="favorite-user-id">ID: ${user.id}</div>
                </div>
            </div>
            <button class="btn-select-user" onclick="selectUser('${user.id}', '${user.nombre}')">
                Seleccionar
            </button>
        </div>
    `).join('');
}

function selectUser(userId, userName) {
    if (!selectedUsers.find(u => u.id === userId)) {
        selectedUsers.push({ id: userId, name: userName });
        renderSelectedUsers();
    }
}

function renderSelectedUsers() {
    const container = document.getElementById('mention-users-container');
    
    if (selectedUsers.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No hay usuarios seleccionados</p>';
        return;
    }
    
    container.innerHTML = selectedUsers.map(user => `
        <span class="mention-tag">
            @${user.name}
            <button onclick="deselectUser('${user.id}')">×</button>
        </span>
    `).join('');
}

function deselectUser(userId) {
    selectedUsers = selectedUsers.filter(u => u.id !== userId);
    renderSelectedUsers();
}

function showAddFavoriteModal() {
    document.getElementById('add-favorite-modal').classList.add('active');
}

function closeAddFavoriteModal() {
    document.getElementById('add-favorite-modal').classList.remove('active');
}

function searchUsers() {
    const query = document.getElementById('search-user-input').value.toLowerCase();
    const results = allServerUsers.filter(u => 
        u.nombre.toLowerCase().includes(query) || u.display_name.toLowerCase().includes(query)
    );
    
    const container = document.getElementById('search-results');
    
    if (results.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No se encontraron usuarios</p>';
        return;
    }
    
    container.innerHTML = results.slice(0, 10).map(user => `
        <div class="search-result-item" onclick="addFavoriteUser('${user.id}', '${user.nombre}')">
            <div>
                <strong>${user.display_name}</strong>
                <div style="font-size: 13px; color: var(--text-secondary);">${user.nombre}</div>
            </div>
        </div>
    `).join('');
}

function addFavoriteUser(userId, userName) {
    if (!currentConfig) return;
    
    const apodo = prompt('Apodo para este usuario (opcional):');
    
    currentConfig.usuarios_favoritos.push({
        id: userId,
        nombre: userName,
        apodo: apodo || ""
    });
    
    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentConfig)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeAddFavoriteModal();
                loadFavoriteUsers();
                alert('✅ Usuario agregado a favoritos');
            }
        })
        .catch(error => console.error('Error:', error));
}

function loadMessages() {
    const channelId = document.getElementById('channel-select').value;
    if (!channelId) return;

    currentChannelId = channelId;

    fetch(`/api/mensajes/${channelId}`)
        .then(response => response.json())
        .then(messages => {
            const container = document.getElementById('messages-container');
            
            if (messages.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No hay mensajes</p>';
                return;
            }

            container.innerHTML = messages.map(msg => `
                <div class="message">
                    <img src="${msg.autor_avatar || 'https://cdn.discordapp.com/embed/avatars/0.png'}" 
                         alt="Avatar" class="message-avatar">
                    <div class="message-content">
                        <div class="message-author">${msg.autor}</div>
                        <div class="message-text">${msg.contenido || '<i>(sin contenido)</i>'}</div>
                        <div class="message-time">${new Date(msg.timestamp).toLocaleString()}</div>
                    </div>
                </div>
            `).join('');

            container.scrollTop = container.scrollHeight;
        })
        .catch(error => console.error('Error:', error));
}

function sendMessageAdvanced() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();

    if (!text) {
        alert('Escribe un mensaje');
        return;
    }

    if (!currentChannelId) {
        alert('Selecciona un canal');
        return;
    }

    const userIds = selectedUsers.map(u => u.id);

    fetch('/api/mensaje/avanzado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            canal_id: currentChannelId,
            mensaje: text,
            usuarios: userIds
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                input.value = '';
                selectedUsers = [];
                renderSelectedUsers();
                loadMessages();
            } else {
                alert('Error al enviar mensaje');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al enviar mensaje');
        });
}

// ========================================
// ESTADÍSTICAS
// ========================================
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            const container = document.getElementById('stats-container');
            container.innerHTML = `
                <div class="stat-card">
                    <div class="stat-icon">🏠</div>
                    <div class="stat-value">${stats.servidores}</div>
                    <div class="stat-label">Servidores</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">💬</div>
                    <div class="stat-value">${stats.canales}</div>
                    <div class="stat-label">Canales</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">👥</div>
                    <div class="stat-value">${stats.usuarios}</div>
                    <div class="stat-label">Usuarios</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⚡</div>
                    <div class="stat-value">${stats.latencia}ms</div>
                    <div class="stat-label">Latencia</div>
                </div>
            `;
        })
        .catch(error => console.error('Error:', error));
}