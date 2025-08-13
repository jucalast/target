'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role?: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  login: (token: string, userData?: User) => void;
  logout: () => void;
  updateUser: (userData: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Função para buscar dados do usuário do backend
  const fetchUserData = async (authToken: string) => {
    try {
      console.log('Buscando dados do usuário...');
      const response = await fetch('http://localhost:8000/api/v1/users/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('Dados do usuário recebidos:', userData);
        setUser(userData);
        // Salvar dados do usuário no localStorage para cache
        localStorage.setItem('user', JSON.stringify(userData));
      } else {
        console.error('Falha ao buscar dados do usuário:', response.status, response.statusText);
        // Limpar dados de autenticação e redirecionar para login
        setToken(null);
        setUser(null);
        Cookies.remove('token');
        localStorage.removeItem('user');
        router.push('/login');
      }
    } catch (error) {
      console.error('Erro ao buscar dados do usuário:', error);
      // Em caso de erro de rede, limpar dados e redirecionar para login
      setToken(null);
      setUser(null);
      Cookies.remove('token');
      localStorage.removeItem('user');
      router.push('/login');
    }
  };

  useEffect(() => {
    const storedToken = Cookies.get('token');
    const storedUser = localStorage.getItem('user');
    
    console.log('Token armazenado:', storedToken);
    console.log('Usuário armazenado:', storedUser);
    
    if (storedToken) {
      setToken(storedToken);
      
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          console.log('Usuário carregado do localStorage:', parsedUser);
          setUser(parsedUser);
        } catch (error) {
          console.error('Erro ao carregar dados do usuário do localStorage:', error);
        }
      }
      
      // Buscar dados atualizados do usuário
      fetchUserData(storedToken);
    } else {
      // Se não há token, redirecionar para login
      setUser(null);
      console.log('Nenhum token encontrado, redirecionando para login...');
      router.push('/login');
    }
    
    setIsLoading(false);
  }, [router]);

  const login = (newToken: string, userData?: User) => {
    console.log('Login iniciado com token:', newToken);
    console.log('Dados do usuário fornecidos:', userData);
    
    setToken(newToken);
    Cookies.set('token', newToken, { expires: 7, secure: true, sameSite: 'strict' });
    
    if (userData) {
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      console.log('Usuário definido:', userData);
    } else {
      // Buscar dados do usuário se não foram fornecidos
      console.log('Buscando dados do usuário...');
      fetchUserData(newToken);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    Cookies.remove('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  const updateUser = (userData: User) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ token, user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
