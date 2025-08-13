'use client';

import React, { useState, useEffect } from 'react';

interface DynamicIslandProps {
  className?: string;
  variant?: 'fixed' | 'inline';
  children?: React.ReactNode;
}

export default function DynamicIsland({ 
  className = '', 
  variant = 'inline',
  children 
}: DynamicIslandProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeString = now.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
      });
      setCurrentTime(timeString);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  const baseStyles = `
    relative flex items-center justify-between
    h-[50px] bg-black text-white px-5 cursor-pointer box-border
    transition-[width] duration-500 ease-[cubic-bezier(0.68,-0.6,0.32,1.6)]
    rounded-bl-[20px] rounded-br-[20px]
    ${isExpanded ? 'w-[400px]' : 'w-[250px]'}
    ${variant === 'fixed' ? 'fixed top-10 left-1/2 transform -translate-x-1/2 z-50' : ''}
    ${className}
  `;

  return (
    <>
      <div 
        className={baseStyles}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {/* Curva esquerda - usando radial-gradient exatamente como no exemplo */}
        <div 
          className="absolute top-0 right-full w-[18px] h-[18px]"
          style={{
            background: 'radial-gradient(circle at 0% 100%, transparent 18px, black calc(18px + 0.5px))'
          }}
        />
        
        {/* Curva direita - usando radial-gradient exatamente como no exemplo */}
        <div 
          className="absolute top-0 left-full w-[18px] h-[18px]"
          style={{
            background: 'radial-gradient(circle at 100% 100%, transparent 18px, black calc(18px + 0.5px))'
          }}
        />

        {/* Conteúdo da ilha */}
        {children || (
          <div className="flex items-center justify-center w-full">
            <div className="text-white font-medium text-sm">
              {currentTime}
            </div>
          </div>
        )}

      </div>
    </>
  );
}