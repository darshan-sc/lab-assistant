import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  FlaskConical,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
} from 'lucide-react';
import { useState } from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/papers', icon: FileText, label: 'Publications' },
    { to: '/experiments', icon: FlaskConical, label: 'Experiments' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  const NavItem = ({ to, icon: Icon, label }: { to: string; icon: typeof LayoutDashboard; label: string }) => (
    <NavLink
      to={to}
      end={to === '/'}
      onClick={() => setMobileMenuOpen(false)}
      className={({ isActive }) =>
        `w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors cursor-pointer ${
          isActive
            ? 'text-blue-600 bg-blue-50'
            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
        }`
      }
    >
      <Icon className="w-5 h-5" />
      {label}
    </NavLink>
  );

  return (
    <div className="min-h-screen w-full bg-gray-50 flex justify-center">
      <div className="flex w-full max-w-[1600px] bg-white h-screen overflow-hidden">
        {/* Desktop Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 hidden md:flex flex-col flex-shrink-0 h-full">
          <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-100">
            <div className="p-2 bg-blue-600 rounded-lg">
              <FlaskConical className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-gray-900 tracking-wide text-lg">RESEARCHNEXUS</span>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navItems.map((item) => (
              <NavItem key={item.to} {...item} />
            ))}
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

        {/* Mobile Header */}
        <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
          <header className="md:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-6 h-6 text-blue-600" />
              <span className="font-bold text-gray-900">ResearchNexus</span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-500 cursor-pointer"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </header>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden absolute top-16 left-0 right-0 bg-white border-b border-gray-200 z-40 shadow-lg">
              <nav className="p-4 space-y-2">
                {navItems.map((item) => (
                  <NavItem key={item.to} {...item} />
                ))}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors cursor-pointer"
                >
                  <LogOut className="w-5 h-5" />
                  Sign Out
                </button>
              </nav>
            </div>
          )}

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </div>
  );
}
