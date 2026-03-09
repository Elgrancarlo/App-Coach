"""API endpoints para dashboard personalizado.

Contém endpoint que agrega dados do perfil, resumo nutricional e insights do usuário.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import (
    list_profiles, get_profile, get_daily_summary, calculate_caloric_goal
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

class DashboardResponse(BaseModel):
    """Schema para resposta completa do dashboard."""
    # Dados do usuário
    user_name: str
    user_age: int
    user_weight: float
    user_goals: str
    has_profile: bool

    # Dados nutricionais
    caloric_goal: int
    calories_consumed: float
    calories_remaining: float
    progress_percentage: float

    # Macronutrientes
    total_proteins: float
    total_carbs: float
    total_fats: float

    # Status e contadores
    entries_today: int
    diary_updated_today: bool
    current_date: str

    # Insights e motivação
    progress_status: str  # "on_track", "ahead", "behind", "exceeded"
    ai_motivation: str
    quick_tip: str

@router.get("/overview", response_model=DashboardResponse)
async def get_dashboard_overview():
    """Retorna visão geral completa do dashboard do usuário."""
    try:
        # Busca perfil do usuário
        profiles = list_profiles()
        current_date = datetime.now().date().isoformat()

        if not profiles:
            # Usuário sem perfil - retorna dados padrão
            return DashboardResponse(
                user_name="Usuário",
                user_age=0,
                user_weight=0,
                user_goals="Não definidos",
                has_profile=False,
                caloric_goal=0,
                calories_consumed=0,
                calories_remaining=0,
                progress_percentage=0,
                total_proteins=0,
                total_carbs=0,
                total_fats=0,
                entries_today=0,
                diary_updated_today=False,
                current_date=current_date,
                progress_status="no_profile",
                ai_motivation="Configure seu perfil na aba 'Definir Objetivos' para começar sua jornada personalizada! 🎯",
                quick_tip="Um perfil completo permite recomendações precisas de nutrição e treinos."
            )

        # Pega o primeiro perfil (usuário atual)
        profile = profiles[0]
        user_profile_id = profile['id']

        # Busca perfil completo
        full_profile = get_profile(user_profile_id)
        if not full_profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado.")

        # Calcula meta calórica
        caloric_goal = calculate_caloric_goal(full_profile)

        # Busca resumo nutricional do dia
        nutrition_summary = get_daily_summary(user_profile_id, current_date)

        # Calcula valores derivados
        calories_consumed = nutrition_summary['total_calories']
        calories_remaining = caloric_goal - calories_consumed
        progress_percentage = min((calories_consumed / caloric_goal) * 100, 150) if caloric_goal > 0 else 0
        entries_today = nutrition_summary['total_entries']
        diary_updated_today = entries_today > 0

        # Determina status do progresso
        progress_status = determine_progress_status(progress_percentage)

        # Gera motivação e dica personalizadas
        ai_motivation = generate_ai_motivation(full_profile, progress_percentage, calories_remaining)
        quick_tip = generate_quick_tip(full_profile, progress_status, entries_today)

        # Formatar objetivos
        goals_text = ", ".join(full_profile.get('goals', [])) if full_profile.get('goals') else "Não definidos"

        return DashboardResponse(
            user_name=full_profile['name'],
            user_age=full_profile['age'],
            user_weight=full_profile['weight'],
            user_goals=goals_text,
            has_profile=True,
            caloric_goal=caloric_goal,
            calories_consumed=calories_consumed,
            calories_remaining=calories_remaining,
            progress_percentage=progress_percentage,
            total_proteins=nutrition_summary['total_proteins'],
            total_carbs=nutrition_summary['total_carbs'],
            total_fats=nutrition_summary['total_fats'],
            entries_today=entries_today,
            diary_updated_today=diary_updated_today,
            current_date=current_date,
            progress_status=progress_status,
            ai_motivation=ai_motivation,
            quick_tip=quick_tip
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(e)}")

def determine_progress_status(progress_percentage: float) -> str:
    """Determina o status do progresso baseado na porcentagem."""
    if progress_percentage < 30:
        return "behind"
    elif progress_percentage < 85:
        return "on_track"
    elif progress_percentage <= 110:
        return "ahead"
    else:
        return "exceeded"

def generate_ai_motivation(profile: dict, progress_percentage: float, calories_remaining: float) -> str:
    """Gera mensagem motivacional personalizada baseada no perfil e progresso."""
    name = profile.get('name', 'Usuário')
    goals = profile.get('goals', [])

    # Identifica o objetivo principal
    main_goal = "manutenção"
    if any('emagrecimento' in g.lower() or 'emagrecer' in g.lower() for g in goals):
        main_goal = "emagrecimento"
    elif any('ganho' in g.lower() and ('peso' in g.lower() or 'massa' in g.lower()) for g in goals):
        main_goal = "ganho_massa"

    # Mensagens baseadas no progresso e objetivo
    if progress_percentage < 30:
        if main_goal == "emagrecimento":
            return f"Bom dia, {name}! 🌅 Você ainda tem {calories_remaining:.0f} kcal para distribuir hoje. Que tal um café da manhã rico em proteínas para acelerar o metabolismo?"
        elif main_goal == "ganho_massa":
            return f"Oi {name}! 💪 Você tem {calories_remaining:.0f} kcal para consumir hoje. Foque em proteínas de qualidade para construir massa muscular!"
        else:
            return f"Olá {name}! ☀️ Dia novo, oportunidades novas! Você tem {calories_remaining:.0f} kcal para distribuir em refeições equilibradas."

    elif progress_percentage < 85:
        return f"Excelente, {name}! 🎯 Você está no caminho certo com {progress_percentage:.0f}% da sua meta. Continue assim!"

    elif progress_percentage <= 110:
        if main_goal == "emagrecimento":
            return f"Perfeito, {name}! ✅ Você atingiu sua meta para {main_goal}. Mantenha o foco e os resultados virão!"
        else:
            return f"Fantástico, {name}! 🔥 Meta atingida com {progress_percentage:.0f}%! Você está comprometido com seus objetivos."

    else:
        if main_goal == "emagrecimento":
            return f"Atenção {name}! ⚠️ Você passou {progress_percentage-100:.0f}% da meta. Tente refeições mais leves no restante do dia."
        else:
            return f"Cuidado {name}! 📊 Você excedeu a meta em {progress_percentage-100:.0f}%. Balance nas próximas refeições."

def generate_quick_tip(profile: dict, progress_status: str, entries_today: int) -> str:
    """Gera dica rápida personalizada."""
    goals = profile.get('goals', [])
    age = profile.get('age', 30)
    activity_level = profile.get('activity_level', 'moderado')

    if entries_today == 0:
        return "🍳 Registre sua primeira refeição do dia para começar o acompanhamento nutricional!"

    if progress_status == "behind":
        if any('emagrecimento' in g.lower() for g in goals):
            return "🥗 Inclua vegetais em suas próximas refeições para aumentar saciedade com poucas calorias."
        else:
            return "🥜 Adicione oleaginosas ou abacate para aumentar as calorias saudavelmente."

    elif progress_status == "on_track":
        if activity_level in ['ativo', 'muito_ativo']:
            return "💧 Mantenha-se bem hidratado, especialmente após os treinos!"
        else:
            return "🚶‍♂️ Que tal uma caminhada de 10 minutos após a próxima refeição?"

    elif progress_status == "exceeded":
        return "🧘‍♀️ Pratique mindful eating: coma devagar e preste atenção aos sinais de saciedade."

    # Dicas gerais baseadas na idade
    if age > 50:
        return "💪 Priorize proteínas em cada refeição para manter a massa muscular."
    elif age < 25:
        return "📚 Estabeleça hábitos alimentares saudáveis que durarão toda a vida!"
    else:
        return "⚖️ Mantenha o equilíbrio: 50% vegetais, 25% proteínas, 25% carboidratos complexos."