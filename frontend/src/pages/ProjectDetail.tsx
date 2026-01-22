import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  FlaskConical,
  Upload,
  Plus,
  Trash2,
  MessageSquare,
  Loader2,
  Search,
  FolderOpen,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { projectsApi, papersApi, experimentsApi } from '../lib/api-service';
import type { Project, Paper, Experiment } from '../types';
import { Modal, Button, Input, Textarea, Badge, EmptyState, Card, CardContent } from '../components/ui';

type Tab = 'papers' | 'experiments';

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = parseInt(id || '0');

  const [project, setProject] = useState<Project | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>('papers');
  const [loading, setLoading] = useState(true);

  // Paper upload state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  // Experiment create state
  const [showExperimentModal, setShowExperimentModal] = useState(false);
  const [newExperiment, setNewExperiment] = useState({ title: '', goal: '', protocol: '' });
  const [creatingExperiment, setCreatingExperiment] = useState(false);

  // Project Q&A state
  const [showQAModal, setShowQAModal] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [askingQuestion, setAskingQuestion] = useState(false);

  const [error, setError] = useState('');

  const fetchData = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const [projectData, papersData, experimentsData] = await Promise.all([
        projectsApi.get(projectId),
        papersApi.list(projectId),
        experimentsApi.list(projectId),
      ]);
      setProject(projectData);
      setPapers(papersData);
      setExperiments(experimentsData);
    } catch (err) {
      console.error('Failed to fetch project:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const handleUploadPaper = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setError('');
    try {
      await papersApi.upload(uploadFile, projectId);
      setShowUploadModal(false);
      setUploadFile(null);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload paper');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateExperiment = async () => {
    if (!newExperiment.title.trim()) {
      setError('Experiment title is required');
      return;
    }
    setCreatingExperiment(true);
    setError('');
    try {
      await experimentsApi.create(projectId, {
        title: newExperiment.title,
        goal: newExperiment.goal || undefined,
        protocol: newExperiment.protocol || undefined,
      });
      setShowExperimentModal(false);
      setNewExperiment({ title: '', goal: '', protocol: '' });
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create experiment');
    } finally {
      setCreatingExperiment(false);
    }
  };

  const handleDeletePaper = async (paperId: number) => {
    if (!confirm('Are you sure you want to delete this paper?')) return;
    try {
      await papersApi.delete(paperId);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete paper');
    }
  };

  const handleDeleteExperiment = async (experimentId: number) => {
    if (!confirm('Are you sure you want to delete this experiment?')) return;
    try {
      await experimentsApi.delete(experimentId);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete experiment');
    }
  };

  const handleAskProjectQuestion = async () => {
    if (!question.trim()) return;
    setAskingQuestion(true);
    setAnswer('');
    try {
      const response = await projectsApi.askQuestion(projectId, question);
      setAnswer(response.answer);
    } catch (err) {
      setAnswer(`Error: ${err instanceof Error ? err.message : 'Failed to get answer'}`);
    } finally {
      setAskingQuestion(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
        return <Badge variant="success">Completed</Badge>;
      case 'processing':
      case 'running':
        return <Badge variant="info">Processing</Badge>;
      case 'failed':
        return <Badge variant="error">Failed</Badge>;
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'paused':
        return <Badge variant="warning">Paused</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-6 md:p-10 flex flex-col items-center">
        <EmptyState
          icon={<FolderOpen className="w-8 h-8" />}
          title="Project not found"
          description="The project you're looking for doesn't exist."
          action={
            <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 flex flex-col items-center">
      <div className="w-full max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              {project.description && (
                <p className="text-gray-500 mt-1">{project.description}</p>
              )}
            </div>
            <Button
              icon={<MessageSquare className="w-4 h-4" />}
              onClick={() => setShowQAModal(true)}
            >
              Ask Project
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex gap-8">
            <button
              onClick={() => setActiveTab('papers')}
              className={`pb-4 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'papers'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Papers ({papers.length})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('experiments')}
              className={`pb-4 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'experiments'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4" />
                Experiments ({experiments.length})
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'papers' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Research Papers</h2>
              <Button
                icon={<Upload className="w-4 h-4" />}
                onClick={() => setShowUploadModal(true)}
              >
                Upload Paper
              </Button>
            </div>

            {papers.length === 0 ? (
              <Card>
                <CardContent>
                  <EmptyState
                    icon={<FileText className="w-8 h-8" />}
                    title="No papers yet"
                    description="Upload your first research paper to get started with Q&A."
                    action={
                      <Button
                        icon={<Upload className="w-4 h-4" />}
                        onClick={() => setShowUploadModal(true)}
                      >
                        Upload Paper
                      </Button>
                    }
                  />
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {papers.map((paper) => (
                  <Card
                    key={paper.id}
                    hover
                    onClick={() => navigate(`/papers/${paper.id}`)}
                  >
                    <CardContent>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className="p-3 bg-indigo-50 rounded-lg">
                            <FileText className="w-5 h-5 text-indigo-600" />
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">
                              {paper.title || 'Untitled Paper'}
                            </h3>
                            {paper.abstract && (
                              <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                                {paper.abstract}
                              </p>
                            )}
                            <div className="flex items-center gap-3 mt-2">
                              {getStatusBadge(paper.processing_status)}
                              {paper.processing_status === 'failed' && paper.processing_error && (
                                <span className="text-xs text-red-600 flex items-center gap-1">
                                  <AlertCircle className="w-3 h-3" />
                                  {paper.processing_error}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeletePaper(paper.id);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'experiments' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Experiments</h2>
              <Button
                icon={<Plus className="w-4 h-4" />}
                onClick={() => setShowExperimentModal(true)}
              >
                New Experiment
              </Button>
            </div>

            {experiments.length === 0 ? (
              <Card>
                <CardContent>
                  <EmptyState
                    icon={<FlaskConical className="w-8 h-8" />}
                    title="No experiments yet"
                    description="Create your first experiment to start logging runs."
                    action={
                      <Button
                        icon={<Plus className="w-4 h-4" />}
                        onClick={() => setShowExperimentModal(true)}
                      >
                        New Experiment
                      </Button>
                    }
                  />
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {experiments.map((experiment) => (
                  <Card
                    key={experiment.id}
                    hover
                    onClick={() => navigate(`/experiments/${experiment.id}`)}
                  >
                    <CardContent>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className="p-3 bg-purple-50 rounded-lg">
                            <FlaskConical className="w-5 h-5 text-purple-600" />
                          </div>
                          <div>
                            <h3 className="font-medium text-gray-900">{experiment.title}</h3>
                            {experiment.goal && (
                              <p className="text-sm text-gray-500 mt-1">{experiment.goal}</p>
                            )}
                            <div className="flex items-center gap-3 mt-2">
                              {getStatusBadge(experiment.status)}
                              <span className="text-xs text-gray-400 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(experiment.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteExperiment(experiment.id);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Upload Paper Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setUploadFile(null);
          setError('');
        }}
        title="Upload Paper"
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              className="hidden"
              id="paper-upload"
            />
            <label
              htmlFor="paper-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-10 h-10 text-gray-400 mb-3" />
              {uploadFile ? (
                <div>
                  <p className="text-gray-900 font-medium">{uploadFile.name}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-900 font-medium">Click to select PDF</p>
                  <p className="text-sm text-gray-500 mt-1">or drag and drop</p>
                </div>
              )}
            </label>
          </div>
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleUploadPaper} loading={uploading} disabled={!uploadFile}>
              Upload
            </Button>
          </div>
        </div>
      </Modal>

      {/* Create Experiment Modal */}
      <Modal
        isOpen={showExperimentModal}
        onClose={() => {
          setShowExperimentModal(false);
          setNewExperiment({ title: '', goal: '', protocol: '' });
          setError('');
        }}
        title="New Experiment"
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}
          <Input
            label="Title"
            value={newExperiment.title}
            onChange={(e) => setNewExperiment({ ...newExperiment, title: e.target.value })}
            placeholder="e.g., Neural Network Optimization"
            autoFocus
          />
          <Textarea
            label="Goal (optional)"
            value={newExperiment.goal}
            onChange={(e) => setNewExperiment({ ...newExperiment, goal: e.target.value })}
            placeholder="What are you trying to achieve?"
            rows={2}
          />
          <Textarea
            label="Protocol (optional)"
            value={newExperiment.protocol}
            onChange={(e) => setNewExperiment({ ...newExperiment, protocol: e.target.value })}
            placeholder="Describe your experimental approach..."
            rows={3}
          />
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="secondary" onClick={() => setShowExperimentModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateExperiment} loading={creatingExperiment}>
              Create Experiment
            </Button>
          </div>
        </div>
      </Modal>

      {/* Project Q&A Modal */}
      <Modal
        isOpen={showQAModal}
        onClose={() => {
          setShowQAModal(false);
          setQuestion('');
          setAnswer('');
        }}
        title="Ask About This Project"
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Ask questions about all indexed papers in this project. The AI will search
            through your documents to find relevant answers.
          </p>
          <div className="flex gap-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., What are the main findings about neural networks?"
              className="flex-1"
              onKeyDown={(e) => e.key === 'Enter' && handleAskProjectQuestion()}
            />
            <Button onClick={handleAskProjectQuestion} loading={askingQuestion}>
              <Search className="w-4 h-4" />
            </Button>
          </div>
          {answer && (
            <div className="bg-gray-50 rounded-lg p-4 mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Answer:</p>
              <p className="text-gray-900 whitespace-pre-wrap">{answer}</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
