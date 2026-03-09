"""Ferramentas simples usadas pelo agente.

Contém a ferramenta `tavily_search` para buscas na web, `food_vision_analyzer` para análise de alimentos por imagem
e `get_user_profile` para consulta de dados personalizados do usuário.
"""

import base64
import json
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch
import openai


load_dotenv()


@tool
def tavily_search(
    query: str,
    max_results: int = 5,
    include_raw_content: bool = False,
) -> str:
    """Busca conteúdo na Internet com Tavily.

    Parâmetros:
    - query: texto da pesquisa.
    - max_results: quantidade máxima de resultados retornados.
    - include_raw_content: quando True, inclui conteúdo bruto das páginas.

    Retorno:
    - string JSON com os resultados (ou string simples em fallback).
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("Defina TAVILY_API_KEY para usar tavily_search.")

    client = TavilySearch(
        api_key=api_key,
        max_results=max_results,
        topic="general",
        include_raw_content=include_raw_content,
    )
    result = client.invoke(input=query)
    try:
        return json.dumps(result)
    except Exception:
        return str(result)


@tool
def food_vision_analyzer(image_base64: str, additional_info: str = "") -> str:
    """Analisa uma foto de alimentos e fornece estimativa detalhada dos macronutrientes.

    Use esta ferramenta quando o usuário enviar uma imagem de comida ou mencionar que quer analiizar uma foto.

    A ferramenta identifica:
    - Tipo de alimento
    - Quantidade estimada
    - Macronutrientes (proteínas, carboidratos, gorduras)
    - Calorias totais
    - Sugestões nutricionais

    Parâmetros:
    - image_base64: Imagem codificada em base64
    - additional_info: Informações adicionais sobre a refeição (opcional)

    Retorno:
    - Análise nutricional completa em formato texto
    """
    try:
        # Debug: Log informações sobre a imagem recebida
        print(f"[DEBUG] Recebendo análise de imagem:")
        print(f"[DEBUG] - Base64 length: {len(image_base64) if image_base64 else 0}")
        print(f"[DEBUG] - Base64 prefix: {image_base64[:50] if image_base64 else 'None'}...")
        print(f"[DEBUG] - Additional info: {additional_info}")
        print(f"[DEBUG] - Timestamp: {datetime.now()}")

        # Se image_base64 está vazio, tenta extrair das mensagens do contexto atual
        if not image_base64 or len(image_base64) < 100:
            print(f"[DEBUG] Base64 vazio ou muito pequeno, tentando buscar nas mensagens do sistema...")
            # Tenta buscar das variáveis de contexto globais ou do agente
            try:
                # Este é um fallback - no contexto do LangChain, pode haver mensagens no contexto
                import inspect
                frame = inspect.currentframe()
                while frame:
                    frame_locals = frame.f_locals
                    for var_name, var_value in frame_locals.items():
                        if isinstance(var_value, str) and var_value.startswith("IMAGE_DATA_BASE64:"):
                            extracted_base64 = var_value.replace("IMAGE_DATA_BASE64:", "").strip()
                            if len(extracted_base64) > 100:
                                print(f"[DEBUG] Encontrado base64 no contexto: {len(extracted_base64)} chars")
                                image_base64 = extracted_base64
                                break
                    frame = frame.f_back
                    if frame is None:
                        break
                if not image_base64 or len(image_base64) < 100:
                    return "❌ Erro: Dados de imagem inválidos ou não encontrados para análise."
            except Exception as e:
                print(f"[DEBUG] Erro ao buscar imagem no contexto: {e}")
                return "❌ Erro: Dados de imagem inválidos ou não encontrados para análise."
        # Configura cliente OpenAI usando a mesma API key do OpenRouter
        openai_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openai_api_key:
            return "❌ Erro: API key não configurada para análise de imagens."

        # Cria cliente OpenAI
        client = openai.OpenAI(
            api_key=openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Prompt especializado para análise nutricional
        system_prompt = """
        Você é um nutricionista especialista em análise visual de alimentos. Analise a imagem fornecida e forneça uma estimativa detalhada dos macronutrientes.

        FORMATO DE RESPOSTA:

        ## 🥗 ALIMENTOS IDENTIFICADOS
        [Liste cada alimento visível na imagem]

        ## ⚖️ ESTIMATIVA DE QUANTIDADE
        [Estime as porções de cada alimento]

        ## 📊 ANÁLISE NUTRICIONAL
        **Por porção estimada:**
        - 🔥 **Calorias**: [valor] kcal
        - 🥩 **Proteínas**: [valor]g
        - 🍞 **Carboidratos**: [valor]g
        - 🥑 **Gorduras**: [valor]g
        - 🧂 **Fibras**: [valor]g (se relevante)

        ## 💡 OBSERVAÇÕES NUTRICIONAIS
        - Avaliação geral da refeição
        - Sugestões de melhoria
        - Alertas importantes (se houver)

        ## 🎯 DICAS DO COACH
        [Dicas personalizadas baseadas no alimento analisado]

        IMPORTANTE: Seja preciso mas indique que são estimativas visuais. Se a qualidade da imagem for ruim, mencione isso.
        """

        user_prompt = f"""
        Analise esta imagem de alimento e forneça a estimativa nutricional completa.

        {f"Informações adicionais fornecidas: {additional_info}" if additional_info else ""}

        Seja detalhado e educativo na análise, como um verdadeiro coach nutricional.
        """

        # Chama a API de visão
        response = client.chat.completions.create(
            model="openai/gpt-4o",  # Modelo com suporte a visão
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1  # Baixa temperatura para análise mais precisa
        )

        analysis_result = response.choices[0].message.content

        return f"""
