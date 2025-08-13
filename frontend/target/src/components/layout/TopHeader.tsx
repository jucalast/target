'use client';

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DynamicIsland from '../ui/DynamicIsland';
import UserAvatar from '../ui/UserAvatar';

export default function TopHeader() {
  const { user } = useAuth();

  console.log('TopHeader - Usuário do contexto:', user);

  // Só renderizar se há dados do usuário
  if (!user) {
    console.log('TopHeader - Aguardando dados do usuário...');
    return (
      <div className="fixed top-0 left-0 right-0 z-50 flex items-start justify-center">
        <div className="flex items-start gap-4">
          {/* Dynamic Island */}
          <div className="relative">
            <DynamicIsland variant="inline" />
          </div>
          
          {/* Loading placeholder para avatar */}
          <div className="relative flex items-center pt-1" style={{ height: '50px' }}>
            <div className="w-10 h-10 rounded-full bg-gray-200 animate-pulse"></div>
          </div>
        </div>
      </div>
    );
  }

  // Usar dados reais do usuário autenticado
  const userData = {
    name: user.name,
    email: user.email,
    avatar: user.avatar || null
  };

  console.log('TopHeader - Dados exibidos:', userData);

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex items-start justify-center">
      <div className="flex items-start gap-4">
        {/* Dynamic Island encostada no topo */}
        <div className="relative">
          <DynamicIsland 
            variant="inline"
          />
        </div>
        
        {/* User Avatar perfeitamente alinhado */}
        <div className="relative flex items-center pt-1" style={{ height: '50px' }}>
          <UserAvatar 
            size="lg"
            showStatus={false}
            showDropdown={true}
            userName={userData.name}
            userEmail={userData.email}
            src={userData.avatar}
            inline={true}
            className="hover:scale-110 transition-transform duration-200"
          />
        </div>
      </div>
    </div>
  );
}
