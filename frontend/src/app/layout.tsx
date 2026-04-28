import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import '@/index.css';

export const metadata: Metadata = {
  title: 'ResearchNexus',
  description: 'AI-assisted research management workspace',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