📸 **ANÁLISE NUTRICIONAL POR IMAGEM**

{analysis_result}

---
*Análise realizada por IA baseada em estimativa visual. Para cálculos precisos, consulte tabelas nutricionais específicas ou um nutricionista.*
"""

    except Exception as e:
        return f"""
❌ **Erro na análise da imagem**

Não foi possível analisar a imagem neste momento.

**Erro**: {str(e)}

**Alternativas**:
- Descreva o alimento por texto que posso ajudar com estimativa de macros
- Verifique se a imagem está clara e bem iluminada
- Tente novamente em alguns momentos
"""


@tool
def get_user_profile(user_id: str = "default") -> str:
    """Consulta dados do perfil do usuário para personalização das recomendações.

    Use esta ferramenta sempre que precisar personalizar recomendações baseadas nos
    dados, objetivos e restrições do usuário. Isso inclui sugestões de receitas,
    treinos, metas nutricionais e orientações de saúde.

    Parâmetros:
    - user_id: ID do usuário (por enquanto usa "default" como placeholder)

    Retorno:
    - Dados estruturados do perfil do usuário ou mensagem informativa se não há perfil
    """
    try:
        # Import local para evitar problemas de dependência circular
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import get_profile, list_profiles

        # Debug: Log da consulta
        print(f"[DEBUG] Consultando perfil do usuário: {user_id}")

        # Por enquanto, como não temos sistema de usuários completo,
        # vamos buscar o perfil mais recente cadastrado
        profiles = list_profiles()

        if not profiles:
            return """
❌ **Nenhum perfil encontrado**

Para ter recomendações personalizadas, é necessário configurar seu perfil primeiro.

**Como configurar:**
- Acesse a aba "Definir Objetivos"
- Preencha seus dados pessoais (idade, peso, altura, etc.)
- Defina seus objetivos (emagrecimento, ganho de massa, etc.)
- Informe restrições alimentares e condições médicas

Após configurar seu perfil, todas as recomendações serão personalizadas para você!
"""

        # Pega o perfil mais recente (último criado)
        latest_profile_id = profiles[0]['id']
        profile = get_profile(latest_profile_id)

        if not profile:
            return "❌ Erro ao carregar dados do perfil."

        # Calcula IMC para contexto adicional
        height_m = profile['height'] / 100
        imc = profile['weight'] / (height_m ** 2)

        # Classifica IMC
        if imc < 18.5:
            imc_class = "Abaixo do peso"
        elif imc < 25:
            imc_class = "Peso normal"
        elif imc < 30:
            imc_class = "Sobrepeso"
        else:
            imc_class = "Obesidade"

        # Formata dados para o agente usar
        profile_summary = f"""
