import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Send,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  Bot,
  User,
} from 'lucide-react';
import { papersApi } from '../lib/api-service';
import type { Paper } from '../types';
import { Button, Badge, EmptyState, Card, CardContent } from '../components/ui';
import Notes from '../components/Notes';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function PaperDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const paperId = parseInt(id || '0');

  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);

  // Q&A state
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchPaper = async () => {
    if (!paperId) return;
    setLoading(true);
    try {
      const data = await papersApi.get(paperId);
      setPaper(data);
    } catch (err) {
      console.error('Failed to fetch paper:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPaper();
  }, [paperId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleAskQuestion = async () => {
    if (!question.trim()) return;

    const userMessage = question;
    setQuestion('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setAsking(true);

    try {
      const response = await papersApi.askQuestion(paperId, userMessage);
      setMessages((prev) => [...prev, { role: 'assistant', content: response.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Failed to get answer'}`,
        },
      ]);
    } finally {
      setAsking(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="success">
            <CheckCircle className="w-3 h-3 mr-1" />
            Text Extracted
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="p-6 md:p-10 flex flex-col items-center">
        <EmptyState
          icon={<FileText className="w-8 h-8" />}
          title="Paper not found"
          description="The paper you're looking for doesn't exist."
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
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-indigo-100 rounded-lg">
                  <FileText className="w-5 h-5 text-indigo-600" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {paper.title || 'Untitled Paper'}
                </h1>
              </div>
              {paper.abstract && (
                <p className="text-gray-600 mt-2 leading-relaxed">{paper.abstract}</p>
              )}
              <div className="flex items-center gap-3 mt-4">
                {getStatusBadge(paper.processing_status)}
                {paper.processing_status === 'failed' && paper.processing_error && (
                  <span className="text-sm text-red-600">{paper.processing_error}</span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Q&A Section */}
          <Card className="flex flex-col h-[600px]">
            <div className="p-5 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Ask Questions</h2>
              <p className="text-sm text-gray-500 mt-1">
                {paper.processing_status === 'completed'
                  ? 'Ask questions about this paper and get AI-powered answers.'
                  : 'Paper is still processing. Q&A will be available once complete.'}
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center text-gray-400">
                  <Bot className="w-12 h-12 mb-3 opacity-50" />
                  <p className="text-sm max-w-[200px]">
                    {paper.processing_status === 'completed'
                      ? 'Start a conversation by asking a question about this paper.'
                      : 'Waiting for paper processing to complete...'}
                  </p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-blue-600" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    </div>
                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-gray-600" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {asking && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-100 bg-gray-50/50">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={
                    paper.processing_status === 'completed' ? 'Ask a question...' : 'Processing paper...'
                  }
                  disabled={paper.processing_status !== 'completed' || asking}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleAskQuestion()}
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-gray-900 placeholder-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <Button
                  onClick={handleAskQuestion}
                  disabled={paper.processing_status !== 'completed' || asking || !question.trim()}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>

          {/* Notes Section */}
          <Card className="h-[600px] overflow-y-auto">
            <CardContent>
              <Notes paperId={paperId} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
