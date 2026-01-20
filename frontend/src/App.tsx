import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import { useAuth } from './context/AuthContext';

import { useEffect, useState } from 'react';
import { authenticatedFetch } from './lib/api';
import { 
  LayoutDashboard, 
  FlaskConical, 
  FileText, 
  Settings, 
  LogOut, 
  Menu,
  CheckCircle2,
  XCircle,
  Loader2
} from 'lucide-react';

function Dashboard() {
  const { user, signOut } = useAuth();
  const [backendStatus, setBackendStatus] = useState<string>('Checking backend connection...');
  const [projects, setProjects] = useState<any[]>([]);
  const [statusType, setStatusType] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const data = await authenticatedFetch('/projects');
        setBackendStatus('System Operational');
        setStatusType('success');
        setProjects(data);
      } catch (error) {
        console.error('Backend check failed:', error);
        setBackendStatus(`System Error: ${error instanceof Error ? error.message : String(error)}`);
        setStatusType('error');
      }
    };

    if (user) {
      checkBackend();
    }
  }, [user]);

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="min-h-screen w-full bg-gray-50 flex justify-center">
      <div className="flex w-full max-w-[1600px] bg-white h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col flex-shrink-0 h-full">
          <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-100">
            <div className="p-2 bg-blue-600 rounded-lg">
              <FlaskConical className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-gray-900 tracking-wide text-lg">LAB ASSISTANT</span>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            <button className="w-full flex items-center gap-3 px-4 py-3 text-blue-600 bg-blue-50 rounded-lg font-medium transition-colors cursor-pointer">
              <LayoutDashboard className="w-5 h-5" />
              Dashboard
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg font-medium transition-colors cursor-pointer">
              <FileText className="w-5 h-5" />
              Publications
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg font-medium transition-colors cursor-pointer">
              <FlaskConical className="w-5 h-5" />
              Experiments
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg font-medium transition-colors cursor-pointer">
              <Settings className="w-5 h-5" />
              Settings
            </button>
          </nav>

          <div className="p-4 border-t border-gray-100 mb-4">
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-gray-50 mb-3">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user?.email}</p>
                <p className="text-xs text-gray-500 truncate">Researcher</p>
              </div>
            </div>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-2 text-gray-500 hover:text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors text-sm font-medium cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col h-full min-w-0 overflow-hidden relative">
          {/* Mobile Header */}
          <header className="md:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-6 h-6 text-blue-600" />
              <span className="font-bold text-gray-900">Lab Assistant</span>
            </div>
            <button className="text-gray-500 cursor-pointer">
              <Menu className="w-6 h-6" />
            </button>
          </header>

          <div className="flex-1 overflow-y-auto p-6 md:p-10 flex flex-col items-center">
            <div className="w-full max-w-5xl">
              
              {/* Page Header */}
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                  <p className="text-gray-500 mt-1 text-sm">Welcome back, here's an overview of your research.</p>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
                  statusType === 'success' ? 'bg-green-50 text-green-700 border-green-200' :
                  statusType === 'error' ? 'bg-red-50 text-red-700 border-red-200' :
                  'bg-blue-50 text-blue-700 border-blue-200'
                }`}>
                  {statusType === 'success' && <CheckCircle2 className="w-3.5 h-3.5" />}
                  {statusType === 'error' && <XCircle className="w-3.5 h-3.5" />}
                  {statusType === 'loading' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  {backendStatus}
                </div>
              </div>

              {/* Dashboard Content */}
              <div className="grid grid-cols-1 gap-8">
                
                {/* Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-500 font-medium text-sm">Active Projects</h3>
                      <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                        <LayoutDashboard className="w-5 h-5" />
                      </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{projects.length}</p>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-500 font-medium text-sm">Total Experiments</h3>
                      <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                        <FlaskConical className="w-5 h-5" />
                      </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">0</p>
                  </div>

                   <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-gray-500 font-medium text-sm">Papers Processed</h3>
                      <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                        <FileText className="w-5 h-5" />
                      </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">0</p>
                  </div>
                </div>

                {/* Projects List with Quick Action */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-900">Recent Projects</h3>
                    <div className="flex gap-3">
                      <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors cursor-pointer">
                        <LayoutDashboard className="w-4 h-4" />
                        New Project
                      </button>
                    </div>
                  </div>
                  
                  {projects.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left">
                        <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold">
                          <tr>
                            <th className="px-6 py-4">Project Name</th>
                            <th className="px-6 py-4">ID</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {projects.map((project: any) => (
                            <tr key={project.id} className="hover:bg-gray-50 transition-colors cursor-pointer group">
                              <td className="px-6 py-4 text-gray-900 font-medium">{project.title || 'Untitled Project'}</td>
                              <td className="px-6 py-4 text-gray-500 font-mono text-xs">{project.id}</td>
                              <td className="px-6 py-4">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Active
                                </span>
                              </td>
                              <td className="px-6 py-4 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-blue-600 font-medium text-sm">Open →</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="p-12 text-center text-gray-500">
                      <p>No projects found. Start by creating one!</p>
                    </div>
                  )}
                </div>

              </div>

            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
             <Route path="/" element={<Dashboard />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