📊 **PERFIL DO USUÁRIO - {profile['name'].upper()}**

👤 **DADOS PESSOAIS**
- Idade: {profile['age']} anos
- Peso: {profile['weight']} kg
- Altura: {profile['height']} cm
- Sexo: {profile['sex']}
- IMC: {imc:.1f} ({imc_class})

🏃 **ATIVIDADE FÍSICA**
- Nível: {profile['activity_level']}

🎯 **OBJETIVOS PRINCIPAIS**
{', '.join(profile['goals']) if profile['goals'] else 'Não definidos'}

🚫 **RESTRIÇÕES ALIMENTARES**
{', '.join(profile['dietary_restrictions']) if profile['dietary_restrictions'] else 'Nenhuma'}

🏥 **CONDIÇÕES MÉDICAS**
{', '.join(profile['medical_conditions']) if profile['medical_conditions'] else 'Nenhuma informada'}

💡 **ORIENTAÇÕES DE USO:**
Use esses dados para personalizar TODAS as suas recomendações:
- Receitas adequadas às restrições
- Treinos compatíveis com o nível de atividade
- Metas calóricas alinhadas aos objetivos
- Sugestões considerando condições médicas
- Abordagem adaptada ao perfil e objetivos

⚠️ **IMPORTANTE:** Sempre considere essas informações ao fazer recomendações!
"""

        print(f"[DEBUG] Perfil carregado com sucesso para {profile['name']}")
        return profile_summary

    except Exception as e:
        print(f"[DEBUG] Erro ao consultar perfil: {e}")
        return f"""
⚠️ **Erro ao carregar perfil**

Não foi possível acessar os dados do seu perfil no momento.

**Erro técnico**: {str(e)}

**Para resolver**:
- Verifique se já configurou seu perfil na aba "Definir Objetivos"
- Tente novamente em alguns momentos
- Se o problema persistir, reconfigure seu perfil

