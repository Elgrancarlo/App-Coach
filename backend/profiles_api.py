"""API endpoints para gerenciamento de perfis de usuário.

Contém endpoints REST para criar, ler, atualizar e deletar perfis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from database import create_profile, get_profile, update_profile, list_profiles, delete_profile

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

class ProfileCreate(BaseModel):
    """Schema para criação de perfil."""
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., gt=0, le=120)
    weight: float = Field(..., gt=0, le=500)
    height: float = Field(..., gt=0, le=300)
    sex: str = Field(..., pattern="^(masculino|feminino|outro)$")
    activity_level: str = Field(..., pattern="^(sedentario|leve|moderado|ativo|muito_ativo)$")
    goals: List[str] = Field(default=[])
    dietary_restrictions: List[str] = Field(default=[])
    medical_conditions: List[str] = Field(default=[])

class ProfileUpdate(BaseModel):
    """Schema para atualização de perfil."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, gt=0, le=120)
    weight: Optional[float] = Field(None, gt=0, le=500)
    height: Optional[float] = Field(None, gt=0, le=300)
    sex: Optional[str] = Field(None, pattern="^(masculino|feminino|outro)$")
    activity_level: Optional[str] = Field(None, pattern="^(sedentario|leve|moderado|ativo|muito_ativo)$")
    goals: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    medical_conditions: Optional[List[str]] = None

class ProfileResponse(BaseModel):
    """Schema para resposta de perfil."""
    id: str
    name: str
    age: int
    weight: float
    height: float
    sex: str
    activity_level: str
    goals: List[str]
    dietary_restrictions: List[str]
    medical_conditions: List[str]
    created_at: str
    updated_at: str

class ProfileListItem(BaseModel):
    """Schema para item da lista de perfis."""
    id: str
    name: str
    age: int
    created_at: str

@router.post("/", response_model=dict)
async def create_user_profile(profile: ProfileCreate):
    """Cria um novo perfil de usuário."""
    try:
        profile_id = create_profile(profile.dict())
        return {"id": profile_id, "message": "Perfil criado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar perfil: {str(e)}")

@router.get("/", response_model=List[ProfileListItem])
async def list_user_profiles():
    """Lista todos os perfis."""
    try:
        return list_profiles()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar perfis: {str(e)}")

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_user_profile(profile_id: str):
    """Busca um perfil específico pelo ID."""
    try:
        profile = get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar perfil: {str(e)}")

@router.put("/{profile_id}", response_model=dict)
async def update_user_profile(profile_id: str, profile: ProfileUpdate):
    """Atualiza um perfil existente."""
    try:
        # Remove campos None do dicionário
        update_data = {k: v for k, v in profile.dict().items() if v is not None}

        success = update_profile(profile_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        return {"message": "Perfil atualizado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar perfil: {str(e)}")

@router.delete("/{profile_id}", response_model=dict)
async def delete_user_profile(profile_id: str):
    """Remove um perfil."""
    try:
        success = delete_profile(profile_id)
        if not success:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        return {"message": "Perfil removido com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover perfil: {str(e)}")

@router.get("/{profile_id}/summary", response_model=dict)
async def get_profile_summary(profile_id: str):
    """Retorna um resumo formatado do perfil para uso do agente."""
    try:
        profile = get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        # Calcula IMC
        height_m = profile['height'] / 100  # converte cm para metros
        imc = profile['weight'] / (height_m ** 2)

        # Formata resumo
        summary = f"""
PERFIL DO USUÁRIO:

📋 **DADOS PESSOAIS**
- Nome: {profile['name']}
- Idade: {profile['age']} anos
- Peso: {profile['weight']} kg
- Altura: {profile['height']} cm
- Sexo: {profile['sex']}
- IMC: {imc:.1f}

🏃 **ATIVIDADE FÍSICA**
- Nível: {profile['activity_level']}

🎯 **OBJETIVOS**
- {', '.join(profile['goals']) if profile['goals'] else 'Nenhum objetivo definido'}

🚫 **RESTRIÇÕES ALIMENTARES**
- {', '.join(profile['dietary_restrictions']) if profile['dietary_restrictions'] else 'Nenhuma restrição'}

🏥 **CONDIÇÕES MÉDICAS**
- {', '.join(profile['medical_conditions']) if profile['medical_conditions'] else 'Nenhuma condição reportada'}

📅 **PERFIL CRIADO EM**: {profile['created_at'][:10]}
        """.strip()

        return {
            "summary": summary,
            "raw_data": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")