'use client';

import AdmissionForm from '@/components/analysis/AdmissionForm';
function CreateAnalysisPage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-screen home-background">
      <div className="container px-4">
        <AdmissionForm />
      </div>
    </main>
  );
}

export default CreateAnalysisPage;