Enquanto isso, posso ajudar com orientações gerais de saúde e bem-estar.
"""


@tool
def save_user_profile(
    name: str,
    age: int,
    weight: float,
    height: float,
    sex: str,
    activity_level: str,
    goals: str = "",
    dietary_restrictions: str = "",
    medical_conditions: str = ""
) -> str:
    """Salva ou atualiza o perfil do usuário com os dados coletados durante a conversa.

    Use esta ferramenta quando o usuário fornecer informações pessoais para criar/atualizar seu perfil.
    É especialmente útil na aba 'Definir Objetivos' para capturar dados através do chat.

    Parâmetros:
    - name: Nome completo do usuário
    - age: Idade em anos (entre 1 e 120)
    - weight: Peso em kg (entre 1 e 500)
    - height: Altura em cm (entre 1 e 300)
    - sex: Sexo (masculino, feminino, outro)
    - activity_level: Nível de atividade (sedentario, leve, moderado, ativo, muito_ativo)
    - goals: Objetivos separados por vírgula (ex: "emagrecimento, ganho de massa")
    - dietary_restrictions: Restrições alimentares separadas por vírgula (ex: "vegetariano, sem glúten")
    - medical_conditions: Condições médicas separadas por vírgula (ex: "diabetes, hipertensão")

    Retorno:
    - Mensagem de confirmação do salvamento
    """
    try:
        # Import local para usar as funções de database
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import create_profile, update_profile, list_profiles

        # Debug: Log dos dados recebidos
        print(f"[DEBUG] Salvando perfil do usuário:")
        print(f"[DEBUG] - Nome: {name}")
        print(f"[DEBUG] - Idade: {age}")
        print(f"[DEBUG] - Peso: {weight}kg")
        print(f"[DEBUG] - Altura: {height}cm")
        print(f"[DEBUG] - Sexo: {sex}")
        print(f"[DEBUG] - Nível de atividade: {activity_level}")
        print(f"[DEBUG] - Objetivos: {goals}")

        # Converte strings separadas por vírgula em listas
        goals_list = [g.strip() for g in goals.split(",") if g.strip()] if goals else []
        restrictions_list = [r.strip() for r in dietary_restrictions.split(",") if r.strip()] if dietary_restrictions else []
        conditions_list = [c.strip() for c in medical_conditions.split(",") if c.strip()] if medical_conditions else []

        # Valida os dados de entrada
        if not name.strip():
            return "❌ Erro: Nome é obrigatório."

        if not (1 <= age <= 120):
            return "❌ Erro: Idade deve estar entre 1 e 120 anos."

        if not (1 <= weight <= 500):
            return "❌ Erro: Peso deve estar entre 1 e 500 kg."

        if not (1 <= height <= 300):
            return "❌ Erro: Altura deve estar entre 1 e 300 cm."

        # Valida o sexo
        if sex.lower() not in ["masculino", "feminino", "outro"]:
            return "❌ Erro: Sexo deve ser 'masculino', 'feminino' ou 'outro'."

        # Valida o nível de atividade
        valid_activity_levels = ["sedentario", "leve", "moderado", "ativo", "muito_ativo"]
        if activity_level.lower() not in valid_activity_levels:
            return f"❌ Erro: Nível de atividade deve ser um dos seguintes: {', '.join(valid_activity_levels)}."

        # Dados do perfil formatados
        profile_data = {
            "name": name.strip(),
            "age": int(age),
            "weight": float(weight),
            "height": float(height),
            "sex": sex.lower(),
            "activity_level": activity_level.lower(),
            "goals": goals_list,
            "dietary_restrictions": restrictions_list,
            "medical_conditions": conditions_list
        }

        # Verifica se já existe um perfil
        existing_profiles = list_profiles()

        if existing_profiles:
            # Atualiza o perfil existente (pega o mais recente)
            profile_id = existing_profiles[0]['id']
            success = update_profile(profile_id, profile_data)

            if success:
                # Calcula IMC para mostrar no resultado
                height_m = float(height) / 100
                imc = float(weight) / (height_m ** 2)

                return f"""✅ **PERFIL ATUALIZADO COM SUCESSO!**

📋 **Dados salvos para {name}:**
- Idade: {age} anos
- Peso: {weight}kg | Altura: {height}cm
- IMC: {imc:.1f}
- Sexo: {sex}
- Atividade: {activity_level}
- Objetivos: {', '.join(goals_list) if goals_list else 'Não definidos'}
- Restrições: {', '.join(restrictions_list) if restrictions_list else 'Nenhuma'}
- Condições médicas: {', '.join(conditions_list) if conditions_list else 'Nenhuma'}

🎯 **Seu perfil está configurado!** Agora todas as recomendações serão personalizadas para seus objetivos e necessidades específicas.

💡 **Próximos passos:**
- Peça recomendações de receitas personalizadas
- Solicite um plano de treinos adequado ao seu perfil
- Receba orientações nutricionais específicas para seus objetivos"""

            else:
                return "❌ Erro ao atualizar o perfil. Tente novamente."
        else:
            # Cria um novo perfil
            profile_id = create_profile(profile_data)

            if profile_id:
                # Calcula IMC para mostrar no resultado
                height_m = float(height) / 100
                imc = float(weight) / (height_m ** 2)

                return f"""🎉 **PERFIL CRIADO COM SUCESSO!**

📋 **Seu perfil foi salvo, {name}:**
- Idade: {age} anos
- Peso: {weight}kg | Altura: {height}cm
- IMC: {imc:.1f}
- Sexo: {sex}
- Atividade: {activity_level}
- Objetivos: {', '.join(goals_list) if goals_list else 'Não definidos'}
- Restrições: {', '.join(restrictions_list) if restrictions_list else 'Nenhuma'}
- Condições médicas: {', '.join(conditions_list) if conditions_list else 'Nenhuma'}

🚀 **Perfeito! Agora sou seu coach pessoal!** Todas as recomendações serão personalizadas especificamente para você.

