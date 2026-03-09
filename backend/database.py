"""Configuração do banco de dados SQLite para perfis de usuário.

Gerencia criação de tabelas e operações CRUD para perfis de usuário.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import contextmanager

DATABASE_PATH = "profiles.db"

def init_database():
    """Inicializa o banco de dados criando as tabelas se não existirem."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Tabela de perfis de usuário
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                weight REAL,
                height REAL,
                sex TEXT,
                activity_level TEXT,
                goals TEXT,
                dietary_restrictions TEXT,
                medical_conditions TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Tabela de entradas do diário alimentar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_entries (
                id TEXT PRIMARY KEY,
                user_profile_id TEXT,
                date TEXT,
                meal_type TEXT,
                food_name TEXT,
                calories REAL,
                proteins REAL,
                carbs REAL,
                fats REAL,
                portion_size TEXT,
                description TEXT,
                entry_method TEXT,
                created_at TEXT,
                FOREIGN KEY (user_profile_id) REFERENCES user_profiles (id)
            )
        """)

        # Tabela de medições de progresso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress_measurements (
                id TEXT PRIMARY KEY,
                user_profile_id TEXT,
                date TEXT,
                weight REAL,
                body_fat_percentage REAL,
                muscle_mass REAL,
                waist_circumference REAL,
                chest_circumference REAL,
                hip_circumference REAL,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (user_profile_id) REFERENCES user_profiles (id)
            )
        """)

        conn.commit()

@contextmanager
def get_db_connection():
    """Context manager para conexões com o banco de dados."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def create_profile(profile_data: Dict) -> str:
    """Cria um novo perfil de usuário.

    Args:
        profile_data: Dicionário com dados do perfil

    Returns:
        ID do perfil criado
    """
    profile_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profiles (
                id, name, age, weight, height, sex, activity_level,
                goals, dietary_restrictions, medical_conditions,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id,
            profile_data.get('name'),
            profile_data.get('age'),
            profile_data.get('weight'),
            profile_data.get('height'),
            profile_data.get('sex'),
            profile_data.get('activity_level'),
            json.dumps(profile_data.get('goals', [])),
            json.dumps(profile_data.get('dietary_restrictions', [])),
            json.dumps(profile_data.get('medical_conditions', [])),
            current_time,
            current_time
        ))
        conn.commit()

    return profile_id

def get_profile(profile_id: str) -> Optional[Dict]:
    """Busca um perfil pelo ID.

    Args:
        profile_id: ID do perfil

    Returns:
        Dicionário com dados do perfil ou None se não encontrado
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (profile_id,))
        row = cursor.fetchone()

        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'age': row['age'],
                'weight': row['weight'],
                'height': row['height'],
                'sex': row['sex'],
                'activity_level': row['activity_level'],
                'goals': json.loads(row['goals']) if row['goals'] else [],
                'dietary_restrictions': json.loads(row['dietary_restrictions']) if row['dietary_restrictions'] else [],
                'medical_conditions': json.loads(row['medical_conditions']) if row['medical_conditions'] else [],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None

def update_profile(profile_id: str, profile_data: Dict) -> bool:
    """Atualiza um perfil existente.

    Args:
        profile_id: ID do perfil
        profile_data: Dados atualizados

    Returns:
        True se atualizado com sucesso, False se perfil não encontrado
    """
    current_time = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user_profiles SET
                name = ?, age = ?, weight = ?, height = ?, sex = ?,
                activity_level = ?, goals = ?, dietary_restrictions = ?,
                medical_conditions = ?, updated_at = ?
            WHERE id = ?
        """, (
            profile_data.get('name'),
            profile_data.get('age'),
            profile_data.get('weight'),
            profile_data.get('height'),
            profile_data.get('sex'),
            profile_data.get('activity_level'),
            json.dumps(profile_data.get('goals', [])),
            json.dumps(profile_data.get('dietary_restrictions', [])),
            json.dumps(profile_data.get('medical_conditions', [])),
            current_time,
            profile_id
        ))

        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False

def list_profiles() -> List[Dict]:
    """Lista todos os perfis (apenas dados básicos).

    Returns:
        Lista de perfis com dados resumidos
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, created_at FROM user_profiles ORDER BY created_at DESC")
        rows = cursor.fetchall()

        return [
            {
                'id': row['id'],
                'name': row['name'],
                'age': row['age'],
                'created_at': row['created_at']
            }
            for row in rows
        ]

