'use client';

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import DashboardLayout from '../../components/layout/DashboardLayout';

export default function DashboardHome() {
  const { token, user } = useAuth();

  // Se não estiver autenticado, não renderizar conteúdo (middleware já redireciona)
  if (!token) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="dashboard-container">
        <div className="p-8">
          {/* Header with main statistic */}
          <div className="text-center mb-16 pt-8">
            <h1 className="dashboard-title">
              5% do seu negócio<br />estruturado
            </h1>
          </div>

          {/* Main Grid Layout - Exactly like the image */}
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Top Row - 3 cards */}
            <div className="grid grid-cols-12 gap-6 h-64">
              {/* Left top card */}
              <div className="col-span-3">
                <div className="dashboard-card w-full h-full rounded-3xl"></div>
              </div>
              
              {/* Center top card - largest */}
              <div className="col-span-6">
                <div className="dashboard-card w-full h-full rounded-3xl"></div>
              </div>
              
              {/* Right top card */}
              <div className="col-span-3">
                <div className="dashboard-card w-full h-full rounded-3xl"></div>
              </div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-12 gap-6 h-48">
              {/* Bottom left large card */}
              <div className="col-span-5">
                <div className="dashboard-card w-full h-full rounded-3xl"></div>
              </div>
              
              {/* Two small vertical cards in the middle */}
              <div className="col-span-2 grid grid-rows-2 gap-4">
                <div className="dashboard-card rounded-2xl"></div>
                <div className="dashboard-card rounded-2xl"></div>
              </div>
              
              {/* Bottom right large card */}
              <div className="col-span-5">
                <div className="dashboard-card w-full h-full rounded-3xl"></div>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
