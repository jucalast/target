"use client";
import Link from "next/link";
import SidebarItem from "./analysis/SidebarItem";

import { FaHome, FaChartBar, FaPlusCircle, FaUser } from "react-icons/fa";

export default function DashboardSidebar() {
  return (
    <aside 
      className="sidebar-minimal h-full flex flex-col overflow-y-auto p-4"
      style={{ backgroundColor: 'var(--bg-primary)', borderRight: '1px solid var(--border-primary)' }}
    >
      <div className="mb-8 flex w-full items-center justify-center">
        <img src="/logo.png" alt="Logo" className="h-8 w-8" />
      </div>
      <nav className="flex flex-col w-full gap-2">
        <SidebarItem href="/dashboard" icon={<FaHome size={20} />} label="Início" />
        <SidebarItem href="/dashboard/analysis" icon={<FaChartBar size={20} />} label="Análises" />
        <SidebarItem href="/dashboard/reports" icon={<FaPlusCircle size={20} />} label="Relatórios" />
        <SidebarItem href="/dashboard/profile" icon={<FaUser size={20} />} label="Perfil" />
      </nav>
    </aside>
  );
}
