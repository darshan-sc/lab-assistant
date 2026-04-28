'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { projectsApi } from '../lib/api-service';
import { Button } from '../components/ui';

export default function JoinProject() {
  const params = useParams<{ code: string }>();
  const code = params?.code;
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(code ? 'loading' : 'error');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState(code ? '' : 'No invite code provided');

  useEffect(() => {
    if (!code) {
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
            <h2 className="text-xl font-semibold text-gray-900 mb-2">You&apos;re in!</h2>
            <p className="text-gray-500 mb-6">You&apos;ve been added to the project as a member.</p>
            <Button onClick={() => router.push(projectId ? `/projects/${projectId}` : '/')}>
              Go to Project
            </Button>
          </div>
        )}

        {status === 'error' && (
          <div>
            <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Could not join</h2>
            <p className="text-gray-500 mb-6">{errorMessage}</p>
            <Button onClick={() => router.push('/')}>Go to Dashboard</Button>
          </div>
        )}
      </div>
    </div>
  );
}
