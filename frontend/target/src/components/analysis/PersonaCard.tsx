import React from 'react';

interface Persona {
  id: number;
  name: string;
  description: string;
  // Futuramente, podemos adicionar mais campos como: demographics, goals, frustrations, etc.
}

interface PersonaCardProps {
  persona: Persona;
}

const PersonaCard: React.FC<PersonaCardProps> = ({ persona }) => {
  return (
    <div 
      className="p-6 rounded-lg flex flex-col h-full"
      style={{
        backgroundColor: 'var(--bg-secondary)', 
        border: '1px solid var(--border-primary)',
        color: 'var(--text-primary)'
      }}
    >
      <h3 className="text-xl font-bold mb-3" style={{ color: 'var(--accent-primary)'}}>{persona.name}</h3>
      <p className="text-base" style={{ color: 'var(--text-secondary)'}}>
        {persona.description}
      </p>
      {/* Espaço reservado para futuros elementos como gráficos ou listas */}
    </div>
  );
};

export default PersonaCard;
