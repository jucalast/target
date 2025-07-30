'use client';

import Image from 'next/image';
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const { token, isLoading } = useAuth();

  return (
    <main className="flex flex-col items-center justify-center min-h-screen text-center home-background">
      <div className="container">
        {isLoading ? (
          <div /> // Renderiza um container vazio enquanto carrega
        ) : token ? (
          (() => {
            if (typeof window !== 'undefined') {
              window.location.href = '/dashboard';
            }
            return null;
          })()
        ) : (
          <div className="text-center">
            <div className="flex justify-center">
              <Image
                src="/logo.png"
                alt="Logo"
                width={320}
                height={320}
                priority
              />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
