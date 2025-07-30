import Link from 'next/link';
import React from 'react';

interface SidebarItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
}

export default function SidebarItem({ href, icon, label }: SidebarItemProps) {
  return (
        <Link href={href} className="sidebar-item">
            <span className="sidebar-icon">{icon}</span>
            <span className="sidebar-label">{label}</span>
    </Link>
  );
}
