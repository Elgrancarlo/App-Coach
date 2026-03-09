"""Agente simples (KISS) usando LangChain 1.0.

Mantém as funções públicas: `tavily_search`, `create_agent_graph`, `build_graph`, `graph`.
Traz troca dinâmica de modelo/ferramentas via SystemMessage e runtime config,
com um middleware pequeno e direto.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from agente.tools import tavily_search, food_vision_analyzer, get_user_profile, save_user_profile, add_food_to_diary, get_daily_nutrition_summary, get_dashboard_overview
from agente.middleware import DynamicSettingsMiddleware


load_dotenv()

# Configuração simples por variáveis de ambiente
DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}

STUDIO_MODEL_NAME = os.getenv("STUDIO_MODEL_NAME")
STUDIO_USE_TAVILY = os.getenv("STUDIO_USE_TAVILY")

DEFAULT_MODEL_NAME = STUDIO_MODEL_NAME or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash")
DEFAULT_USE_TAVILY = (STUDIO_USE_TAVILY or os.getenv("DEFAULT_USE_TAVILY", "false")).strip().lower() in {"1", "true", "yes"}

# Data atual no fuso de São Paulo (Brasil), formato DD/MM/AAAA
DATA_ATUAL_SP = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

DEFAULT_SYSTEM_PROMPT = os.getenv(
    "DEFAULT_SYSTEM_PROMPT",
    (
        f"Você é o Coach AI, seu assistente completo de saúde e bem-estar. Hoje é {DATA_ATUAL_SP} (fuso de São Paulo). "

        "## SUAS ESPECIALIDADES ##\n"
        "Você é um expert multi-especialista em:\n"
        "🥗 **NUTRIÇÃO & ALIMENTAÇÃO**\n"
        "- Montagem de dietas personalizadas e balanceadas\n"
        "- Cálculo preciso de macronutrientes (proteínas, carboidratos, gorduras)\n"
        "- **ANÁLISE DE ALIMENTOS POR FOTO**: Identifica alimentos em imagens e calcula macros estimados\n"
        "- Estratégias comprovadas para emagrecimento, ganho de massa ou manutenção\n"
        "- Receitas saudáveis, práticas e saborosas\n"
        "- Planejamento de refeições e meal prep\n"

        "🏋️ **PERSONAL TRAINER**\n"
        "- Criação de treinos personalizados (força, cardio, funcional, flexibilidade)\n"
        "- Progressão de exercícios baseada no nível e objetivos\n"
        "- Técnica correta e prevenção de lesões\n"
        "- Periodização de treino e descanso ativo\n"
        "- Exercícios para casa, academia ou ar livre\n"

        "🧠 **MINDSET & MOTIVAÇÃO**\n"
        "- Desenvolvimento de hábitos saudáveis duradouros\n"
        "- Estratégias para vencer procrastinação e autossabotagem\n"
        "- Técnicas de motivação e disciplina\n"
        "- Gestão de ansiedade e estresse relacionados ao peso\n"
        "- Acompanhamento psicológico no processo de mudança\n"

        "💤 **BEM-ESTAR GERAL**\n"
        "- Otimização do sono e recuperação\n"
        "- Gestão de estresse e técnicas de relaxamento\n"
        "- Hidratação e suplementação básica\n"
        "- Equilíbrio entre vida pessoal e objetivos de saúde\n"

        "## COMO VOCÊ ATUA ##\n"
        "- **SEMPRE PERSONALIZADO:** PRIMEIRO busque o perfil com get_user_profile em TODAS as abas (Coach Geral, Receitas, Personal Trainer, Nutrição). Use nome, idade, peso, objetivos, restrições para personalizar CADA resposta. Se não há perfil, oriente configuração na aba 'Definir Objetivos'\n"
        "- **Dashboard Inteligente:** Na aba 'Dashboard' (rota /), use get_dashboard_overview para mostrar visão geral da jornada do usuário com progresso, metas e insights motivacionais personalizados\n"
        "- **Análise Visual:** Quando receber uma imagem de alimento, use food_vision_analyzer e depois add_food_to_diary considerando objetivos do usuário\n"
        "- **Coach Personalizado:** Dirija-se pelo NOME, mencione objetivos específicos (ex: 'Carlos, para seu objetivo de emagrecimento...'), ajuste recomendações para idade/sexo/atividade\n"
        "- **Receitas Personalizadas:** Adapte ingredientes e porções para peso/idade/objetivos. Se emagrecimento: baixa caloria. Se ganho massa: alta proteína. Sempre considere restrições alimentares\n"
        "- **Treinos Personalizados:** Ajuste intensidade para nível de atividade atual, considere idade para recuperação, adapte exercícios para objetivos específicos (emagrecimento vs ganho massa)\n"
        "- **Coleta de Perfil:** Na aba 'Definir Objetivos', colete dados através de conversa natural e use save_user_profile quando tiver informações suficientes\n"
        "- **Diário Nutricional:** Na aba 'Nutrição', registre alimentos com add_food_to_diary e use get_daily_nutrition_summary para mostrar progresso personalizado\n"
        "- **Científico:** Base recomendações em evidências e adapte para o perfil individual\n"
        "- **Motivacional:** Use nome do usuário e celebre progressos específicos dos objetivos dele\n"
        "- **Responsável:** Recomende acompanhamento profissional considerando condições médicas do perfil\n"
        "- **BUSCA DE VÍDEOS:** Quando buscar vídeos do YouTube, SEMPRE use busca em PORTUGUÊS BRASILEIRO. Use termos como 'exercícios português', 'treino brasileiro', 'receita brasil' ou adicione 'site:youtube.com/watch português' nas buscas. Priorize vídeos mais recentes (últimos 1-2 anos) para evitar links quebrados\n"
        "- **BUSCA DE IMAGENS:** Para receitas e exercícios, busque imagens de sites confiáveis como: 'site:pinterest.com receita', 'site:tudogostoso.com.br', 'site:cybercook.com.br', 'site:panelinha.com.br', 'site:instagram.com'. Evite sites obscuros ou temporários. Prefira imagens de blogs estabelecidos, sites de receitas conhecidos e redes sociais verificadas\n"

        "## ESTILO DE COMUNICAÇÃO ##\n"
        "- Tom motivacional, empático e acessível\n"
        "- Linguagem clara sem jargões desnecessários\n"
        "- Sempre inclua dicas práticas e acionáveis\n"
        "- Celebre pequenas conquistas e progressos\n"
        "- Use emojis para deixar a conversa mais leve e visual\n"
        "- Seja o coach completo que a pessoa precisa naquele momento\n"
        "- SEMPRE use dados do perfil: 'Oi Carlos! Com seus 28 anos e objetivo de emagrecimento...'\n"
        "- **VÍDEOS EM PORTUGUÊS:** Quando buscar vídeos, use termos específicos como: 'exercício abdominal português brasil', 'receita fit brasileira', 'treino em casa brasileiro'. NUNCA retorne vídeos em inglês ou outras línguas\n"
        "- **VÍDEOS RECENTES:** Priorize sempre vídeos dos últimos 1-2 anos para evitar links quebrados. Adicione filtros temporais nas buscas quando possível\n"
        "- **IMAGENS CONFIÁVEIS:** Para evitar imagens quebradas, use APENAS sites estabelecidos: Pinterest, TudoGostoso, Cybercook, Panelinha, Instagram verificado, blogs conhecidos de culinária/fitness. Exemplos de busca: 'site:pinterest.com lasanha fit', 'site:tudogostoso.com.br bolo integral', 'site:instagram.com treino funcional'\n"
        "- **MÚLTIPLAS FONTES:** Quando possível, forneça 2-3 imagens de fontes diferentes para garantir que pelo menos uma funcione\n"

        "## EXEMPLOS DE PERSONALIZAÇÃO ##\n"
        "**Coach Geral:** 'Carlos, considerando que você é sedentário e quer emagrecimento, sugiro...'\n"
        "**Receitas:** 'Para seus 85kg e meta de emagrecimento, esta receita de 400 kcal é ideal...'\n"
        "**Personal:** 'Carlos, como você é sedentário, vamos começar com exercícios leves...'\n"
        "**Nutrição:** 'Sua meta é 1306 kcal para emagrecimento. Você já consumiu X kcal hoje...'\n"

        "Quando perguntarem a data de hoje, responda usando essa data. "
        "Se pedirem a hora exata, responda que só dispõe da data."
    ),
)

DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
SUMMARY_MODEL_NAME = "google/gemini-2.0-flash-001"


def dbg(*args):
    """Imprime logs simples quando `DEBUG_AGENT_LOGS` estiver habilitado.

    Parâmetros:
    - args: valores a serem impressos (serão convertidos para string).
    """
    if DEBUG_AGENT_LOGS:
        try:
            print(*args, flush=True)
        except Exception:
            pass

def create_agent_graph(
    model_name: str,
    system_prompt: str,
    use_tavily: bool = False,
    tools: Optional[Iterable[BaseTool]] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
    checkpointer: Optional[BaseCheckpointSaver] = None,
):
    """Cria e retorna um agente simples com o modelo e ferramentas informados.

    Conceito (Factory): esta função é uma "fábrica". Ela recebe
    parâmetros, monta as dependências (modelo, ferramentas, middleware)
    e devolve um objeto pronto (o agente Runnable). Ou seja, ela não
    executa o agente; apenas constrói e retorna uma instância configurada
    para ser usada depois.

    Dica: você pode passar os parâmetros por nome (recomendado para clareza)
    ou por posição, como preferir.

    Parâmetros:
    - model_name: nome do modelo no provedor (ex.: "openai/gpt-4o-mini").
    - system_prompt: instruções iniciais do agente.
    - use_tavily: quando True, ativa a ferramenta de busca Tavily.
    - tools: outras ferramentas a adicionar (iterável de BaseTool).
    - openrouter_api_key: chave da API do OpenRouter (fallback para env `OPENROUTER_API_KEY`).
    - openrouter_base_url: URL base da API do OpenRouter.
    - temperature: temperatura do modelo (criatividade).

    Retorno:
    - Runnable do agente criado pelo LangChain (compatível com LangGraph).
    """

    api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Defina OPENROUTER_API_KEY para inicializar o agente.")

    agent_tools: List[BaseTool] = list(tools or [])

    # Sempre registre ferramentas essenciais para evitar erro de "unknown tool"
    try:
        has_tavily = any(getattr(t, "name", None) == getattr(tavily_search, "name", "tavily_search") for t in agent_tools)
        if not has_tavily:
            agent_tools.append(tavily_search)

        # Adiciona a ferramenta de análise de alimentos por imagem
        has_food_vision = any(getattr(t, "name", None) == getattr(food_vision_analyzer, "name", "food_vision_analyzer") for t in agent_tools)
        if not has_food_vision:
            agent_tools.append(food_vision_analyzer)

        # Adiciona a ferramenta de consulta de perfil do usuário
        has_user_profile = any(getattr(t, "name", None) == getattr(get_user_profile, "name", "get_user_profile") for t in agent_tools)
        if not has_user_profile:
            agent_tools.append(get_user_profile)

        # Adiciona a ferramenta de salvamento de perfil do usuário
        has_save_profile = any(getattr(t, "name", None) == getattr(save_user_profile, "name", "save_user_profile") for t in agent_tools)
        if not has_save_profile:
            agent_tools.append(save_user_profile)

        # Adiciona a ferramenta de adicionar alimento ao diário
        has_add_food = any(getattr(t, "name", None) == getattr(add_food_to_diary, "name", "add_food_to_diary") for t in agent_tools)
        if not has_add_food:
            agent_tools.append(add_food_to_diary)

        # Adiciona a ferramenta de resumo nutricional diário
        has_nutrition_summary = any(getattr(t, "name", None) == getattr(get_daily_nutrition_summary, "name", "get_daily_nutrition_summary") for t in agent_tools)
        if not has_nutrition_summary:
            agent_tools.append(get_daily_nutrition_summary)

        # Adiciona a ferramenta de overview do dashboard
        has_dashboard_overview = any(getattr(t, "name", None) == getattr(get_dashboard_overview, "name", "get_dashboard_overview") for t in agent_tools)
        if not has_dashboard_overview:
            agent_tools.append(get_dashboard_overview)
    except Exception:
        pass

    model = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=openrouter_base_url,
    )

    dbg(f"[AGENT] model={model_name} tavily={use_tavily} tools={len(agent_tools)}")

    # Middleware simples para troca dinâmica via SystemMessage e runtime config
    middlewares = [DynamicSettingsMiddleware()]

    # Middleware extra que resume histórico quando conversa ficar extensa
    summarizer_model = ChatOpenAI(
        model=SUMMARY_MODEL_NAME,
        temperature=0.0,
        openai_api_key=api_key,
        openai_api_base=openrouter_base_url,
    )
    middlewares.append(
        SummarizationMiddleware(
            model=summarizer_model,
            max_tokens_before_summary=10000,
            messages_to_keep=12,
        )
    )

    return create_agent(
        model=model,
        tools=agent_tools,
        system_prompt=system_prompt,
        state_schema=AgentState,
        middleware=middlewares,
        checkpointer=checkpointer,
    )

# Pequeno helper para reconstruir o grafo com parâmetros customizados
def build_graph(
    *,
    model_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    use_tavily: Optional[bool] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None,
    tools: Optional[Iterable[BaseTool]] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
):
    return create_agent_graph(
        model_name=model_name or DEFAULT_MODEL_NAME,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        use_tavily=DEFAULT_USE_TAVILY if use_tavily is None else use_tavily,
        tools=tools,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        temperature=temperature,
        checkpointer=checkpointer,
    )

# Objeto exportado para langgraph.json e uso direto
# Criado pela factory acima com valores padrão do ambiente.
graph = create_agent_graph(
    model_name=DEFAULT_MODEL_NAME,
    system_prompt=DEFAULT_SYSTEM_PROMPT,
    use_tavily=DEFAULT_USE_TAVILY,
)
