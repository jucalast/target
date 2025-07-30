'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, ComponentType } from 'react';

const withAuth = <P extends object>(WrappedComponent: ComponentType<P>) => {
  const AuthComponent = (props: P) => {
    const { token } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!token) {
        router.replace('/login');
      }
    }, [token, router]);

    if (!token) {
      return null; // Ou um spinner de carregamento
    }

    return <WrappedComponent {...props} />;
  };

  return AuthComponent;
};

export default withAuth;