💡 **Vamos começar:**
- Quer receitas adequadas aos seus objetivos?
- Precisa de um plano de treinos personalizado?
- Tem alguma dúvida sobre nutrição específica?"""

            else:
                return "❌ Erro ao criar o perfil. Tente novamente."

    except ValueError as e:
        return f"❌ Erro nos dados fornecidos: {str(e)}. Verifique se idade, peso e altura são números válidos."
    except Exception as e:
        print(f"[DEBUG] Erro ao salvar perfil: {e}")
        return f"❌ Erro técnico ao salvar o perfil: {str(e)}. Tente novamente ou verifique os dados informados."


@tool
def add_food_to_diary(
    food_name: str,
    calories: float,
    meal_type: str = "lanche",
    proteins: float = 0,
    carbs: float = 0,
    fats: float = 0,
    portion_size: str = "",
    description: str = "",
    entry_method: str = "text"
) -> str:
    """Adiciona uma entrada de alimento no diário nutricional do usuário.

    Use esta ferramenta quando o usuário relatar o que comeu ou após análise de foto de alimento.
    Útil na aba 'Calculadora/Nutrição' para registrar o consumo diário.

    Parâmetros:
    - food_name: Nome do alimento (ex: "Arroz integral", "Frango grelhado")
    - calories: Quantidade de calorias (kcal)
    - meal_type: Tipo de refeição (cafe_da_manha, almoco, lanche, jantar, lanche_noturno)
    - proteins: Proteínas em gramas (opcional)
    - carbs: Carboidratos em gramas (opcional)
    - fats: Gorduras em gramas (opcional)
    - portion_size: Tamanho da porção (ex: "1 prato", "200g")
    - description: Descrição adicional ou observações
    - entry_method: Método de entrada ("text" ou "photo")

    Retorno:
    - Confirmação do registro e resumo nutricional atualizado
    """
    try:
        # Import local para usar as funções de database
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database import add_food_entry, list_profiles
        import requests
        from datetime import datetime

        # Debug: Log dos dados recebidos
        print(f"[DEBUG] Adicionando alimento ao diário:")
        print(f"[DEBUG] - Alimento: {food_name}")
        print(f"[DEBUG] - Calorias: {calories}")
        print(f"[DEBUG] - Refeição: {meal_type}")
        print(f"[DEBUG] - Método: {entry_method}")

        # Validações básicas
        if not food_name.strip():
            return "❌ Erro: Nome do alimento é obrigatório."

        if calories <= 0:
            return "❌ Erro: Calorias devem ser um valor positivo."

        valid_meal_types = ["cafe_da_manha", "almoco", "lanche", "jantar", "lanche_noturno"]
        if meal_type not in valid_meal_types:
            return f"❌ Erro: Tipo de refeição deve ser um dos seguintes: {', '.join(valid_meal_types)}."

        # Busca perfil do usuário
        profiles = list_profiles()
        if not profiles:
            return "❌ Erro: Nenhum perfil encontrado. Configure seu perfil na aba 'Definir Objetivos' primeiro."

        user_profile_id = profiles[0]['id']
        current_date = datetime.now().date().isoformat()

        # Dados da entrada
        entry_data = {
            "user_profile_id": user_profile_id,
            "date": current_date,
            "meal_type": meal_type,
            "food_name": food_name.strip(),
            "calories": float(calories),
            "proteins": float(proteins),
            "carbs": float(carbs),
            "fats": float(fats),
            "portion_size": portion_size.strip(),
            "description": description.strip(),
            "entry_method": entry_method
        }

        # Salva no banco
        entry_id = add_food_entry(entry_data)

        # Busca resumo atualizado via API
        try:
            response = requests.get("http://localhost:8000/api/food-diary/summary", timeout=5)
            if response.status_code == 200:
                summary = response.json()

                meal_emoji = {
                    "cafe_da_manha": "🍳",
                    "almoco": "🍽️",
                    "lanche": "🍎",
                    "jantar": "🌙",
                    "lanche_noturno": "🌟"
                }

                return f"""✅ **ALIMENTO ADICIONADO AO DIÁRIO!**

