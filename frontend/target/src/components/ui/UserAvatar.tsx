'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '../../contexts/AuthContext';

interface UserAvatarProps {
  src?: string | null;
  alt?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showStatus?: boolean;
  status?: 'online' | 'offline' | 'busy' | 'away';
  onClick?: () => void;
  showDropdown?: boolean;
  userName?: string;
  userEmail?: string;
  inline?: boolean;
}

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8', 
  lg: 'w-10 h-10',
  xl: 'w-12 h-12'
};

const statusColors = {
  online: 'bg-green-400',
  offline: 'bg-gray-400',
  busy: 'bg-red-400',
  away: 'bg-yellow-400'
};

export default function UserAvatar({
  src,
  alt = 'User Avatar',
  size = 'md',
  className = '',
  showStatus = false,
  status = 'online',
  onClick,
  showDropdown = false,
  userName = 'Usuário',
  userEmail = 'user@example.com',
  inline = false
}: UserAvatarProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const { logout, user } = useAuth();

  // Usar dados reais do usuário se disponíveis, senão usar props
  const displayName = user?.name || userName;
  const displayEmail = user?.email || userEmail;
  const displayAvatar = user?.avatar || src;

  console.log('UserAvatar - Usuário do contexto:', user);
  console.log('UserAvatar - Nome exibido:', displayName);
  console.log('UserAvatar - Email exibido:', displayEmail);

  // Se não há dados do usuário nem props, mostrar loading
  if (!user && !userName) {
    return (
      <div className={`${sizeClasses[size]} rounded-full bg-tertiary animate-pulse border border-muted`}></div>
    );
  }

  const handleClick = () => {
    if (showDropdown) {
      setIsDropdownOpen(!isDropdownOpen);
    }
    onClick?.();
  };

  const handleLogout = () => {
    logout();
    setIsDropdownOpen(false);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="relative">
      <div
        className={`
          relative cursor-pointer transition-all duration-200
          ${sizeClasses[size]}
          ${className}
        `}
        onClick={handleClick}
      >
        {/* Avatar Container */}
        <div className={`
          ${sizeClasses[size]} 
          rounded-full overflow-hidden
          border border-muted
        `}>
          {displayAvatar && !imageError ? (
            <Image
              src={displayAvatar}
              alt={alt}
              width={40}
              height={40}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full accent-primary flex items-center justify-center text-primary font-semibold text-xs border border-muted">
              {getInitials(displayName)}
            </div>
          )}
        </div>

        {/* Status Indicator */}
        {showStatus && (
          <div className={`
            absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white
            ${statusColors[status]}
          `} />
        )}
      </div>

      {/* Dropdown Menu */}
      {showDropdown && isDropdownOpen && (
        <div className="absolute bg-secondary rounded-lg border border-muted min-w-[200px] z-1000 top-full mt-2 right-0">
          <div className="p-4 border-b border-muted">
            <div className="flex items-center space-x-3">
              <div className={`${sizeClasses.sm} rounded-full overflow-hidden border border-muted`}>
                {displayAvatar && !imageError ? (
                  <Image
                    src={displayAvatar}
                    alt={alt}
                    width={32}
                    height={32}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-secondary flex items-center justify-center text-primary text-xs font-semibold border border-muted">
                    {getInitials(displayName)}
                  </div>
                )}
              </div>
              <div>
                <div className="font-semibold text-primary text-sm">{displayName}</div>
                <div className="text-xs text-secondary">{displayEmail}</div>
              </div>
            </div>
          </div>
          
          <div className="py-2">
            <button className="w-full px-4 py-2 text-left text-sm text-secondary hover:bg-tertiary transition-colors">
              Perfil
            </button>
            <button className="w-full px-4 py-2 text-left text-sm text-secondary hover:bg-tertiary transition-colors">
              Configurações
            </button>
            <button className="w-full px-4 py-2 text-left text-sm text-secondary hover:bg-tertiary transition-colors">
              Ajuda
            </button>
            <hr className="my-2 border-muted" />
            <button 
              onClick={handleLogout}
              className="w-full px-4 py-2 text-left text-sm text-error hover:bg-tertiary transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      )}

      {/* Overlay para fechar dropdown */}
      {showDropdown && isDropdownOpen && (
        <div
          className="fixed inset-0 z-990"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
}
