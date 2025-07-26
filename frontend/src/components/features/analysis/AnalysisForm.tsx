import React from "react";

const AnalysisForm: React.FC = () => {
  return (
    <form>
      <h2>Análise</h2>
      {/* Campos do formulário */}
      <input type="text" placeholder="Nome da análise" />
      <button type="submit">Enviar</button>
    </form>
  );
};

export default AnalysisForm;
