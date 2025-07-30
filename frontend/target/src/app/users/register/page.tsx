"use client";
import { useState } from "react";
import Link from 'next/link';

export default function RegisterUser() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Erro ao registrar usuário");
      }
      setResult("Usuário registrado com sucesso!");
      setForm({ email: "", password: "" }); // Limpa o formulário
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background-dark p-4">
      <div className="form-container">
        <form onSubmit={handleSubmit}>
          <h1 className="form-title">Registrar</h1>
          {result && <p className="success-message mb-4">{result}</p>}
          {error && <p className="error-message mb-4">{error}</p>}
          <div className="mb-4">
            <label htmlFor="email" className="form-label">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              className="form-input"
              placeholder="seu@email.com"
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="password" className="form-label">
              Senha
            </label>
            <input
              id="password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              className="form-input"
              placeholder="Crie uma senha forte"
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={loading}
          >
            {loading ? 'Registrando...' : 'Registrar'}
          </button>
          <div className="text-center mt-6">
            <Link
              href="/login"
              className="text-sm text-accent-color hover:text-accent-color-hover transition-colors duration-200"
            >
              Já tem uma conta? Entrar
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
