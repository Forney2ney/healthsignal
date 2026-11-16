import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import {
  Activity, BrainCircuit, FlaskConical, LayoutDashboard, LogOut, ScanLine,
  ScrollText, ShieldAlert, Sparkles,
} from "lucide-react";
import { AuthProvider, useAuth, hasToken } from "./lib/auth";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ModelsPage from "./pages/ModelsPage";
import ImagingPage from "./pages/ImagingPage";
import ReportPage from "./pages/ReportPage";
import AssistantPage from "./pages/AssistantPage";
import ResearchPage from "./pages/ResearchPage";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/models", label: "Risk models", icon: Activity },
  { to: "/imaging", label: "Image analysis", icon: ScanLine },
  { to: "/reports", label: "Reports", icon: ScrollText },
  { to: "/assistant", label: "Assistant", icon: Sparkles },
  { to: "/research", label: "Research", icon: FlaskConical },
];

function Shell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <div className="bg-warn/10 border-b border-warn/25 text-xs text-warn px-4 py-2 text-center backdrop-blur">
        <ShieldAlert className="inline w-3.5 h-3.5 mr-1.5 -mt-0.5" />
        This project is a prototype and is not medical advice. HealthSignal is an educational/research prototype, not a clinically validated diagnostic system or a substitute for a qualified healthcare professional. Outputs are statistical research indicators, not diagnoses.
      </div>
      <div className="flex flex-1">
        <aside className="w-60 shrink-0 border-r border-white/10 p-4 hidden md:flex md:flex-col bg-panel/30">
          <div className="flex items-center gap-2 mb-1">
            <span className="grid place-items-center w-9 h-9 rounded-xl bg-accent/15 border border-accent/25">
              <BrainCircuit className="w-5 h-5 text-accent" />
            </span>
            <span className="font-semibold text-lg tracking-tight text-gradient">HealthSignal</span>
          </div>
          <div className="text-[11px] text-muted mb-7 pl-11">multimodal intelligence · prototype</div>
          <nav className="space-y-1">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition ${
                    isActive
                      ? "bg-accent/12 text-accent border border-accent/20"
                      : "text-slate-300 hover:bg-white/5 hover:text-white border border-transparent"
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-auto pt-6 border-t border-white/10 text-xs text-muted space-y-1.5">
            <div className="truncate text-slate-300">{user?.email}</div>
            <div className="capitalize">role: {user?.role}</div>
            <button
              className="mt-2 flex items-center gap-1.5 text-accent hover:underline"
              onClick={logout}
            >
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </button>
          </div>
        </aside>
        <main className="flex-1 p-5 md:p-7 overflow-x-hidden">
          {/* Mobile navigation */}
          <nav className="flex md:hidden gap-2 overflow-x-auto pb-3 -mt-1">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap px-3 py-1.5 rounded-full text-xs border ${
                    isActive ? "bg-accent/15 text-accent border-accent/30" : "bg-white/5 border-white/10 text-muted"
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" /> {label}
              </NavLink>
            ))}
          </nav>
          {children}
        </main>
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
