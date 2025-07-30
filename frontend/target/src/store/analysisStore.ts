import { create } from 'zustand';

interface AnalysisState {
  isLoading: boolean;
  error: string | null;
  analysisResult: any; 
  loadingStage: string;
  niche: string | null;
  performAnalysis: (description: string, niche: string) => Promise<void>;
}

const analysisStages = [
  "Normalizando e preparando seu texto...",
  "Extraindo conceitos-chave e entidades...",
  "Analisando o significado semântico...",
  "Cruzando informações com dados de mercado...",
  "Construindo os arquétipos de público-alvo... Quase pronto!"
];

const useAnalysisStore = create<AnalysisState>((set) => ({
  isLoading: false,
  error: null,
  analysisResult: null,
  loadingStage: '',
  niche: null,
  performAnalysis: async (description: string, niche: string) => {
    set({ isLoading: true, error: null, analysisResult: null, niche });
    try {
      for (let i = 0; i < analysisStages.length; i++) {
        set({ loadingStage: analysisStages[i] });
        await new Promise(resolve => setTimeout(resolve, 800)); // Loader mais rápido
      }
      // Validação dos dados antes de enviar
      if (!niche || niche.length < 3) {
        throw new Error('O nicho deve ter no mínimo 3 caracteres.');
      }
      if (niche.length > 100) {
        throw new Error('O nicho não pode ter mais que 100 caracteres.');
      }
      if (!description || description.length < 100) {
        throw new Error('A descrição deve ter no mínimo 100 caracteres.');
      }

      // Formatação dos dados conforme o schema do backend
      const analysisData = {
        niche: niche.trim(),
        description: description.trim()
      };

      // Log detalhado para depuração
      console.log('Enviando dados para a API:', {
        url: "http://localhost:8000/api/v1/analysis/",
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: analysisData
      });

      const response = await fetch("http://localhost:8000/api/v1/analysis/", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(analysisData)
      });

      // Log da resposta bruta
      console.log('Status da resposta:', response.status, response.statusText);
      
      // Tentar ler o corpo da resposta mesmo em caso de erro
      let responseBody;
      try {
        responseBody = await response.clone().json();
        console.log('Corpo da resposta:', responseBody);
      } catch (e) {
        console.error('Erro ao ler corpo da resposta:', e);
        responseBody = await response.text();
        console.log('Resposta como texto:', responseBody);
      }

      if (!response.ok) {
        throw new Error("Erro ao processar análise: " + response.statusText + ' - ' + JSON.stringify(responseBody));
      }
      
      const data = responseBody;
      set({ analysisResult: data, isLoading: false, loadingStage: '' });
    } catch (error: any) {
      console.error('Erro na análise:', error);
      set({ error: error.message || 'Ocorreu um erro ao analisar a descrição. Tente novamente.', isLoading: false, loadingStage: '' });
    }
  },
}));

export default useAnalysisStore;
