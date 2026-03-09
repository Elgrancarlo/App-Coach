"""API endpoints para diário nutricional.

Contém endpoints REST para gerenciar entradas de alimentos e resumos nutricionais.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from database import (
    add_food_entry, get_daily_food_entries, get_daily_summary,
    delete_food_entry, calculate_caloric_goal, list_profiles, get_profile
)

router = APIRouter(prefix="/api/food-diary", tags=["food_diary"])

class FoodEntryCreate(BaseModel):
    """Schema para criação de entrada de alimento."""
    meal_type: str = Field(..., pattern="^(cafe_da_manha|almoco|lanche|jantar|lanche_noturno)$")
    food_name: str = Field(..., min_length=1, max_length=200)
    calories: float = Field(..., gt=0, le=5000)
    proteins: Optional[float] = Field(0, ge=0, le=1000)
    carbs: Optional[float] = Field(0, ge=0, le=1000)
    fats: Optional[float] = Field(0, ge=0, le=1000)
    portion_size: Optional[str] = Field("", max_length=100)
    description: Optional[str] = Field("", max_length=500)
    entry_method: str = Field(..., pattern="^(text|photo)$")

class FoodEntryResponse(BaseModel):
    """Schema para resposta de entrada de alimento."""
    id: str
    user_profile_id: str
    date: str
    meal_type: str
    food_name: str
    calories: float
    proteins: float
    carbs: float
    fats: float
    portion_size: str
    description: str
    entry_method: str
    created_at: str

class DailySummaryResponse(BaseModel):
    """Schema para resumo diário nutricional."""
    date: str
    caloric_goal: int
    total_calories: float
    remaining_calories: float
    total_proteins: float
    total_carbs: float
    total_fats: float
    total_entries: int
    progress_percentage: float
    ai_comment: str

@router.post("/entries", response_model=dict)
async def create_food_entry(entry: FoodEntryCreate):
    """Adiciona uma nova entrada de alimento no diário."""
    try:
        # Para agora, usar o primeiro perfil disponível
        # TODO: Implementar autenticação e pegar perfil do usuário logado
        profiles = list_profiles()
        if not profiles:
            raise HTTPException(status_code=404, detail="Nenhum perfil encontrado. Configure seu perfil primeiro.")

        user_profile_id = profiles[0]['id']
        current_date = datetime.now().date().isoformat()

        entry_data = {
            "user_profile_id": user_profile_id,
            "date": current_date,
            "meal_type": entry.meal_type,
            "food_name": entry.food_name,
            "calories": entry.calories,
            "proteins": entry.proteins or 0,
            "carbs": entry.carbs or 0,
            "fats": entry.fats or 0,
            "portion_size": entry.portion_size or "",
            "description": entry.description or "",
            "entry_method": entry.entry_method
        }

        entry_id = add_food_entry(entry_data)
        return {"id": entry_id, "message": "Entrada adicionada com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar entrada: {str(e)}")

@router.get("/entries", response_model=List[FoodEntryResponse])
async def get_food_entries(date: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD")):
    """Lista entradas de alimento do dia especificado ou hoje."""
    try:
        # Para agora, usar o primeiro perfil disponível
        profiles = list_profiles()
        if not profiles:
            raise HTTPException(status_code=404, detail="Nenhum perfil encontrado.")

        user_profile_id = profiles[0]['id']
        target_date = date or datetime.now().date().isoformat()

        entries = get_daily_food_entries(user_profile_id, target_date)
        return entries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar entradas: {str(e)}")

@router.get("/summary", response_model=DailySummaryResponse)
async def get_daily_nutrition_summary(date: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD")):
    """Retorna resumo nutricional do dia com meta calórica e comentário da IA."""
    try:
        # Para agora, usar o primeiro perfil disponível
        profiles = list_profiles()
        if not profiles:
            raise HTTPException(status_code=404, detail="Nenhum perfil encontrado.")

        user_profile_id = profiles[0]['id']
        target_date = date or datetime.now().date().isoformat()

        # Busca o perfil completo para calcular a meta
        profile = get_profile(user_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado.")

        # Calcula meta calórica
        caloric_goal = calculate_caloric_goal(profile)

        # Busca resumo do dia
        summary = get_daily_summary(user_profile_id, target_date)

        # Calcula valores derivados
        remaining_calories = caloric_goal - summary['total_calories']
        progress_percentage = min((summary['total_calories'] / caloric_goal) * 100, 100) if caloric_goal > 0 else 0

        # Gera comentário da IA baseado no progresso
        ai_comment = generate_ai_comment(progress_percentage, remaining_calories, caloric_goal)

        return DailySummaryResponse(
            date=target_date,
            caloric_goal=caloric_goal,
            total_calories=summary['total_calories'],
            remaining_calories=remaining_calories,
            total_proteins=summary['total_proteins'],
            total_carbs=summary['total_carbs'],
            total_fats=summary['total_fats'],
            total_entries=summary['total_entries'],
            progress_percentage=progress_percentage,
            ai_comment=ai_comment
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")

@router.delete("/entries/{entry_id}", response_model=dict)
async def remove_food_entry(entry_id: str):
    """Remove uma entrada de alimento."""
    try:
        # Para agora, usar o primeiro perfil disponível
        profiles = list_profiles()
        if not profiles:
            raise HTTPException(status_code=404, detail="Nenhum perfil encontrado.")

        user_profile_id = profiles[0]['id']

        success = delete_food_entry(entry_id, user_profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Entrada não encontrada.")

        return {"message": "Entrada removida com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover entrada: {str(e)}")

def generate_ai_comment(progress_percentage: float, remaining_calories: float, caloric_goal: int) -> str:
    """Gera comentário motivacional da IA baseado no progresso."""

    if progress_percentage < 30:
        if remaining_calories > caloric_goal * 0.7:
            return "🌅 Bom dia! Você ainda tem bastante margem para suas refeições hoje. Que tal começar com um café da manhã nutritivo?"
        else:
            return "💪 Você está começando bem o dia! Continue assim com refeições balanceadas."

    elif progress_percentage < 60:
        return "👍 Ótimo progresso! Você está no caminho certo para atingir sua meta diária."

    elif progress_percentage < 85:
        return "🎯 Excelente! Você está quase atingindo sua meta. Mantenha o foco!"

    elif progress_percentage < 100:
        return "🔥 Fantástico! Você está muito próximo da sua meta diária!"

    elif progress_percentage <= 110:
        return "✅ Perfeito! Você atingiu sua meta calórica do dia. Parabéns!"

    elif progress_percentage <= 130:
        return "⚠️ Cuidado! Você passou um pouco da sua meta. Tente ajustar nas próximas refeições."

    else:
        return "🚨 Atenção! Você excedeu significativamente sua meta diária. Considere refeições mais leves no restante do dia."