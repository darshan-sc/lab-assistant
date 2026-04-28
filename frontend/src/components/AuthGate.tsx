'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FlaskConical } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <FlaskConical className="w-12 h-12 text-blue-600 animate-bounce" />
          <p className="text-gray-500 font-medium">Initializing ResearchNexus...</p>
        </div>
      </div>
    );
  }

  return children;
}
