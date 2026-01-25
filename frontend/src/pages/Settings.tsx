import { useAuth } from '../context/AuthContext';
import { Settings as SettingsIcon, User, Mail, Shield } from 'lucide-react';
import { Card, CardContent } from '../components/ui';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="p-6 md:p-10 flex flex-col items-center">
      <div className="w-full max-w-3xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Manage your account and preferences.</p>
        </div>

        {/* Profile Section */}
        <Card className="mb-6">
          <CardContent>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-2xl">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Profile</h2>
                <p className="text-gray-500">Your account information</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Mail className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="text-gray-900 font-medium">{user?.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <User className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">User ID</p>
                  <p className="text-gray-900 font-medium font-mono text-sm">{user?.id}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Shield className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Role</p>
                  <p className="text-gray-900 font-medium">Researcher</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* About Section */}
        <Card>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <SettingsIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">About</h2>
                <p className="text-gray-500">ResearchNexus v1.0</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              ResearchNexus is a research management platform that helps you organize experiments,
              track literature, and collaborate with your team. Upload papers, ask questions using
              AI-powered RAG, and log your experimental runs all in one place.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
