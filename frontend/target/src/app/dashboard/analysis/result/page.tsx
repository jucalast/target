

'use client';

import useAnalysisStore from '@/store/analysisStore';
import { useEffect } from 'react';
import MultiStageLoader from '@/components/analysis/MultiStageLoader';
import PersonaCard from '@/components/analysis/PersonaCard';

export default function AnalysisResultPage() {
  const { analysisResult, isLoading, error, niche } = useAnalysisStore();

  useEffect(() => {
    // Mock data for demonstration purposes if not available from store
    if (!analysisResult && !isLoading) {
      useAnalysisStore.setState({
        analysisResult: {
          personas: [
            { id: 1, name: 'O Profissional Remoto', description: 'Busca conveniência e um ambiente tranquilo para trabalhar.' },
            { id: 2, name: 'O Aficionado por Café', description: 'Valoriza a qualidade do grão e métodos de extração.' },
            { id: 3, name: 'O Estudante Criativo', description: 'Procura um espaço inspirador e acessível para socializar e estudar.' },
          ],
          mainInsight: "O interesse central deste mercado gira em torno de 'sustentabilidade' e 'consumo ético'.",
        },
        niche: 'Cafeterias Gourmet'
      });
    }
  }, [analysisResult, isLoading]);

  if (isLoading) {
    return <MultiStageLoader />;
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen text-center p-4" style={{ backgroundColor: 'var(--bg-primary)'}}>
        <p className="error-message mb-4">Erro: {error}</p>
        <button 
          onClick={() => window.location.href = '/dashboard/analysis/create'}
          className="btn btn-primary"
        >
          Tentar Novamente
        </button>
      </div>
    );
  }

  if (!analysisResult) {
    return null; // Or a loading/empty state
  }

  const { personas = [], mainInsight, keywords, entities, embedding, normalized_text, description } = analysisResult || {};

  return (
    <main className="p-8 bg-[var(--bg-primary)] text-[var(--text-primary)] min-h-screen">
      {/* Barra Superior */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Análise para: <span className="text-[var(--accent-primary)]">{niche || 'seu negócio'}</span></h1>
        <button 
          onClick={() => window.location.href = '/dashboard/analysis/create'}
          className="btn btn-secondary"
        >
          + Nova Análise
        </button>
      </header>

      {/* Conteúdo Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quadrante Superior Esquerdo (Sumário Executivo e Dados Intermediários) */}
        <div className="lg:col-span-1">
          <div className="p-6 rounded-lg space-y-6 bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
            <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">Sumário Executivo</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-[var(--text-muted)]">Perfis Identificados</p>
                <p className="text-2xl font-bold text-[var(--accent-primary)]">{personas.length}</p>
              </div>
              <div>
                <p className="text-sm text-[var(--text-muted)]">Principal Insight</p>
                <p>{mainInsight}</p>
              </div>
            </div>
            {/* Dados Intermediários */}
            {keywords && keywords.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-muted)'}}>Palavras-chave extraídas:</p>
                <div className="flex flex-wrap gap-2">
                  {keywords.map((kw: string, i: number) => (
                    <span key={i} className="px-2 py-1 rounded bg-blue-100 text-blue-800 text-xs font-semibold">{kw}</span>
                  ))}
                </div>
              </div>
            )}
            {entities && entities.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-1 mt-4" style={{ color: 'var(--text-muted)'}}>Entidades reconhecidas:</p>
                <ul className="text-xs space-y-1">
                  {entities.map((ent: any, i: number) => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-green-100 text-green-800 font-mono">{ent.text}</span>
                      <span className="bg-gray-200 px-1.5 py-0.5 rounded text-gray-700">{ent.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {normalized_text && (
              <div>
                <p className="text-sm font-medium mb-1 mt-4" style={{ color: 'var(--text-muted)'}}>Texto Normalizado:</p>
                <p className="text-xs bg-gray-50 p-2 rounded border border-gray-200 font-mono break-words">{normalized_text}</p>
              </div>
            )}
            {embedding && Array.isArray(embedding) && embedding.length > 0 && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm font-medium mb-1" style={{ color: 'var(--text-muted)'}}>Ver embedding (vetor)</summary>
                <div className="text-xs bg-gray-50 p-2 rounded border border-gray-200 font-mono break-all max-h-32 overflow-auto">
                  [{embedding.slice(0, 10).map((v: number) => v.toFixed(4)).join(', ')}{embedding.length > 10 ? ', ...' : ''}]
                </div>
              </details>
            )}
          </div>
        </div>

        {/* Seção de Dados da Análise */}
      <div className="lg:col-span-2 space-y-8">
        {/* Seção de Palavras-chave e Entidades */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Palavras-chave */}
          {keywords && keywords.length > 0 && (
            <div className="p-6 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
              <h3 className="text-lg font-semibold mb-3 text-[var(--text-primary)]">Palavras-chave Extraídas</h3>
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw: string, i: number) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] text-sm font-medium">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Entidades */}
          {entities && entities.length > 0 && (
            <div className="p-6 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
              <h3 className="text-lg font-semibold mb-3 text-[var(--text-primary)]">Entidades Reconhecidas</h3>
              <div className="space-y-2">
                {entities.map((ent: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-[var(--bg-tertiary)] p-2 rounded">
                    <span className="font-medium text-[var(--text-primary)]">{ent.text}</span>
                    <span className="text-xs bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] px-2 py-1 rounded-full">{ent.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Seção de Texto Normalizado */}
        {normalized_text && (
          <div className="p-6 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
            <h3 className="text-lg font-semibold mb-3 text-[var(--text-primary)]">Texto Normalizado</h3>
            <p className="text-sm text-[var(--text-secondary)] bg-[var(--bg-tertiary)] p-4 rounded font-mono">{normalized_text}</p>
          </div>
        )}

        {/* Seção de Embedding */}
        {embedding && Array.isArray(embedding) && embedding.length > 0 && (
          <div className="p-6 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
            <h3 className="text-lg font-semibold mb-3 text-[var(--text-primary)]">Vetor de Embedding</h3>
            <div className="text-xs bg-[var(--bg-tertiary)] p-3 rounded font-mono overflow-x-auto text-[var(--text-secondary)]">
              <p>Dimensões: {embedding.length}</p>
              <p className="mt-2">Primeiros valores: [{embedding.slice(0, 5).map((v: number) => v.toFixed(4)).join(', ')}...]</p>
            </div>
          </div>
        )}

        {/* Seção de Personas */}
        {personas && personas.length > 0 && (
          <div>
            <h3 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">Personas Identificadas</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {personas.map((persona: any) => (
                <PersonaCard key={persona.id} persona={persona} />
              ))}
            </div>
          </div>
        )}
      </div>
      </div>
    </main>
  );
}
