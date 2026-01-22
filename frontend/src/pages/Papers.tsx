import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Loader2,
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  FolderOpen,
} from 'lucide-react';
import { papersApi, projectsApi } from '../lib/api-service';
import type { Paper, Project } from '../types';
import { Badge, EmptyState, Card, CardContent, Input } from '../components/ui';

export default function Papers() {
  const navigate = useNavigate();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [papersData, projectsData] = await Promise.all([
        papersApi.list(),
        projectsApi.list(),
      ]);
      setPapers(papersData);
      setProjects(projectsData);
    } catch (err) {
      console.error('Failed to fetch papers:', err);
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
            Indexed
          </Badge>
        );
      case 'processing':
        return (
          <Badge variant="info">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Processing
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="error">
            <AlertCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      default:
        return (
          <Badge variant="default">
            <Clock className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
    }
  };

  const filteredPapers = papers.filter((paper) =>
    paper.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    paper.abstract?.toLowerCase().includes(searchQuery.toLowerCase())
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
          <h1 className="text-2xl font-bold text-gray-900">Publications</h1>
          <p className="text-gray-500 mt-1">All your research papers across projects.</p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search papers..."
              className="pl-10"
            />
          </div>
        </div>

        {/* Papers List */}
        {filteredPapers.length === 0 ? (
          <Card>
            <CardContent>
              <EmptyState
                icon={<FileText className="w-8 h-8" />}
                title={searchQuery ? 'No papers found' : 'No papers yet'}
                description={
                  searchQuery
                    ? 'Try adjusting your search query.'
                    : 'Upload papers to your projects to see them here.'
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredPapers.map((paper) => (
              <Card
                key={paper.id}
                hover
                onClick={() => navigate(`/papers/${paper.id}`)}
              >
                <CardContent>
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-indigo-50 rounded-lg flex-shrink-0">
                      <FileText className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">
                        {paper.title || 'Untitled Paper'}
                      </h3>
                      {paper.abstract && (
                        <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                          {paper.abstract}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-3">
                        {getStatusBadge(paper.processing_status)}
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <FolderOpen className="w-3 h-3" />
                          {getProjectName(paper.project_id)}
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
