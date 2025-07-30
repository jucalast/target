'use client';

import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ReactNode } from 'react';

function AppHeader() {
  const { token, logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-10 bg-transparent p-4 flex justify-end">
      <div className="container mx-auto flex justify-end items-center">
        {isLoading ? null : token ? (
          <button onClick={handleLogout} className="btn-primary">
            Sair
          </button>
        ) : (
          <Link href="/login" className="btn-primary">
            Entrar
          </Link>
        )}
      </div>
    </header>
  );
}

import { usePathname } from 'next/navigation';

export function Providers({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <AuthProvider>
      {pathname !== '/login' && !pathname.startsWith('/dashboard') && <AppHeader />}
      {children}
    </AuthProvider>
  );
}
