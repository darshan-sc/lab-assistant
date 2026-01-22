import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FlaskConical,
  Loader2,
  Search,
  Clock,
  FolderOpen,
  CheckCircle,
  Pause,
} from 'lucide-react';
import { experimentsApi, projectsApi } from '../lib/api-service';
import type { Experiment, Project } from '../types';
import { Badge, EmptyState, Card, CardContent, Input } from '../components/ui';

export default function Experiments() {
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const projectsData = await projectsApi.list();
      setProjects(projectsData);

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
    } catch (err) {
      console.error('Failed to fetch experiments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getProjectName = (projectId: number | null) => {
    if (!projectId) return 'Unassigned';
    const project = projects.find((p) => p.id === projectId);
    return project?.name || 'Unknown Project';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="success">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'active':
        return (
          <Badge variant="success">
            <FlaskConical className="w-3 h-3 mr-1" />
            Active
          </Badge>
        );
      case 'paused':
        return (
          <Badge variant="warning">
            <Pause className="w-3 h-3 mr-1" />
            Paused
          </Badge>
        );
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  const filteredExperiments = experiments.filter((exp) =>
    exp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    exp.goal?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 flex flex-col items-center">
      <div className="w-full max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Experiments</h1>
          <p className="text-gray-500 mt-1">All your experiments across projects.</p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search experiments..."
              className="pl-10"
            />
          </div>
        </div>

        {/* Experiments List */}
        {filteredExperiments.length === 0 ? (
          <Card>
            <CardContent>
              <EmptyState
                icon={<FlaskConical className="w-8 h-8" />}
                title={searchQuery ? 'No experiments found' : 'No experiments yet'}
                description={
                  searchQuery
                    ? 'Try adjusting your search query.'
                    : 'Create experiments in your projects to see them here.'
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredExperiments.map((experiment) => (
              <Card
                key={experiment.id}
                hover
                onClick={() => navigate(`/experiments/${experiment.id}`)}
              >
                <CardContent>
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-purple-50 rounded-lg flex-shrink-0">
                      <FlaskConical className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900">{experiment.title}</h3>
                      {experiment.goal && (
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                          {experiment.goal}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-3">
                        {getStatusBadge(experiment.status)}
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <FolderOpen className="w-3 h-3" />
                          {getProjectName(experiment.project_id)}
                        </span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(experiment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
