"""
Authentication and user management
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

USERS_FILE = 'data/users.json'


def init_users_system():
    """Initialize users file with admin user if it doesn't exist"""
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        
        # Create default admin user
        users = {
            'users': [
                {
                    'user_id': 'admin',
                    'username': 'admin',
                    'password_hash': _hash_password('admin123'),
                    'email': 'admin@copiloto.local',
                    'role': 'admin',
                    'company_name': 'Administrador',
                    'created_at': datetime.now().isoformat(),
                    'active': True
                }
            ]
        }
        
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        logger.info("Users system initialized with admin user")


def _hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> Dict:
    """Load users from JSON"""
    if not os.path.exists(USERS_FILE):
        init_users_system()
    
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_users(users_data: Dict):
    """Save users to JSON"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2, ensure_ascii=False)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate user by username and password
    Returns user dict without password if successful, None otherwise
    """
    users_data = _load_users()
    password_hash = _hash_password(password)
    
    for user in users_data['users']:
        if user['username'] == username and user['password_hash'] == password_hash:
            if not user.get('active', True):
                logger.warning(f"Inactive user login attempt: {username}")
                return None
            
            # Return user without password
            user_copy = user.copy()
            user_copy.pop('password_hash', None)
            logger.info(f"User authenticated: {username}")
            return user_copy
    
    logger.warning(f"Failed login attempt for username: {username}")
    return None


def create_user(username: str, password: str, email: str, company_name: str, 
                role: str = 'client') -> tuple[bool, str]:
    """
    Create new user
    Returns: (success, message)
    """
    users_data = _load_users()
    
    # Check if username exists
    if any(u['username'] == username for u in users_data['users']):
        return False, "El nombre de usuario ya existe"
    
    # Check if email exists
    if any(u['email'] == email for u in users_data['users']):
        return False, "El email ya está registrado"
    
    # Generate user_id
    user_id = username.lower().replace(' ', '_')
    
    # Create user
    new_user = {
        'user_id': user_id,
        'username': username,
        'password_hash': _hash_password(password),
        'email': email,
        'role': role,
        'company_name': company_name,
        'created_at': datetime.now().isoformat(),
        'active': True
    }
    
    users_data['users'].append(new_user)
    _save_users(users_data)
    
    # Create user's history directory
    user_history_dir = f'data/history/{user_id}'
    os.makedirs(user_history_dir, exist_ok=True)
    
    logger.info(f"User created: {username} ({user_id})")
    return True, "Usuario creado exitosamente"


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by user_id"""
    users_data = _load_users()
    
    for user in users_data['users']:
        if user['user_id'] == user_id:
            user_copy = user.copy()
            user_copy.pop('password_hash', None)
            return user_copy
    
    return None


def list_all_users() -> List[Dict]:
    """List all users (admin only)"""
    users_data = _load_users()
    
    users_list = []
    for user in users_data['users']:
        user_copy = user.copy()
        user_copy.pop('password_hash', None)
        users_list.append(user_copy)
    
    return users_list


def update_user_status(user_id: str, active: bool) -> tuple[bool, str]:
    """Activate or deactivate user"""
    users_data = _load_users()
    
    for user in users_data['users']:
        if user['user_id'] == user_id:
            if user['role'] == 'admin':
                return False, "No se puede desactivar al administrador"
            
            user['active'] = active
            _save_users(users_data)
            
            status = "activado" if active else "desactivado"
            logger.info(f"User {user_id} {status}")
            return True, f"Usuario {status} correctamente"
    
    return False, "Usuario no encontrado"


def delete_user(user_id: str) -> tuple[bool, str]:
    """Delete user (admin only)"""
    users_data = _load_users()
    
    for i, user in enumerate(users_data['users']):
        if user['user_id'] == user_id:
            if user['role'] == 'admin':
                return False, "No se puede eliminar al administrador"
            
            users_data['users'].pop(i)
            _save_users(users_data)
            
            logger.info(f"User deleted: {user_id}")
            return True, "Usuario eliminado correctamente"
    
    return False, "Usuario no encontrado"


def change_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change user password"""
    users_data = _load_users()
    old_hash = _hash_password(old_password)
    
    for user in users_data['users']:
        if user['user_id'] == user_id:
            if user['password_hash'] != old_hash:
                return False, "Contraseña actual incorrecta"
            
            user['password_hash'] = _hash_password(new_password)
            _save_users(users_data)
            
            logger.info(f"Password changed for user: {user_id}")
            return True, "Contraseña cambiada correctamente"
    
    return False, "Usuario no encontrado"
