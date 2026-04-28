import AuthGate from '@/components/AuthGate';
import Layout from '@/components/Layout';

export default function ProtectedLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGate>
      <Layout>{children}</Layout>
    </AuthGate>
  );
}
