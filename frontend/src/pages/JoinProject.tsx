import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { projectsApi } from '../lib/api-service';
import { Button } from '../components/ui';

export default function JoinProject() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!code) {
      setStatus('error');
      setErrorMessage('No invite code provided');
      return;
    }

    projectsApi
      .joinByCode(code)
      .then((result) => {
        setStatus('success');
        setProjectId(result.project_id);
      })
      .catch((err) => {
        setStatus('error');
        setErrorMessage(err instanceof Error ? err.message : 'Failed to join project');
      });
  }, [code]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-md w-full text-center">
        {status === 'loading' && (
          <div>
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Joining project...</h2>
            <p className="text-gray-500">Please wait while we add you to the project.</p>
          </div>
        )}

        {status === 'success' && (
          <div>
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">You're in!</h2>
            <p className="text-gray-500 mb-6">You've been added to the project as a member.</p>
            <Button onClick={() => navigate(projectId ? `/projects/${projectId}` : '/')}>
              Go to Project
            </Button>
          </div>
        )}

        {status === 'error' && (
          <div>
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Could not join</h2>
            <p className="text-gray-500 mb-6">{errorMessage}</p>
            <Button onClick={() => navigate('/')}>Go to Dashboard</Button>
          </div>
        )}
      </div>
    </div>
  );
}
