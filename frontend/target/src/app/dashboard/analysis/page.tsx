"use client";
import { useState, useEffect } from "react";
import withAuth from "@/components/auth/withAuth";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from 'next/navigation';

interface Analysis {
  id: number;
  description: string;
  status: string;
  created_at: string;
}

function AnalysisListPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (token) {
      const fetchAnalyses = async () => {
        try {
          const res = await fetch("http://localhost:8000/api/v1/analysis", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || "Erro ao buscar análises");
          }
          const data = await res.json();
          setAnalyses(data);
        } catch (e: any) {
          setError(e.message);
        }
      };
      fetchAnalyses();
    }
  }, [token]);

  return (
    <main className="p-8" style={{ color: 'var(--text-primary)'}}>
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Análises Realizadas</h1>
        <button 
          onClick={() => router.push('/dashboard/analysis/create')}
          className="btn btn-primary"
        >
          + Iniciar Nova Análise
        </button>
      </header>

      {error && <p className="error-message text-center mb-4">Erro: {error}</p>}

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th className="table-header">ID</th>
              <th className="table-header">Descrição</th>
              <th className="table-header">Status</th>
              <th className="table-header">Data de Criação</th>
            </tr>
          </thead>
          <tbody>
            {analyses.length > 0 ? (
              analyses.map((analysis) => (
                <tr key={analysis.id}>
                  <td className="table-cell font-medium">{analysis.id}</td>
                  <td className="table-cell">{analysis.description}</td>
                  <td className="table-cell">
                    <span className={`status-badge status-${analysis.status?.toLowerCase() || 'default'}`}>
                      {analysis.status}
                    </span>
                  </td>
                  <td className="table-cell">{new Date(analysis.created_at).toLocaleString()}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="table-cell text-center" style={{ color: 'var(--text-muted)'}}>
                  Nenhuma análise encontrada.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

export default withAuth(AnalysisListPage);