def delete_profile(profile_id: str) -> bool:
    """Remove um perfil.

    Args:
        profile_id: ID do perfil

    Returns:
        True se removido com sucesso, False se perfil não encontrado
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_profiles WHERE id = ?", (profile_id,))

        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False

# ============================================================================
# FUNÇÕES DO DIÁRIO ALIMENTAR
# ============================================================================

def add_food_entry(entry_data: Dict) -> str:
    """Adiciona uma entrada de alimento no diário.

    Args:
        entry_data: Dicionário com dados da entrada

    Returns:
        ID da entrada criada
    """
    entry_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO food_entries (
                id, user_profile_id, date, meal_type, food_name,
                calories, proteins, carbs, fats, portion_size,
                description, entry_method, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id,
            entry_data.get('user_profile_id'),
            entry_data.get('date'),
            entry_data.get('meal_type'),
            entry_data.get('food_name'),
            entry_data.get('calories'),
            entry_data.get('proteins'),
            entry_data.get('carbs'),
            entry_data.get('fats'),
            entry_data.get('portion_size'),
            entry_data.get('description'),
            entry_data.get('entry_method'),
            current_time
        ))
        conn.commit()

    return entry_id

def get_daily_food_entries(user_profile_id: str, date: str) -> List[Dict]:
    """Busca todas as entradas de alimento de um dia específico.

    Args:
        user_profile_id: ID do perfil do usuário
        date: Data no formato YYYY-MM-DD

    Returns:
        Lista de entradas do dia
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM food_entries
            WHERE user_profile_id = ? AND date = ?
            ORDER BY created_at ASC
        """, (user_profile_id, date))
        rows = cursor.fetchall()

        return [
            {
                'id': row['id'],
                'user_profile_id': row['user_profile_id'],
                'date': row['date'],
                'meal_type': row['meal_type'],
                'food_name': row['food_name'],
                'calories': row['calories'],
                'proteins': row['proteins'],
                'carbs': row['carbs'],
                'fats': row['fats'],
                'portion_size': row['portion_size'],
                'description': row['description'],
                'entry_method': row['entry_method'],
                'created_at': row['created_at']
            }
            for row in rows
        ]

def get_daily_summary(user_profile_id: str, date: str) -> Dict:
    """Calcula o resumo nutricional do dia.

    Args:
        user_profile_id: ID do perfil do usuário
        date: Data no formato YYYY-MM-DD

    Returns:
        Resumo com totais de calorias e macros
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(proteins), 0) as total_proteins,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fats), 0) as total_fats,
                COUNT(*) as total_entries
            FROM food_entries
            WHERE user_profile_id = ? AND date = ?
        """, (user_profile_id, date))
        row = cursor.fetchone()

        return {
            'date': date,
            'total_calories': row['total_calories'],
            'total_proteins': row['total_proteins'],
            'total_carbs': row['total_carbs'],
            'total_fats': row['total_fats'],
            'total_entries': row['total_entries']
        }

def calculate_caloric_goal(profile: Dict) -> int:
    """Calcula a meta calórica diária baseada no perfil do usuário.

    Args:
        profile: Dados do perfil do usuário

    Returns:
        Meta calórica em kcal
    """
    # Fórmula de Mifflin-St Jeor para TMB (Taxa Metabólica Basal)
    if profile['sex'] == 'masculino':
        tmb = 88.362 + (13.397 * profile['weight']) + (4.799 * profile['height']) - (5.677 * profile['age'])
    else:
        tmb = 447.593 + (9.247 * profile['weight']) + (3.098 * profile['height']) - (4.330 * profile['age'])

    # Fatores de atividade
    activity_factors = {
        'sedentario': 1.2,
        'leve': 1.375,
        'moderado': 1.55,
        'ativo': 1.725,
        'muito_ativo': 1.9
    }

    activity_factor = activity_factors.get(profile['activity_level'], 1.55)
    tdee = tmb * activity_factor  # TDEE = Total Daily Energy Expenditure

    # Ajuste baseado nos objetivos
    goals = profile.get('goals', [])
    if 'emagrecimento' in [g.lower() for g in goals] or 'emagrecer' in [g.lower() for g in goals]:
        # Déficit de 500 kcal para perder ~0.5kg por semana
        return int(tdee - 500)
    elif 'ganho de peso' in [g.lower() for g in goals] or 'ganhar peso' in [g.lower() for g in goals]:
        # Superávit de 300 kcal para ganhar peso
        return int(tdee + 300)
    elif 'ganho de massa muscular' in [g.lower() for g in goals] or 'ganhar massa' in [g.lower() for g in goals]:
        # Superávit de 200 kcal para ganho de massa magra
        return int(tdee + 200)
    else:
        # Manutenção
        return int(tdee)

def delete_food_entry(entry_id: str, user_profile_id: str) -> bool:
    """Remove uma entrada de alimento.

    Args:
        entry_id: ID da entrada
        user_profile_id: ID do perfil (para segurança)

    Returns:
        True se removido com sucesso
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM food_entries
            WHERE id = ? AND user_profile_id = ?
        """, (entry_id, user_profile_id))

        if cursor.rowcount > 0:
            conn.commit()
            return True
        return False

# Inicializa o banco na importação do módulo
init_database()