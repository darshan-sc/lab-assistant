import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FlaskConical,
  Play,
  Plus,
  Trash2,
  Edit2,
  Loader2,
  Clock,
  CheckCircle,
  XCircle,
  Pause,
  Target,
  FileText,
  Settings,
  BarChart3,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { experimentsApi, runsApi } from '../lib/api-service';
import type { Experiment, ExperimentRun } from '../types';
import { Modal, Button, Badge, EmptyState, Card, CardContent, Input, Textarea } from '../components/ui';
import Notes from '../components/Notes';

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const experimentId = parseInt(id || '0');

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRun, setExpandedRun] = useState<number | null>(null);

  // Edit experiment state
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({ title: '', goal: '', protocol: '', results: '' });
  const [saving, setSaving] = useState(false);

  // Create run state
  const [showRunModal, setShowRunModal] = useState(false);
  const [newRun, setNewRun] = useState({ name: '', config: '' });
  const [creatingRun, setCreatingRun] = useState(false);

  // Update run state
  const [editingRun, setEditingRun] = useState<number | null>(null);
  const [runMetrics, setRunMetrics] = useState('');
  const [runStatus, setRunStatus] = useState('');

  const [error, setError] = useState('');

  const fetchData = async () => {
    if (!experimentId) return;
    setLoading(true);
    try {
      const [experimentData, runsData] = await Promise.all([
        experimentsApi.get(experimentId),
        runsApi.list(experimentId),
      ]);
      setExperiment(experimentData);
      setRuns(runsData);
      setEditData({
        title: experimentData.title,
        goal: experimentData.goal || '',
        protocol: experimentData.protocol || '',
        results: experimentData.results || '',
      });
    } catch (err) {
      console.error('Failed to fetch experiment:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [experimentId]);

  const handleSaveExperiment = async () => {
    setSaving(true);
    try {
      await experimentsApi.update(experimentId, {
        title: editData.title,
        goal: editData.goal || undefined,
        protocol: editData.protocol || undefined,
        results: editData.results || undefined,
      });
      setEditing(false);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save experiment');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (status: string) => {
    try {
      await experimentsApi.update(experimentId, { status });
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  const handleCreateRun = async () => {
    setCreatingRun(true);
    setError('');
    try {
      let config = undefined;
      if (newRun.config.trim()) {
        try {
          config = JSON.parse(newRun.config);
        } catch {
          setError('Invalid JSON in config field');
          setCreatingRun(false);
          return;
        }
      }
      await runsApi.create(experimentId, {
        run_name: newRun.name || undefined,
        config,
      });
      setShowRunModal(false);
      setNewRun({ name: '', config: '' });
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run');
    } finally {
      setCreatingRun(false);
    }
  };

  const handleUpdateRun = async (runId: number) => {
    try {
      let metrics = undefined;
      if (runMetrics.trim()) {
        try {
          metrics = JSON.parse(runMetrics);
        } catch {
          alert('Invalid JSON in metrics field');
          return;
        }
      }
      await runsApi.update(runId, {
        status: runStatus || undefined,
        metrics,
      });
      setEditingRun(null);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update run');
    }
  };

  const handleDeleteRun = async (runId: number) => {
    if (!confirm('Are you sure you want to delete this run?')) return;
    try {
      await runsApi.delete(runId);
      fetchData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete run');
    }
  };

  const startEditRun = (run: ExperimentRun) => {
    setEditingRun(run.id);
    setRunStatus(run.status);
    setRunMetrics(run.metrics ? JSON.stringify(run.metrics, null, 2) : '');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
        return <Badge variant="success">Completed</Badge>;
      case 'running':
        return <Badge variant="info">Running</Badge>;
      case 'failed':
        return <Badge variant="error">Failed</Badge>;
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'paused':
        return <Badge variant="warning">Paused</Badge>;
      case 'planned':
        return <Badge variant="default">Planned</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'done':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'running':
        return <Play className="w-4 h-4 text-blue-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'paused':
        return <Pause className="w-4 h-4 text-yellow-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!experiment) {
    return (
      <div className="p-6 md:p-10 flex flex-col items-center">
        <EmptyState
          icon={<FlaskConical className="w-8 h-8" />}
          title="Experiment not found"
          description="The experiment you're looking for doesn't exist."
          action={<Button onClick={() => navigate(-1)}>Go Back</Button>}
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
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>

          <Card>
            <CardContent>
              {editing ? (
                <div className="space-y-4">
                  <Input
                    label="Title"
                    value={editData.title}
                    onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                  />
                  <Textarea
                    label="Goal"
                    value={editData.goal}
                    onChange={(e) => setEditData({ ...editData, goal: e.target.value })}
                    rows={2}
                  />
                  <Textarea
                    label="Protocol"
                    value={editData.protocol}
                    onChange={(e) => setEditData({ ...editData, protocol: e.target.value })}
                    rows={3}
                  />
                  <Textarea
                    label="Results"
                    value={editData.results}
                    onChange={(e) => setEditData({ ...editData, results: e.target.value })}
                    rows={3}
                  />
                  {error && (
                    <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
                  )}
                  <div className="flex gap-2 justify-end">
                    <Button variant="secondary" onClick={() => setEditing(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleSaveExperiment} loading={saving}>
                      Save Changes
                    </Button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-purple-100 rounded-lg">
                        <FlaskConical className="w-6 h-6 text-purple-600" />
                      </div>
                      <div>
                        <h1 className="text-2xl font-bold text-gray-900">{experiment.title}</h1>
                        <div className="flex items-center gap-3 mt-2">
                          {getStatusBadge(experiment.status)}
                          <span className="text-sm text-gray-500">
                            Created {new Date(experiment.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<Edit2 className="w-4 h-4" />}
                        onClick={() => setEditing(true)}
                      >
                        Edit
                      </Button>
                      <select
                        value={experiment.status}
                        onChange={(e) => handleUpdateStatus(e.target.value)}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                      >
                        <option value="active">Active</option>
                        <option value="paused">Paused</option>
                        <option value="completed">Completed</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                    {experiment.goal && (
                      <div>
                        <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                          <Target className="w-4 h-4" />
                          Goal
                        </div>
                        <p className="text-gray-900">{experiment.goal}</p>
                      </div>
                    )}
                    {experiment.protocol && (
                      <div>
                        <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                          <FileText className="w-4 h-4" />
                          Protocol
                        </div>
                        <p className="text-gray-900">{experiment.protocol}</p>
                      </div>
                    )}
                    {experiment.results && (
                      <div>
                        <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
                          <BarChart3 className="w-4 h-4" />
                          Results
                        </div>
                        <p className="text-gray-900">{experiment.results}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Runs Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Experiment Runs</h2>
              <Button
                size="sm"
                icon={<Plus className="w-4 h-4" />}
                onClick={() => setShowRunModal(true)}
              >
                Log Run
              </Button>
            </div>

            {runs.length === 0 ? (
              <Card>
                <CardContent>
                  <EmptyState
                    icon={<Play className="w-8 h-8" />}
                    title="No runs yet"
                    description="Log your first experiment run to track progress."
                    action={
                      <Button
                        size="sm"
                        icon={<Plus className="w-4 h-4" />}
                        onClick={() => setShowRunModal(true)}
                      >
                        Log Run
                      </Button>
                    }
                  />
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {runs.map((run) => (
                  <Card key={run.id}>
                    <CardContent className="p-4">
                      <div
                        className="flex items-center justify-between cursor-pointer"
                        onClick={() => setExpandedRun(expandedRun === run.id ? null : run.id)}
                      >
                        <div className="flex items-center gap-3">
                          {getStatusIcon(run.status)}
                          <div>
                            <p className="font-medium text-gray-900">
                              {run.run_name || `Run #${run.id}`}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(run.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(run.status)}
                          {expandedRun === run.id ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                      </div>

                      {expandedRun === run.id && (
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          {editingRun === run.id ? (
                            <div className="space-y-3">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                  Status
                                </label>
                                <select
                                  value={runStatus}
                                  onChange={(e) => setRunStatus(e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                >
                                  <option value="planned">Planned</option>
                                  <option value="running">Running</option>
                                  <option value="done">Done</option>
                                  <option value="failed">Failed</option>
                                </select>
                              </div>
                              <Textarea
                                label="Metrics (JSON)"
                                value={runMetrics}
                                onChange={(e) => setRunMetrics(e.target.value)}
                                placeholder='{"accuracy": 0.95, "loss": 0.05}'
                                rows={3}
                              />
                              <div className="flex gap-2 justify-end">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setEditingRun(null)}
                                >
                                  Cancel
                                </Button>
                                <Button size="sm" onClick={() => handleUpdateRun(run.id)}>
                                  Save
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <>
                              {run.config && (
                                <div className="mb-3">
                                  <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                    <Settings className="w-3 h-3" />
                                    Config
                                  </div>
                                  <pre className="text-xs bg-gray-50 rounded p-2 overflow-x-auto">
                                    {JSON.stringify(run.config, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {run.metrics && (
                                <div className="mb-3">
                                  <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
                                    <BarChart3 className="w-3 h-3" />
                                    Metrics
                                  </div>
                                  <pre className="text-xs bg-gray-50 rounded p-2 overflow-x-auto">
                                    {JSON.stringify(run.metrics, null, 2)}
                                  </pre>
                                </div>
                              )}
                              <div className="flex gap-2 justify-end mt-3">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  icon={<Edit2 className="w-3 h-3" />}
                                  onClick={() => startEditRun(run)}
                                >
                                  Edit
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  icon={<Trash2 className="w-3 h-3" />}
                                  onClick={() => handleDeleteRun(run.id)}
                                  className="text-red-600 hover:bg-red-50"
                                >
                                  Delete
                                </Button>
                              </div>

                              {/* Notes for this run */}
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <Notes experimentRunId={run.id} />
                              </div>
                            </>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Experiment Notes Section */}
          <Card className="h-fit">
            <CardContent>
              <Notes experimentId={experimentId} />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Create Run Modal */}
      <Modal
        isOpen={showRunModal}
        onClose={() => {
          setShowRunModal(false);
          setNewRun({ name: '', config: '' });
          setError('');
        }}
        title="Log Experiment Run"
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
              {error}
            </div>
          )}
          <Input
            label="Run Name (optional)"
            value={newRun.name}
            onChange={(e) => setNewRun({ ...newRun, name: e.target.value })}
            placeholder="e.g., seed=42, baseline"
          />
          <Textarea
            label="Config (JSON, optional)"
            value={newRun.config}
            onChange={(e) => setNewRun({ ...newRun, config: e.target.value })}
            placeholder='{"learning_rate": 0.001, "batch_size": 32}'
            rows={4}
          />
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="secondary" onClick={() => setShowRunModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateRun} loading={creatingRun}>
              Log Run
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
