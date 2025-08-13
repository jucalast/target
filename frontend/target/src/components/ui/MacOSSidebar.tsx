'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';

interface SidebarApp {
  id: string;
  name: string;
  icon: string;
  href: string;
  color: string; // Cor dominante do app
  isActive?: boolean;
}

const sidebarApps: SidebarApp[] = [
  {
    id: 'analysis',
    name: 'Análises',
    icon: '/Logo Maven (15).png',
    href: '/dashboard/analysis',
    color: '#4F7FFF' // Azul do logo Maven
  }
];

export default function MacOSSidebar() {
  const pathname = usePathname();
  const [hoveredApp, setHoveredApp] = useState<string | null>(null);

  // Gerar gradiente baseado nas cores dos apps
  const generateGradient = () => {
    const colors = sidebarApps.map(app => app.color);
    if (colors.length === 1) {
      const color = colors[0];
      return {
        background: `
          radial-gradient(ellipse at center, ${color}20 0%, ${color}12 30%, ${color}05 60%, transparent 100%),
          linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.4))
        `,
        backdropFilter: 'blur(12px) saturate(1.1)',
        border: `1px solid rgba(255, 255, 255, 0.3)`
      };
    }
    // Para múltiplas cores (futuro)
    return {
      background: `linear-gradient(135deg, ${colors.map(c => c + '10').join(', ')}, rgba(255, 255, 255, 0.6))`,
      backdropFilter: 'blur(12px) saturate(1.1)',
      border: '1px solid rgba(255, 255, 255, 0.3)'
    };
  };

  const gradientStyle = generateGradient();

  return (
    <div 
      className="fixed left-4 top-1/2 transform -translate-y-1/2 w-16 rounded-full flex flex-col items-center py-4 z-50"
      style={gradientStyle}
    >
      {/* Apps */}
      <div className="flex flex-col space-y-3">
        {sidebarApps.map((app) => {
          const isActive = pathname === app.href;
          const isHovered = hoveredApp === app.id;
          
          return (
            <div key={app.id} className="relative group">
              <Link
                href={app.href}
                prefetch={false}
                className={`
                  relative block w-10 h-10 rounded-full transition-all duration-300 ease-out
                  ${isActive 
                    ? 'bg-white/20 shadow-lg scale-110 backdrop-blur-sm' 
                    : 'hover:bg-white/15 hover:scale-110 backdrop-blur-sm'
                  }
                  ${isHovered ? 'shadow-xl' : ''}
                `}
                style={{
                  boxShadow: isActive ? `0 0 20px ${app.color}40` : undefined
                }}
                onMouseEnter={() => setHoveredApp(app.id)}
                onMouseLeave={() => setHoveredApp(null)}
              >
                <div className="w-full h-full flex items-center justify-center">
                  {app.icon.endsWith('.svg') || app.icon.endsWith('.png') ? (
                    <Image
                      src={app.icon}
                      alt={app.name}
                      width={24}
                      height={24}
                      className="w-6 h-6"
                    />
                  ) : (
                    <span className="text-lg">{app.icon}</span>
                  )}
                </div>
                
                {/* Active indicator */}
                {isActive && (
                  <div 
                    className="absolute -left-2 top-1/2 transform -translate-y-1/2 w-1 h-4 rounded-r"
                    style={{ backgroundColor: app.color }}
                  ></div>
                )}
              </Link>

              {/* Tooltip */}
              <div className={`
                absolute left-12 top-1/2 transform -translate-y-1/2 ml-2
                bg-black/80 text-white px-3 py-1 rounded-lg text-sm whitespace-nowrap backdrop-blur-sm
                transition-all duration-200 z-50
                ${isHovered 
                  ? 'opacity-100 visible translate-x-0' 
                  : 'opacity-0 invisible -translate-x-2'
                }
              `}>
                {app.name}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
