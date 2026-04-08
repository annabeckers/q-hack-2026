import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './hooks/useTheme.tsx';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import SecurityIntelligence from './pages/SecurityIntelligence';
import CostIntelligence from './pages/CostIntelligence';
import ModelAnalytics from './pages/ModelAnalytics';
import Compliance from './pages/Compliance';
import AlertsFeed from './pages/AlertsFeed';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/leaks" element={<SecurityIntelligence />} />
        <Route path="/costs" element={<CostIntelligence />} />
        <Route path="/models" element={<ModelAnalytics />} />
        <Route path="/compliance" element={<Compliance />} />
        <Route path="/alerts" element={<AlertsFeed />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Layout>
        <AnimatedRoutes />
      </Layout>
    </ThemeProvider>
  );
}

export default App;
