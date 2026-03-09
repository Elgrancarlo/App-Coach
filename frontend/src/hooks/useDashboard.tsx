import { useState, useEffect } from "react";
import { useAuth } from "@/state/useAuth";

interface DashboardData {
  // Dados do usuário
  user_name: string;
  user_age: number;
  user_weight: number;
  user_goals: string;
  has_profile: boolean;

  // Dados nutricionais
  caloric_goal: number;
  calories_consumed: number;
  calories_remaining: number;
  progress_percentage: number;

  // Macronutrientes
  total_proteins: number;
  total_carbs: number;
  total_fats: number;

  // Status e contadores
  entries_today: number;
  diary_updated_today: boolean;
  current_date: string;

  // Insights e motivação
  progress_status: string;
  ai_motivation: string;
  quick_tip: string;
}

export function useDashboard() {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    if (!token) {
      setError("Token de autenticação não encontrado");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch("http://localhost:8000/api/dashboard/overview", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`Erro ao carregar dashboard: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      console.error("Erro no dashboard:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchDashboardData
  };
}