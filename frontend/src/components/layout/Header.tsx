'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { User } from '@/types';

export function Header() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.getCurrentUser()
      .then((data) => setUser(data as User))
      .catch(() => setUser(null));
  }, []);

  return (
    <header className="sticky top-0 z-30 h-16 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full items-center justify-between px-6">
        <div>
          <h2 className="text-lg font-semibold">Trading Setup Detector</h2>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-muted-foreground">
              {user.email}
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
