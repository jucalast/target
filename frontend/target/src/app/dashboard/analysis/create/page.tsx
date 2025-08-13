'use client';

import withAuth from '@/components/auth/withAuth';
import DashboardLayout from '@/components/layout/DashboardLayout';
import BusinessChatInterface from '@/components/analysis/BusinessChatInterface';

function CreateAnalysisPage() {
  return (
    <DashboardLayout>
      <div className="dashboard-container">
        <div className="min-h-screen flex flex-col">
          <BusinessChatInterface />
        </div>
      </div>
    </DashboardLayout>
  );
}

export default withAuth(CreateAnalysisPage);