{meal_emoji.get(meal_type, '🍽️')} **{food_name}** - {calories} kcal
📊 **Macros:** {proteins}g proteína | {carbs}g carbo | {fats}g gordura
{f'📏 **Porção:** {portion_size}' if portion_size else ''}

📈 **RESUMO DO DIA:**
🎯 **Meta:** {summary['caloric_goal']} kcal
✅ **Consumido:** {summary['total_calories']:.0f} kcal
📊 **Restante:** {summary['remaining_calories']:.0f} kcal
📍 **Progresso:** {summary['progress_percentage']:.1f}%

🤖 **{summary['ai_comment']}**

💡 Continue registrando suas refeições para manter o controle nutricional!"""

            else:
                return f"✅ Alimento '{food_name}' adicionado ao diário com sucesso! ({calories} kcal)"

        except Exception as api_error:
            print(f"[DEBUG] Erro ao buscar resumo: {api_error}")
            return f"✅ Alimento '{food_name}' adicionado ao diário com sucesso! ({calories} kcal)"

    except ValueError as e:
        return f"❌ Erro nos valores fornecidos: {str(e)}. Verifique se calorias e macros são números válidos."
    except Exception as e:
        print(f"[DEBUG] Erro ao adicionar alimento: {e}")
        return f"❌ Erro técnico ao adicionar alimento: {str(e)}. Tente novamente."


@tool
def get_daily_nutrition_summary() -> str:
    """Busca o resumo nutricional do dia atual do usuário.

    Use esta ferramenta para mostrar o progresso calórico e nutricional diário.
    Inclui meta calórica, consumo atual, calorias restantes e comentário motivacional.

    Retorno:
    - Resumo completo do dia com progresso e recomendações
    """
    try:
        import requests
        from datetime import datetime

        print(f"[DEBUG] Buscando resumo nutricional do dia")

        # Busca resumo via API
        response = requests.get("http://localhost:8000/api/food-diary/summary", timeout=5)

        if response.status_code == 200:
            summary = response.json()

            # Calcula porcentagem de macros (estimativa baseada em proporções padrão)
            total_macros = summary['total_proteins'] + summary['total_carbs'] + summary['total_fats']

            if total_macros > 0:
                protein_pct = (summary['total_proteins'] / total_macros) * 100
                carbs_pct = (summary['total_carbs'] / total_macros) * 100
                fats_pct = (summary['total_fats'] / total_macros) * 100
                macro_info = f"""
🥩 **Proteínas:** {summary['total_proteins']:.1f}g ({protein_pct:.1f}%)
🍞 **Carboidratos:** {summary['total_carbs']:.1f}g ({carbs_pct:.1f}%)
🥑 **Gorduras:** {summary['total_fats']:.1f}g ({fats_pct:.1f}%)"""
            else:
                macro_info = "\n📝 **Nenhum alimento registrado ainda hoje.**"

            progress_bar = "🟢" * int(summary['progress_percentage'] / 10) + "⚪" * (10 - int(summary['progress_percentage'] / 10))

            return f"""📊 **RESUMO NUTRICIONAL - {summary['date']}**

🎯 **META CALÓRICA:** {summary['caloric_goal']} kcal
✅ **CONSUMIDO:** {summary['total_calories']:.0f} kcal
📊 **RESTANTE:** {summary['remaining_calories']:.0f} kcal

📈 **PROGRESSO:** {summary['progress_percentage']:.1f}%
{progress_bar}
{macro_info}

📝 **REFEIÇÕES REGISTRADAS:** {summary['total_entries']}

🤖 **COMENTÁRIO DO COACH:**
{summary['ai_comment']}

💡 **Dica:** Continue registrando todos os alimentos para manter o controle nutricional preciso!"""

        else:
            return f"❌ Erro ao buscar resumo nutricional. Status: {response.status_code}"

    except Exception as e:
        print(f"[DEBUG] Erro ao buscar resumo nutricional: {e}")
        return f"""❌ **Erro ao buscar resumo nutricional**

**Para resolver**:
- Verifique se configurou seu perfil na aba 'Definir Objetivos'
- Tente novamente em alguns momentos
- Se o problema persistir, reinicie a aplicação

