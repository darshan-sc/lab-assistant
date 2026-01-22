import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FlaskConical,
  FileText,
  Plus,
  Trash2,
  FolderOpen,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';
import { projectsApi, papersApi, experimentsApi } from '../lib/api-service';
import type { Project, Paper, Experiment } from '../types';
import { Modal, Button, Input, Textarea, EmptyState } from '../components/ui';

export default function Dashboard() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusType, setStatusType] = useState<'loading' | 'success' | 'error'>('loading');
  const [backendStatus, setBackendStatus] = useState('Checking backend connection...');

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setStatusType('loading');
    try {
      const [projectsData, papersData] = await Promise.all([
        projectsApi.list(),
        papersApi.list(),
      ]);
      setProjects(projectsData);
      setPapers(papersData);

      // Fetch experiments for all projects
      const allExperiments: Experiment[] = [];
      for (const project of projectsData) {
        try {
          const exps = await experimentsApi.list(project.id);
          allExperiments.push(...exps);
        } catch {
          // Ignore errors for individual projects
        }
      }
      setExperiments(allExperiments);

      setBackendStatus('System Operational');
      setStatusType('success');
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setBackendStatus(`System Error: ${err instanceof Error ? err.message : String(err)}`);
      setStatusType('error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      setError('Project name is required');
      return;
    }
    setCreating(true);
    setError('');
    try {
      await projectsApi.create({
        name: newProjectName,
        description: newProjectDescription || undefined,
      });
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDescription('');
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
      return;
    }
    try {
      await projectsApi.delete(id);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete project');
    }
  };

  return (
    <div className="p-6 md:p-10 flex flex-col items-center">
      <div className="w-full max-w-5xl">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 mt-1 text-sm">
              Welcome back, here's an overview of your research.
            </p>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
              statusType === 'success'
                ? 'bg-green-50 text-green-700 border-green-200'
                : statusType === 'error'
                ? 'bg-red-50 text-red-700 border-red-200'
                : 'bg-blue-50 text-blue-700 border-blue-200'
            }`}
          >
            {statusType === 'success' && <CheckCircle2 className="w-3.5 h-3.5" />}
            {statusType === 'error' && <XCircle className="w-3.5 h-3.5" />}
            {statusType === 'loading' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {backendStatus}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
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
            <p className="text-3xl font-bold text-gray-900">{experiments.length}</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-gray-500 font-medium text-sm">Papers Processed</h3>
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <FileText className="w-5 h-5" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {papers.filter((p) => p.processing_status === 'completed').length}
            </p>
          </div>
        </div>

        {/* Projects List */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-900">Your Projects</h3>
            <Button
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setShowCreateModal(true)}
            >
              New Project
            </Button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
          ) : projects.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold">
                  <tr>
                    <th className="px-6 py-4">Project Name</th>
                    <th className="px-6 py-4">Description</th>
                    <th className="px-6 py-4">Created</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {projects.map((project) => (
                    <tr
                      key={project.id}
                      className="hover:bg-gray-50 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-50 rounded-lg">
                            <FolderOpen className="w-4 h-4 text-blue-600" />
                          </div>
                          <span className="text-gray-900 font-medium">{project.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-500 text-sm max-w-xs truncate">
                        {project.description || '-'}
                      </td>
                      <td className="px-6 py-4 text-gray-500 text-sm">
                        {new Date(project.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <span className="text-blue-600 font-medium text-sm mr-2">Open</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteProject(project.id, project.name);
                            }}
                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              icon={<FolderOpen className="w-8 h-8" />}
              title="No projects yet"
              description="Create your first project to start organizing your research."
              action={
                <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
                  Create Project
                </Button>
              }
            />
          )}
        </div>
      </div>

      {/* Create Project Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setError('');
          setNewProjectName('');
          setNewProjectDescription('');
        }}
        title="Create New Project"
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}
          <Input
            label="Project Name"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="e.g., Machine Learning Research"
            autoFocus
          />
          <Textarea
            label="Description (optional)"
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
            placeholder="Brief description of your project..."
            rows={3}
          />
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateProject} loading={creating}>
              Create Project
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
