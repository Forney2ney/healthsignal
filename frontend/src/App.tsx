import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth, hasToken } from "./lib/auth";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ModelsPage from "./pages/ModelsPage";
import ImagingPage from "./pages/ImagingPage";
import ReportPage from "./pages/ReportPage";
import AssistantPage from "./pages/AssistantPage";
import ResearchPage from "./pages/ResearchPage";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/models", label: "Risk models" },
  { to: "/imaging", label: "Image analysis" },
  { to: "/reports", label: "Reports" },
  { to: "/assistant", label: "Assistant" },
  { to: "/research", label: "Research workspace" },
];

function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <div className="bg-warn/10 border-b border-warn/30 text-xs text-warn px-4 py-2 text-center">
        This project is a prototype and is not medical advice. HealthSignal is an educational/research prototype, not a clinically validated diagnostic system or a substitute for a qualified healthcare professional. Outputs are statistical research indicators, not diagnoses.
      </div>
      <div className="flex flex-1">
        <aside className="w-56 shrink-0 border-r border-white/10 p-4 hidden md:block">
          <div className="font-semibold text-lg mb-1">HealthSignal</div>
          <div className="text-xs text-muted mb-6">multimodal health intelligence · prototype</div>
          <nav className="space-y-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-lg text-sm ${isActive ? "bg-accent/15 text-accent" : "hover:bg-white/5"}`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-8 text-xs text-muted space-y-1">
            <div>{user?.email}</div>
            <div className="capitalize">role: {user?.role}</div>
            <button className="mt-2 text-accent hover:underline" onClick={logout}>
              Sign out
            </button>
          </div>
        </aside>
        <main className="flex-1 p-6 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}

function Guarded({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Shell>{children}</Shell>;
}

function AppInner() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<Guarded><DashboardPage /></Guarded>} />
      <Route path="/models" element={<Guarded><ModelsPage /></Guarded>} />
      <Route path="/imaging" element={<Guarded><ImagingPage /></Guarded>} />
      <Route path="/reports" element={<Guarded><ReportPage /></Guarded>} />
      <Route path="/assistant" element={<Guarded><AssistantPage /></Guarded>} />
      <Route path="/research" element={<Guarded><ResearchPage /></Guarded>} />
      <Route path="*" element={<Navigate to={hasToken() ? "/dashboard" : "/login"} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
