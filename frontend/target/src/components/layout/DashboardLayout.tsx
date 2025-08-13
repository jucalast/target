'use client';

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import TopHeader from './TopHeader';
import CustomScrollbar from '../ui/CustomScrollbar';
import MacOSSidebar from '../ui/MacOSSidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { isLoading, token } = useAuth();

  // Mostrar loading enquanto verifica autenticação
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-primary">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-secondary">Carregando...</p>
        </div>
      </div>
    );
  }

  // Se não há token, não renderizar (middleware já deve redirecionar)
  if (!token) {
    return null;
  }

  return (
    <div className="min-h-screen relative bg-primary">
      {/* Sidebar */}
      <MacOSSidebar />
      
      {/* Main Content Area */}
      <div>
        {/* Top Header com Dynamic Island e Avatar lado a lado */}
        <TopHeader />
        
        {/* Main Content */}
        <div className="pt-16">
          <CustomScrollbar maxHeight="calc(100vh - 64px)">
            {children}
          </CustomScrollbar>
        </div>
      </div>
    </div>
  );
}
