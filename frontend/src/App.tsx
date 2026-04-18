import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    const { token, loading } = useAuth();
    if (loading) return <div className="min-h-screen bg-black text-zinc-400 flex items-center justify-center">Loading...</div>;
    if (!token) return <Navigate to="/login" replace />;
    return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
        <Router>
            <div className="min-h-screen pb-12 bg-black text-zinc-100 font-sans">
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/" element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    } />
                </Routes>
            </div>
        </Router>
    </AuthProvider>
  );
}

export default App;
