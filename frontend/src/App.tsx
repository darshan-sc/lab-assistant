import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import {
  Login,
  Dashboard,
  ProjectDetail,
  PaperDetail,
  ExperimentDetail,
  Papers,
  Experiments,
  Settings,
  JoinProject,
} from './pages';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route
              path="/"
              element={
                <Layout>
                  <Dashboard />
                </Layout>
              }
            />
            <Route
              path="/projects/:id"
              element={
                <Layout>
                  <ProjectDetail />
                </Layout>
              }
            />
            <Route
              path="/papers"
              element={
                <Layout>
                  <Papers />
                </Layout>
              }
            />
            <Route
              path="/papers/:id"
              element={
                <Layout>
                  <PaperDetail />
                </Layout>
              }
            />
            <Route
              path="/experiments"
              element={
                <Layout>
                  <Experiments />
                </Layout>
              }
            />
            <Route
              path="/experiments/:id"
              element={
                <Layout>
                  <ExperimentDetail />
                </Layout>
              }
            />
            <Route
              path="/settings"
              element={
                <Layout>
                  <Settings />
                </Layout>
              }
            />
            <Route
              path="/join/:code"
              element={
                <Layout>
                  <JoinProject />
                </Layout>
              }
            />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
