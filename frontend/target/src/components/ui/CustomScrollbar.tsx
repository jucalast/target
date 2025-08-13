'use client';

import React, { useRef, useEffect, useState } from 'react';

interface CustomScrollbarProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string;
  variant?: 'default' | 'thin' | 'thick';
}

export default function CustomScrollbar({
  children,
  className = '',
  maxHeight = '100vh',
  variant = 'default'
}: CustomScrollbarProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const thumbRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isScrolling, setIsScrolling] = useState(false);
  const [scrollTimeout, setScrollTimeout] = useState<NodeJS.Timeout | null>(null);
  const [startY, setStartY] = useState(0);
  const [startScrollTop, setStartScrollTop] = useState(0);

  const getScrollbarWidth = () => {
    switch (variant) {
      case 'thin':
        return 8;
      case 'thick':
        return 16;
      default:
        return 12;
    }
  };

  const updateThumb = () => {
    const content = contentRef.current;
    const thumb = thumbRef.current;
    const track = trackRef.current;
    
    if (!content || !thumb || !track) return;

    const scrollableHeight = content.scrollHeight;
    const visibleHeight = content.clientHeight;
    
    if (scrollableHeight <= visibleHeight) {
      thumb.style.display = 'none';
      return;
    }
    
    thumb.style.display = 'block';
    
    const thumbHeight = (visibleHeight / scrollableHeight) * track.clientHeight;
    thumb.style.height = `${thumbHeight}px`;
    
    const scrollTop = content.scrollTop;
    const maxScrollTop = scrollableHeight - visibleHeight;
    const scrollPercentage = scrollTop / maxScrollTop;
    const maxThumbTop = track.clientHeight - thumbHeight;
    const thumbTop = scrollPercentage * maxThumbTop;
    
    thumb.style.transform = `translateY(${thumbTop}px)`;
  };

  const handleScroll = () => {
    updateThumb();
    setIsScrolling(true);
    
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }
    
    const timeout = setTimeout(() => {
      setIsScrolling(false);
    }, 250);
    
    setScrollTimeout(timeout);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setStartY(e.clientY);
    setStartScrollTop(contentRef.current?.scrollTop || 0);
    document.body.style.userSelect = 'none';
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !contentRef.current) return;
    
    const deltaY = e.clientY - startY;
    const content = contentRef.current;
    const scrollableHeight = content.scrollHeight;
    const visibleHeight = content.clientHeight;
    const scrollDelta = (deltaY / visibleHeight) * scrollableHeight;
    
    content.scrollTop = startScrollTop + scrollDelta;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    document.body.style.userSelect = '';
  };

  useEffect(() => {
    const content = contentRef.current;
    if (!content) return;

    // Observer para redimensionamento
    const resizeObserver = new ResizeObserver(updateThumb);
    resizeObserver.observe(content);

    // Event listeners para mouse
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    // Atualização inicial
    updateThumb();

    return () => {
      resizeObserver.disconnect();
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [isDragging, startY, startScrollTop, scrollTimeout]);

  const scrollbarWidth = getScrollbarWidth();

  return (
    <div 
      className={`relative ${className}`}
      style={{ maxHeight, overflow: 'hidden' }}
    >
      {/* Track da scrollbar */}
      <div
        ref={trackRef}
        className="absolute top-0 right-0 h-full bg-transparent z-10"
        style={{ width: `${scrollbarWidth}px` }}
      >
        {/* Thumb da scrollbar */}
        <div
          ref={thumbRef}
          className={`
            absolute bg-black rounded-full cursor-pointer transition-all duration-200 ease-out
            ${isScrolling || isDragging ? 'w-full mx-0' : 'mx-1'}
          `}
          style={{
            width: isScrolling || isDragging ? `${scrollbarWidth}px` : `${scrollbarWidth - 6}px`,
            backgroundColor: '#000000',
            borderRadius: '20px'
          }}
          onMouseDown={handleMouseDown}
          onMouseEnter={() => {
            if (thumbRef.current) {
              thumbRef.current.style.backgroundColor = '#000000';
            }
          }}
          onMouseLeave={() => {
            if (thumbRef.current && !isDragging) {
              thumbRef.current.style.backgroundColor = '#000000';
            }
          }}
        />
      </div>

      {/* Conteúdo com scrollbar nativo escondido */}
      <div
        ref={contentRef}
        className="h-full w-full overflow-y-scroll pr-4"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          maxHeight
        }}
        onScroll={handleScroll}
      >
        <div className="pr-4">
          {children}
        </div>
        
        <style jsx>{`
          div::-webkit-scrollbar {
            display: none;
          }
        `}</style>
      </div>
    </div>
  );
}