Enquanto isso, posso ajudar com orientações gerais de nutrição."""


@tool
def get_dashboard_overview() -> str:
    """Busca visão geral completa do dashboard do usuário.

    Use esta ferramenta para mostrar o status geral da jornada do usuário,
    incluindo progresso nutricional, insights personalizados e dicas.
    Ideal para dar boas-vindas e mostrar o panorama do dia.

    Retorno:
    - Resumo personalizado com dados do perfil, progresso nutricional e motivação
    """
    try:
        import requests

        print(f"[DEBUG] Buscando overview do dashboard")

        # Busca dados do dashboard via API
        response = requests.get("http://localhost:8000/api/dashboard/overview", timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Se não tem perfil, orienta configuração
            if not data['has_profile']:
                return f"""👋 **Bem-vindo ao Coach AI!**

🎯 **Configure seu perfil primeiro** na aba "Definir Objetivos" para começar sua jornada personalizada de saúde e bem-estar.

💡 **Com seu perfil completo, você terá:**
- Meta calórica personalizada para seus objetivos
- Recomendações de receitas adequadas ao seu perfil
- Planos de treino adaptados ao seu nível
- Acompanhamento nutricional inteligente

📊 **{data['ai_motivation']}**

🔧 **{data['quick_tip']}**"""

            # Monta o overview completo
            progress_emoji = {
                "behind": "🔻",
                "on_track": "🎯",
                "ahead": "🟢",
                "exceeded": "⚠️"
            }.get(data['progress_status'], "📊")

            # Barra visual de progresso
            filled_bars = int(data['progress_percentage'] / 10)
            progress_bar = "🟢" * min(filled_bars, 10) + "⚪" * max(0, 10 - filled_bars)
            if data['progress_percentage'] > 100:
                excess_bars = int((data['progress_percentage'] - 100) / 10)
                progress_bar = "🟢" * 10 + "🔴" * min(excess_bars, 3)

            # Status das refeições
            meal_status = "✅ Diário atualizado" if data['diary_updated_today'] else "📝 Nenhuma refeição registrada"

            return f"""👋 **Olá {data['user_name']}!** - {data['current_date']}

🎯 **SEUS OBJETIVOS:** {data['user_goals']}
📊 **{data['user_age']} anos | {data['user_weight']}kg**

## 📈 PROGRESSO NUTRICIONAL DE HOJE

{progress_emoji} **META CALÓRICA:** {data['caloric_goal']} kcal
✅ **CONSUMIDO:** {data['calories_consumed']:.0f} kcal
📊 **RESTANTE:** {data['calories_remaining']:.0f} kcal

**PROGRESSO:** {data['progress_percentage']:.1f}%
{progress_bar}

## 🥗 MACRONUTRIENTES

🥩 **Proteínas:** {data['total_proteins']:.1f}g
🍞 **Carboidratos:** {data['total_carbs']:.1f}g
🥑 **Gorduras:** {data['total_fats']:.1f}g

📝 **STATUS:** {meal_status} ({data['entries_today']} registros)

## 🤖 SEU COACH PESSOAL

💬 **{data['ai_motivation']}**

💡 **DICA DO DIA:** {data['quick_tip']}

## 🚀 AÇÕES RÁPIDAS

- 📸 **Analisar foto de alimento** na aba Nutrição
- 🥗 **Ver receitas personalizadas** na aba Receitas
- 🏋️ **Treino do dia** na aba Personal Trainer
- ⚙️ **Atualizar objetivos** na aba Definir Objetivos

Continue sua jornada de saúde! Estou aqui para te ajudar em cada passo. 💪"""

        else:
            return f"❌ Erro ao buscar dashboard. Status: {response.status_code}"

    except Exception as e:
        print(f"[DEBUG] Erro ao buscar dashboard: {e}")
        return f"""❌ **Erro ao carregar dashboard**

**Para resolver**:
- Verifique se configurou seu perfil na aba 'Definir Objetivos'
- Tente novamente em alguns momentos
- Se o problema persistir, reinicie a aplicação

Enquanto isso, posso ajudar com orientações gerais de saúde e bem-estar."""
