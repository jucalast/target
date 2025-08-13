"use client";
import { ReactNode, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.replace("/login");
    }
  }, [token, isLoading, router]);

  if (isLoading || !token) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {children}
    </div>
  );
}
