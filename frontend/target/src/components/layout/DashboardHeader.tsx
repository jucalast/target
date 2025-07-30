"use client";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FaSearch, FaBell } from "react-icons/fa";

export default function DashboardHeader() {
  const { logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header 
      className="w-full flex justify-between items-center"
      style={{
        backgroundColor: 'var(--bg-primary)',
        padding: 'var(--spacing-lg)',
        height: '5rem'
      }}
    >
      {/* Espaço vazio à esquerda */}
      <div></div>



      {/* Zona de Ações e Perfil (Direita) */}
      <div className="flex items-center" style={{ gap: 'var(--spacing-md)' }}>
        <button 
          className="rounded-lg transition-all"
          style={{
            padding: 'var(--spacing-sm)',
            color: 'var(--text-secondary)',
            backgroundColor: 'transparent',
            border: 'none',
            borderRadius: 'var(--border-radius-md)',
            transition: 'all var(--transition-normal)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)';
            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-secondary)';
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <FaSearch size={18} />
        </button>
        
        <button 
          className="rounded-lg transition-all relative"
          style={{
            padding: 'var(--spacing-sm)',
            color: 'var(--text-secondary)',
            backgroundColor: 'transparent',
            border: 'none',
            borderRadius: 'var(--border-radius-md)',
            transition: 'all var(--transition-normal)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)';
            e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-secondary)';
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <FaBell size={18} />
          <span 
            className="absolute -top-1 -right-1 rounded-full"
            style={{
              width: '0.75rem',
              height: '0.75rem',
              backgroundColor: 'var(--error)'
            }}
          ></span>
        </button>
        
        {/* Divisor */}
        <div 
          style={{
            width: '1px',
            height: '1.5rem',
            backgroundColor: 'var(--border-primary)',
            margin: '0 var(--spacing-sm)'
          }}
        ></div>
        
        {/* Avatar e Botão Sair */}
        <div className="flex items-center" style={{ gap: 'var(--spacing-sm)' }}>
          <div 
            className="rounded-full overflow-hidden border-2 transition-colors"
            style={{
              width: '2rem',
              height: '2rem',
              borderColor: 'var(--border-secondary)',
              transition: 'border-color var(--transition-fast)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-secondary)';
            }}
          >
            <img src="/avatar.png" alt="Avatar" className="w-full h-full object-cover" />
          </div>
          
          {/* Botão Sair */}
          <button 
            onClick={handleLogout}
            className="flex items-center rounded-lg transition-all"
            style={{
              padding: 'var(--spacing-sm) var(--spacing-md)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-medium)',
              color: 'var(--text-secondary)',
              backgroundColor: 'var(--bg-tertiary)',
              border: '1px solid var(--border-primary)',
              borderRadius: 'var(--border-radius-md)',
              transition: 'all var(--transition-normal)',
              gap: 'var(--spacing-xs)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--text-primary)';
              e.currentTarget.style.backgroundColor = 'var(--error)';
              e.currentTarget.style.borderColor = 'var(--error)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
              e.currentTarget.style.borderColor = 'var(--border-primary)';
            }}
          >
            <span>Sair</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
