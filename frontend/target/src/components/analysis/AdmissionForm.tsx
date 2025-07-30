'use client';

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import useAnalysisStore from '@/store/analysisStore';

export default function AdmissionForm() {
  const [niche, setNiche] = useState('');
  const [description, setDescription] = useState('');
  const router = useRouter();
  const { performAnalysis, isLoading, error } = useAnalysisStore();
  const minChars = 100;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (description.length < minChars || !niche) return; // Safeguard

    await performAnalysis(description, niche);
    
    const currentError = useAnalysisStore.getState().error;
    if (!currentError) {
      router.push('/dashboard/analysis/result');
    }
  };

  const isDescriptionMet = description.length >= minChars;
  const isNicheMet = niche.trim() !== '';
  const isFormReady = isDescriptionMet && isNicheMet;

  return (
    <div className="form-container">
      <h1 className="form-title">Descreva Seu Negócio</h1>
      <p className="text-center mb-4">Para começar, forneça uma descrição detalhada. Nossa IA usará essas informações para identificar seu público-alvo com precisão.</p>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="niche" className="form-label">
            Nicho de Mercado
          </label>
          <input 
            type="text"
            id="niche"
            name="niche"
            className="form-input"
            placeholder="Ex: Cafeterias, Lojas de Roupas, etc."
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>
        <div>
          <label htmlFor="business-description" className="form-label">
            Descrição Detalhada do Negócio
          </label>
          <p className="text-xs text-muted mt-1 mb-2">Para uma análise precisa, descreva seu negócio com o máximo de detalhes possível. (Mínimo de 100 caracteres)</p>
          <textarea
            id="business-description"
            name="business-description"
            rows={8}
            className="form-input"
            placeholder="Ex: Uma cafeteria gourmet no coração da cidade, especializada em grãos de origem única e métodos de extração artesanais..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            disabled={isLoading}
          />
          <div className="text-right text-sm mt-2">
            <span style={{ color: isDescriptionMet ? 'var(--success)' : 'var(--text-muted)' }}>
              {description.length} / {minChars} caracteres
            </span>
          </div>
        </div>
        <div>
          <button
            type="submit"
            className="w-full btn btn-primary"
            disabled={isLoading || !isFormReady}
          >
            {isLoading ? 'Analisando...' : 'Gerar Análise'}
          </button>
        </div>
        {error && <p className="error-message text-center mt-4">{error}</p>}
      </form>
    </div>
  );
}
