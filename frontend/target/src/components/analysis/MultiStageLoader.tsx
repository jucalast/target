'use client';

import React, { useState, useEffect } from 'react';
import useAnalysisStore from '@/store/analysisStore';

const marketingTips = [
  "Sabia que? Perfis de público-alvo baseados em comportamento são até 80% mais eficazes do que os baseados apenas em demografia.",
  "Dica: Testes A/B em suas campanhas de marketing podem aumentar as taxas de conversão em mais de 40%.",
  "Insight: 88% dos consumidores pesquisam produtos online antes de comprar em uma loja física. Sua presença digital é sua vitrine.",
  "Fato: Empresas que utilizam análise de dados para tomar decisões são 5% mais produtivas e 6% mais lucrativas.",
  "Lembre-se: O custo de adquirir um novo cliente é 5 vezes maior do que o de reter um cliente existente. Fidelize!"
];

const MultiStageLoader = () => {
  const { loadingStage } = useAnalysisStore();
  const [currentTip, setCurrentTip] = useState('');

  useEffect(() => {
    // Seleciona uma nova dica sempre que o estágio de carregamento muda
    const randomIndex = Math.floor(Math.random() * marketingTips.length);
    setCurrentTip(marketingTips[randomIndex]);
  }, [loadingStage]);

  return (
    <div 
      className="flex flex-col items-center justify-center min-h-screen text-center p-4"
      style={{ backgroundColor: 'var(--bg-primary)' }}
    >
      <div className="w-full max-w-md">
        <div className="relative w-24 h-24 mx-auto mb-6">
          <div 
            className="absolute inset-0 border-4 rounded-full"
            style={{ borderColor: 'var(--border-primary)' }}
          ></div>
          <div 
            className="absolute inset-0 border-4 border-t-transparent rounded-full animate-spin"
            style={{ borderTopColor: 'var(--accent-primary)' }}
          ></div>
        </div>
        <h1 
          className="text-2xl font-semibold mb-2"
          style={{ color: 'var(--text-primary)' }}
        >
          Analisando seu negócio...
        </h1>
        <p 
          className="text-lg transition-opacity duration-500 ease-in-out mb-8"
          style={{ color: 'var(--text-secondary)' }}
        >
          {loadingStage}
        </p>

        {currentTip && (
          <div className="tip-container p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)'}}>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{currentTip}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiStageLoader;
