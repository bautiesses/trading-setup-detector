'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  List,
  ScanSearch,
  LineChart,
  LogOut,
  Wallet
} from 'lucide-react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/watchlist', label: 'Watchlist', icon: List },
  { href: '/scanner', label: 'Scanner', icon: ScanSearch },
  { href: '/trades', label: 'Trades', icon: LineChart },
  { href: '/solana', label: 'Solana', icon: Wallet },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    api.logout();
    router.push('/login');
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-full flex-col">
        <div className="flex h-16 items-center border-b border-zinc-800 px-6">
          <h1 className="text-xl font-bold text-white">Break & Retest</h1>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-emerald-600 text-white'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100'
                )}
              >
                <Icon className="h-5 w-5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-zinc-800 p-3">
          <div className="mb-3 px-3 py-2 text-xs text-zinc-500">
            100% Gratis • Sin APIs de pago
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
          >
            <LogOut className="h-5 w-5" />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </aside>
  );
}
