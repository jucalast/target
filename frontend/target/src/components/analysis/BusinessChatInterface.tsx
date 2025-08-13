'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Message {
  id: number;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
}

export default function BusinessChatInterface() {
  const router = useRouter();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      type: 'bot',
      content: 'Olá Luccas, tudo bem? nessa etapa, preciso que você me conte sobre o seu negócio',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showTypingEffect, setShowTypingEffect] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [selectionStart, setSelectionStart] = useState(0);
  const [selectionEnd, setSelectionEnd] = useState(0);
  const [isMouseDown, setIsMouseDown] = useState(false);

  // Auto focus no input quando componente carrega
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
      setCursorPosition(inputValue.length);
    }
  }, []);

  // Atualiza posição do cursor quando input muda
  useEffect(() => {
    setCursorPosition(inputValue.length);
  }, [inputValue]);

  // Função para capturar mudanças na posição do cursor
  const handleCursorChange = () => {
    if (textareaRef.current) {
      const start = textareaRef.current.selectionStart || 0;
      const end = textareaRef.current.selectionEnd || 0;
      setCursorPosition(start);
      setSelectionStart(start);
      setSelectionEnd(end);
    }
  };

  // Função para calcular posição do cursor baseada na coordenada do mouse
  const getCharacterIndex = (element: HTMLElement, x: number) => {
    const text = inputValue;
    if (!text) return 0;
    
    const style = window.getComputedStyle(element);
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) return 0;
    
    // Define a mesma fonte do elemento com as propriedades corretas
    const fontSize = '1.125rem'; // 18px
    const fontFamily = 'Consolas, "Courier New", Monaco, monospace';
    context.font = `400 ${fontSize} ${fontFamily}`;
    
    console.log('Text to measure:', text, 'Mouse x:', x);
    
    let totalWidth = 0;
    for (let i = 0; i < text.length; i++) {
      const charWidth = context.measureText(text[i]).width;
      console.log(`Char ${i} "${text[i]}": width=${charWidth}, totalWidth=${totalWidth}`);
      
      if (totalWidth + charWidth / 2 > x) {
        console.log(`Returning index ${i} at totalWidth ${totalWidth}`);
        return i;
      }
      totalWidth += charWidth;
    }
    
    console.log(`Returning final index ${text.length} at totalWidth ${totalWidth}`);
    return text.length;
  };

  // Eventos de mouse para seleção
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    console.log('Mouse down event triggered');
    e.preventDefault();
    e.stopPropagation();
    
    setIsMouseDown(true);
    const rect = e.currentTarget.getBoundingClientRect();
    
    // Como o texto está alinhado à direita, precisamos ajustar o cálculo
    const containerWidth = rect.width;
    const mouseX = e.clientX - rect.left;
    
    let index = 0;
    
    // Calcular largura total do texto
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (context) {
      context.font = '400 1.125rem Consolas, "Courier New", Monaco, monospace';
      const textWidth = context.measureText(inputValue).width;
      
      // Ajustar x para começar do início do texto (que está à direita)
      const textStartX = containerWidth - textWidth;
      const adjustedX = mouseX - textStartX;
      
      console.log('Container width:', containerWidth, 'Text width:', textWidth, 'Mouse X:', mouseX, 'Adjusted X:', adjustedX);
      
      index = getCharacterIndex(e.currentTarget, Math.max(0, adjustedX));
      
      console.log('Character index:', index, 'at adjusted x:', adjustedX);
    }
    
    setCursorPosition(index);
    setSelectionStart(index);
    setSelectionEnd(index);
    
    // Sincronizar com textarea
    if (textareaRef.current) {
      textareaRef.current.focus();
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.setSelectionRange(index, index);
        }
      }, 0);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isMouseDown) return;
    
    console.log('Mouse move event triggered');
    e.preventDefault();
    
    const rect = e.currentTarget.getBoundingClientRect();
    const containerWidth = rect.width;
    const mouseX = e.clientX - rect.left;
    
    let index = 0;
    
    // Calcular largura total do texto
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (context) {
      context.font = '400 1.125rem Consolas, "Courier New", Monaco, monospace';
      const textWidth = context.measureText(inputValue).width;
      
      // Ajustar x para começar do início do texto (que está à direita)
      const textStartX = containerWidth - textWidth;
      const adjustedX = mouseX - textStartX;
      
      index = getCharacterIndex(e.currentTarget, Math.max(0, adjustedX));
    }
    
    setSelectionEnd(index);
    setCursorPosition(index);
    
    // Sincronizar com textarea
    if (textareaRef.current) {
      textareaRef.current.setSelectionRange(Math.min(selectionStart, index), Math.max(selectionStart, index));
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLDivElement>) => {
    console.log('Mouse up event triggered');
    e.preventDefault();
    setIsMouseDown(false);
  };

  // Adicionar listener global para mouseup
  useEffect(() => {
    const handleGlobalMouseUp = () => setIsMouseDown(false);
    const handleGlobalTouchEnd = () => setIsMouseDown(false);
    
    document.addEventListener('mouseup', handleGlobalMouseUp);
    document.addEventListener('touchend', handleGlobalTouchEnd);
    document.addEventListener('dragend', handleGlobalMouseUp);
    
    return () => {
      document.removeEventListener('mouseup', handleGlobalMouseUp);
      document.removeEventListener('touchend', handleGlobalTouchEnd);
      document.removeEventListener('dragend', handleGlobalMouseUp);
    };
  }, []);

  // Scroll para baixo quando novas mensagens chegam
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Adicionar mensagem do usuário
    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    setShowTypingEffect(true);

    // Simular resposta do bot com efeito de digitação
    setTimeout(() => {
      const botResponse: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Entendi! Pode me dar mais detalhes sobre esse aspecto do seu negócio?',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
      setIsTyping(false);
      setShowTypingEffect(false);
      
      // Refocar no input após resposta
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Captura movimentos do cursor com setas e seleções
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Shift'].includes(e.key) || 
        (e.shiftKey && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key))) {
      setTimeout(() => handleCursorChange(), 0);
    }
  };

  // Função para renderizar texto com seleção
  const renderTextWithSelection = () => {
    const hasSelection = selectionStart !== selectionEnd;
    
    if (!hasSelection) {
      // Sem seleção - mostrar apenas cursor
      return (
        <>
          <span>{inputValue.slice(0, cursorPosition)}</span>
          <span 
            className="cursor-pulse"
            style={{
              fontFamily: '"Consolas", "Courier New", "Monaco", monospace',
              fontSize: '1.1em',
              fontWeight: 'bold'
            }}
          >
            |
          </span>
          <span>{inputValue.slice(cursorPosition)}</span>
        </>
      );
    } else {
      // Com seleção - mostrar texto selecionado destacado
      const beforeSelection = inputValue.slice(0, Math.min(selectionStart, selectionEnd));
      const selectedText = inputValue.slice(Math.min(selectionStart, selectionEnd), Math.max(selectionStart, selectionEnd));
      const afterSelection = inputValue.slice(Math.max(selectionStart, selectionEnd));
      
      return (
        <>
          <span>{beforeSelection}</span>
          <span 
            style={{
              backgroundColor: '#9333ea',
              color: 'white',
              fontFamily: '"Consolas", "Courier New", "Monaco", monospace',
              fontSize: '1.125rem',
              fontWeight: '400'
            }}
          >
            {selectedText}
          </span>
          <span>{afterSelection}</span>
        </>
      );
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto p-8">
      {/* Header */}
      <div className="text-center mb-12 pt-8">
        <div className="mb-4">
          <span className="text-secondary text-sm">
            {'>'} Definição de público alvo
          </span>
        </div>
        <h1 className="dashboard-title">
          Me conte sobre<br />seu negócio
        </h1>
      </div>

      {/* Chat Container */}
      <div className="flex-1 max-w-3xl mx-auto w-full">
        {/* Messages Area */}
        <div className="space-y-6 mb-8">
          {/* Renderizar mensagens do estado */}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`${message.type === 'user' ? 'max-w-[70%]' : 'max-w-[85%] mr-[15%]'} chat-monospace`}>
                <p 
                  className={`text-lg leading-relaxed chat-monospace ${
                    message.type === 'bot' 
                      ? 'text-left' 
                      : 'text-right'
                  }`}
                  style={{
                    color: message.type === 'bot' ? '#333333' : '#333333',
                    fontFamily: '"Consolas", "Courier New", "Monaco", monospace !important',
                    fontSize: '1.125rem',
                    fontWeight: '400 !important'
                  }}
                >
                  {message.type === 'bot' && (
                    <span style={{ color: '#666666' }}>{'>>'} </span>
                  )}
                  {message.content}
                </p>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="max-w-[85%] mr-[15%] chat-monospace">
                <p 
                  className="text-lg leading-relaxed text-left chat-monospace"
                  style={{
                    color: '#333333',
                    fontFamily: '"Consolas", "Courier New", "Monaco", monospace !important',
                    fontSize: '1.125rem',
                    fontWeight: '400 !important'
                  }}
                >
                  <span style={{ color: '#666666' }}>{'>>'} </span>
                  <span className="animate-pulse">Digitando...</span>
                </p>
              </div>
            </div>
          )}

          {/* Input area - texto visível com cursor roxo */}
          <div className="flex justify-end">
            <div className="max-w-[70%] w-full">
              <div className="relative">
                {/* Texto sendo digitado + cursor/seleção visível */}
                <div 
                  className="text-lg leading-relaxed text-right min-h-[28px] chat-monospace cursor-text select-none"
                  style={{
                    color: '#333333',
                    fontFamily: '"Consolas", "Courier New", "Monaco", monospace !important',
                    fontSize: '1.125rem',
                    fontWeight: '400 !important',
                    userSelect: 'none',
                    touchAction: 'none'
                  }}
                  onClick={() => textareaRef.current?.focus()}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onTouchStart={(e) => {
                    const touch = e.touches[0];
                    const mouseEvent = {
                      ...e,
                      clientX: touch.clientX,
                      clientY: touch.clientY,
                      currentTarget: e.currentTarget,
                      preventDefault: e.preventDefault,
                      stopPropagation: e.stopPropagation
                    } as any;
                    handleMouseDown(mouseEvent);
                  }}
                  onTouchMove={(e) => {
                    if (e.touches.length > 0) {
                      const touch = e.touches[0];
                      const mouseEvent = {
                        ...e,
                        clientX: touch.clientX,
                        clientY: touch.clientY,
                        currentTarget: e.currentTarget,
                        preventDefault: e.preventDefault
                      } as any;
                      handleMouseMove(mouseEvent);
                    }
                  }}
                  onTouchEnd={(e) => {
                    const mouseEvent = {
                      ...e,
                      preventDefault: e.preventDefault
                    } as any;
                    handleMouseUp(mouseEvent);
                  }}
                >
                  {renderTextWithSelection()}
                </div>
                
                {/* Textarea invisível para capturar input - posicionado fora da tela */}
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onKeyDown={handleKeyDown}
                  onKeyUp={handleCursorChange}
                  onClick={handleCursorChange}
                  onSelect={handleCursorChange}
                  className="absolute chat-input chat-monospace"
                  style={{ 
                    position: 'fixed',
                    top: '-9999px',
                    left: '-9999px',
                    width: '1px',
                    height: '1px',
                    opacity: 0,
                    caretColor: 'transparent',
                    fontSize: '1.125rem',
                    fontFamily: '"Consolas", "Courier New", "Monaco", monospace !important',
                    color: 'transparent',
                    backgroundColor: 'transparent',
                    border: 'none',
                    outline: 'none',
                    boxShadow: 'none',
                    resize: 'none'
                  }}
                  rows={1}
                  disabled={isTyping}
                />
              </div>
            </div>
          </div>
        </div>
        
        {/* Referência para scroll */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
