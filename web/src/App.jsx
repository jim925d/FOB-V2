import { Routes, Route } from 'react-router-dom';

import AppNav from '@/components/layout/AppNav';
import CrisisBar from '@/components/layout/CrisisBar';
import Footer from '@/components/layout/Footer';
import HomePage from '@/pages/HomePage';
import CareerPathfinderPage from '@/pages/CareerPathfinderPage';
import CareerMapPage from '@/pages/CareerMapPage';
import SkillBridgeExplorerPage from '@/pages/SkillBridgeExplorerPage';
import BenefitsPage from '@/pages/BenefitsPage';
import CommunitiesPage from '@/pages/CommunitiesPage';
import ERGDirectoryPage from '@/pages/ERGDirectoryPage';
import VANewsPage from '@/pages/VANewsPage';
import EmploymentNetworkingPage from '@/pages/EmploymentNetworkingPage';
import DashboardPage from '@/pages/DashboardPage';
import NotFoundPage from '@/pages/NotFoundPage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <CrisisBar />
      <AppNav />
      <main className="flex-1 pt-14">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/careers/pathfinder" element={<CareerPathfinderPage />} />
          <Route path="/careers/pathfinder/map" element={<CareerMapPage />} />
          <Route path="/skillbridge" element={<SkillBridgeExplorerPage />} />
          <Route path="/benefits" element={<BenefitsPage />} />
          <Route path="/communities" element={<CommunitiesPage />} />
          <Route path="/employment/ergs" element={<ERGDirectoryPage />} />
          <Route path="/employment/networking" element={<EmploymentNetworkingPage />} />
          <Route path="/news" element={<VANewsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
