"use client";

import { FormEvent, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/state/useAuth";
import { Alert } from "@/components/ui/alert";
import { useDashboard } from "@/hooks/useDashboard";
import Link from "next/link";

export function Dashboard() {
  const { token, isReady: authReady, isLoggingIn, loginError, login } = useAuth();
  const { data: dashboardData, isLoading: isDashboardLoading, error: dashboardError, refetch } = useDashboard();

  const [passkeyInput, setPasskeyInput] = useState("");
  const [localLoginError, setLocalLoginError] = useState<string | null>(null);

  // Handle de login
  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLocalLoginError(null);

    if (!passkeyInput.trim()) {
      setLocalLoginError("Por favor, informe sua chave de acesso");
      return;
    }

    try {
      await login(passkeyInput);
    } catch {
      setLocalLoginError("Erro ao fazer login. Verifique sua chave de acesso.");
    }
  };

  // Se não está logado, mostra tela de login
  if (!authReady || !token) {
    return (
      <main className="flex h-full flex-1 flex-col items-center justify-center gap-8 p-8">
        <div className="flex max-w-md flex-col items-center gap-6 text-center">
          <div className="space-y-2">
            <h1 className="text-3xl font-black uppercase text-white" style={{ fontFamily: "var(--font-condensed)" }}>
              Coach AI
            </h1>
            <p className="text-[#9ba3c0]">
              Acesse sua jornada personalizada de saúde e bem-estar
            </p>
          </div>

          <form onSubmit={handleLogin} className="w-full space-y-4">
            <div>
              <input
                type="password"
                value={passkeyInput}
                onChange={(e) => setPasskeyInput(e.target.value)}
                placeholder="Informe sua chave de acesso"
                disabled={isLoggingIn}
                className="w-full rounded-2xl border border-white/20 bg-white/5 px-4 py-3 text-white placeholder-[#7f8baf] focus:border-[#1086ad] focus:outline-none"
              />
            </div>
            <Button
              type="submit"
              disabled={isLoggingIn}
              className="w-full rounded-2xl bg-[#1086ad] py-3 text-white hover:bg-[#0d6b87]"
            >
              {isLoggingIn ? "Entrando..." : "Entrar"}
            </Button>
          </form>

          {(loginError || localLoginError) && (
            <Alert className="border-red-500/20 bg-red-500/10 text-red-400">
              {loginError || localLoginError}
            </Alert>
          )}
        </div>
      </main>
    );
  }

  // Se há erro ou não há dados ainda
  if (dashboardError) {
    return (
      <main className="flex h-full flex-1 flex-col items-center justify-center gap-6 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-black uppercase text-white mb-2" style={{ fontFamily: "var(--font-condensed)" }}>
            📊 Dashboard
          </h1>
          <p className="text-[#9ba3c0] mb-6">
            Erro ao carregar dashboard
          </p>
          <Alert className="border-red-500/20 bg-red-500/10 text-red-400 mb-6">
            {dashboardError}
          </Alert>
        </div>
        <Button
          onClick={refetch}
          className="rounded-2xl bg-[#1086ad] px-6 py-3 text-white hover:bg-[#0d6b87]"
        >
          Tentar Novamente
        </Button>
      </main>
    );
  }

  if (isDashboardLoading) {
    return (
      <main className="flex h-full flex-1 flex-col items-center justify-center gap-6 p-8">
        <div className="text-center">
          <h1 className="text-3xl font-black uppercase text-white mb-2" style={{ fontFamily: "var(--font-condensed)" }}>
            📊 Dashboard
          </h1>
          <p className="text-[#9ba3c0] mb-6">
            Carregando seus dados...
          </p>
          <div className="flex items-center gap-2 text-[#7f8baf]">
            <div className="h-2 w-2 animate-pulse rounded-full bg-[#1086ad]"></div>
            Preparando seu dashboard personalizado...
          </div>
        </div>
      </main>
    );
  }

  // Interface principal do dashboard
  return (
    <main className="flex h-full flex-1 flex-col">
      {/* Header */}
      <div className="border-b border-white/10 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black uppercase text-white" style={{ fontFamily: "var(--font-condensed)" }}>
              📊 Dashboard
            </h1>
            <p className="text-[#9ba3c0]">
              Olá, {dashboardData?.user_name || "Usuário"}! Sua jornada de saúde e bem-estar
            </p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={refetch}
              disabled={isDashboardLoading}
              className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10"
            >
              🔄 Atualizar
            </Button>
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Perfil e Estatísticas Rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card do Perfil */}
          <Card className="border-white/10 bg-white/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>👤</span>
                Seu Perfil
              </h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-[#dfdecf]">
                <p><strong>Nome:</strong> {dashboardData?.user_name}</p>
                <p><strong>Idade:</strong> {dashboardData?.user_age} anos</p>
                <p><strong>Peso:</strong> {dashboardData?.user_weight} kg</p>
              </div>
              <div className="pt-2 border-t border-white/10">
                <p className="text-xs text-[#9ba3c0]">Objetivos:</p>
                <p className="text-sm text-[#dfdecf]">
                  {dashboardData?.user_goals || "Nenhum objetivo definido"}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Card de Estatísticas */}
          <Card className="border-white/10 bg-white/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>📈</span>
                Estatísticas
              </h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-[#dfdecf] space-y-2">
                <div className="flex justify-between">
                  <span>Perfil:</span>
                  <span className="text-[#1086ad] font-semibold">
                    {dashboardData?.has_profile ? "Ativo" : "Incompleto"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Entradas hoje:</span>
                  <span>{dashboardData?.entries_today || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className={dashboardData?.progress_status === "on_track" ? "text-green-400" : dashboardData?.progress_status === "behind" ? "text-yellow-400" : "text-red-400"}>
                    {dashboardData?.progress_status || "N/A"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Card de Status Nutricional */}
          <Card className="border-white/10 bg-white/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>🍽️</span>
                Nutrição Hoje
              </h3>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-[#dfdecf] space-y-2">
                <div className="flex justify-between">
                  <span>Meta calórica:</span>
                  <span>{dashboardData?.caloric_goal || 0} kcal</span>
                </div>
                <div className="flex justify-between">
                  <span>Consumidas:</span>
                  <span className="text-[#1086ad]">{dashboardData?.calories_consumed || 0} kcal</span>
                </div>
                <div className="flex justify-between">
                  <span>Restantes:</span>
                  <span className={dashboardData?.calories_remaining && dashboardData.calories_remaining > 0 ? "text-green-400" : "text-red-400"}>
                    {dashboardData?.calories_remaining || 0} kcal
                  </span>
                </div>
              </div>
              {dashboardData?.progress_percentage !== undefined && (
                <div className="pt-2">
                  <div className="flex justify-between text-xs text-[#9ba3c0] mb-1">
                    <span>Progresso</span>
                    <span>{dashboardData.progress_percentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div
                      className="bg-[#1086ad] h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(dashboardData.progress_percentage, 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Insights e Mensagens Motivacionais */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Mensagem Motivacional */}
          <Card className="border-white/10 bg-gradient-to-br from-[#1086ad]/20 to-[#1086ad]/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>💪</span>
                Mensagem Motivacional
              </h3>
            </CardHeader>
            <CardContent>
              <p className="text-[#dfdecf] text-sm leading-relaxed">
                {dashboardData?.ai_motivation || "Continue sua jornada! Cada passo conta para alcançar seus objetivos."}
              </p>
            </CardContent>
          </Card>

          {/* Dica de Saúde */}
          <Card className="border-white/10 bg-gradient-to-br from-green-500/20 to-green-500/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>💡</span>
                Dica de Saúde
              </h3>
            </CardHeader>
            <CardContent>
              <p className="text-[#dfdecf] text-sm leading-relaxed">
                {dashboardData?.quick_tip || "Beba água regularmente ao longo do dia para manter-se hidratado e auxiliar no metabolismo."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Projeção da Meta */}
        {dashboardData?.progress_status && (
          <Card className="border-white/10 bg-white/5">
            <CardHeader>
              <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                <span>📈</span>
                Projeção da sua Meta
              </h3>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-[#dfdecf] space-y-4">
                {/* Estimativa baseada no objetivo */}
                <div className="p-3 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">🎯</span>
                    <span className="font-semibold text-white">
                      {dashboardData.user_goals.includes("emagrecimento") ? "Meta de Emagrecimento" :
                       dashboardData.user_goals.includes("ganho") ? "Meta de Ganho de Peso" :
                       "Meta de Manutenção"}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed">
                    {dashboardData.user_goals.includes("emagrecimento") ? (
                      dashboardData.progress_status === "on_track" ?
                        "🔥 Mantendo esse ritmo, você pode perder até 0,5kg esta semana! Continue assim." :
                      dashboardData.progress_status === "ahead" ?
                        "⚡ Excelente! No ritmo atual, você pode perder 0,5-0,7kg esta semana." :
                      dashboardData.progress_status === "behind" ?
                        "📊 Ajuste necessário: mantenha o déficit calórico para perder 0,3-0,5kg esta semana." :
                        "⚠️ Meta calórica excedida. Foque em refeições mais leves nos próximos dias."
                    ) : dashboardData.user_goals.includes("ganho") ? (
                      dashboardData.progress_status === "on_track" ?
                        "💪 Perfeito! Continue assim e você pode ganhar 0,3-0,5kg de massa esta semana." :
                      dashboardData.progress_status === "ahead" ?
                        "🌟 Excelente! No ritmo atual, ganho de 0,4-0,6kg esta semana é possível." :
                      dashboardData.progress_status === "behind" ?
                        "📈 Aumente a ingestão calórica para atingir ganho de 0,2-0,4kg esta semana." :
                        "🎯 Meta atingida! Mantenha o equilíbrio para ganho saudável de massa."
                    ) : (
                      dashboardData.progress_status === "on_track" ?
                        "⚖️ Perfeito! Você está mantendo seu peso atual com sucesso." :
                      dashboardData.progress_status === "ahead" ?
                        "✅ Bom controle! Continue assim para manter seu peso estável." :
                      dashboardData.progress_status === "behind" ?
                        "📊 Aumente um pouco a ingestão para manter seu peso atual." :
                        "⚠️ Está comendo um pouco além do necessário para manutenção."
                    )}
                  </p>
                </div>

                {/* Tendência semanal */}
                <div className="pt-2 border-t border-white/10">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-[#9ba3c0]">Tendência semanal</span>
                    <span className={`text-xs font-semibold ${
                      dashboardData.progress_status === "on_track" || dashboardData.progress_status === "ahead" ?
                      "text-green-400" : "text-yellow-400"
                    }`}>
                      {dashboardData.progress_status === "on_track" ? "📈 No caminho" :
                       dashboardData.progress_status === "ahead" ? "🚀 Acelerado" :
                       dashboardData.progress_status === "behind" ? "🔄 Ajustar" :
                       "⚠️ Atenção"}
                    </span>
                  </div>
                  <p className="text-xs text-[#9ba3c0]">
                    Baseado no seu progresso de hoje • {dashboardData?.current_date || new Date().toLocaleDateString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <Card className="border-white/10 bg-white/5">
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">
              Ações Rápidas
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Link
                href="/calculadora"
                className="flex flex-col items-center gap-2 rounded-xl border border-white/20 bg-white/5 p-4 text-center transition hover:bg-white/10"
              >
                <span className="text-2xl">📸</span>
                <span className="text-xs font-medium text-[#dfdecf]">Analisar Alimento</span>
              </Link>
              <Link
                href="/receitas"
                className="flex flex-col items-center gap-2 rounded-xl border border-white/20 bg-white/5 p-4 text-center transition hover:bg-white/10"
              >
                <span className="text-2xl">🥗</span>
                <span className="text-xs font-medium text-[#dfdecf]">Receitas</span>
              </Link>
              <Link
                href="/personal-trainer"
                className="flex flex-col items-center gap-2 rounded-xl border border-white/20 bg-white/5 p-4 text-center transition hover:bg-white/10"
              >
                <span className="text-2xl">🏋️</span>
                <span className="text-xs font-medium text-[#dfdecf]">Treinos</span>
              </Link>
              <Link
                href="/objetivos"
                className="flex flex-col items-center gap-2 rounded-xl border border-white/20 bg-white/5 p-4 text-center transition hover:bg-white/10"
              >
                <span className="text-2xl">⚙️</span>
                <span className="text-xs font-medium text-[#dfdecf]">Objetivos</span>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}