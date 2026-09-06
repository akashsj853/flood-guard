import { lazy, Suspense, useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import { useAuth } from './context/AuthContext'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const MapPage = lazy(() => import('./pages/Map'))
const Predictions = lazy(() => import('./pages/Predictions'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Simulator = lazy(() => import('./pages/Simulator'))
const CitizenMode = lazy(() => import('./pages/CitizenMode'))
const AnalyticsPage = lazy(() => import('./pages/Analytics'))

const PAGES = {
  dashboard: Dashboard,
  map: MapPage,
  predictions: Predictions,
  alerts: Alerts,
  simulator: Simulator,
  citizen: CitizenMode,
  analytics: AnalyticsPage,
}

export default function App() {
  const { user, loading, login, loginAdmin, register, registerAdmin, logout } = useAuth()
  const [page, setPage] = useState('dashboard')
  const [demo, setDemo] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('floodguard-theme') || 'dark')

  useEffect(() => {
    localStorage.setItem('floodguard-theme', theme)
  }, [theme])

  const [authView, setAuthView] = useState('landing')
  if (loading) return <PageLoading />
  if (!user && authView === 'landing') return <Landing onLogin={() => setAuthView('login')} onAdminLogin={() => setAuthView('admin-login')} onRegister={() => setAuthView('register')} />
  if (!user && authView === 'login') return <Login onSubmit={login} onBack={() => setAuthView('landing')} onRegister={() => setAuthView('register')} />
  if (!user && authView === 'admin-login') return <Login admin onSubmit={loginAdmin} onBack={() => setAuthView('landing')} onRegister={() => setAuthView('login')} onAdminRegister={() => setAuthView('admin-register')} />
  if (!user && authView === 'admin-register') return <Register admin onSubmit={registerAdmin} onBack={() => setAuthView('admin-login')} onLogin={() => setAuthView('admin-login')} />
  if (!user) return <Register onSubmit={register} onBack={() => setAuthView('landing')} onLogin={() => setAuthView('login')} />

  const isCitizen = user.role === 'citizen'
  const Page = isCitizen ? CitizenMode : (PAGES[page] || Dashboard)

  return (
    <div className={`app-shell min-h-screen text-slate-200 flex ${theme === 'light' ? 'theme-light' : ''}`}>
      {!isCitizen && <Sidebar active={page} onNavigate={setPage} />}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar demo={demo} user={user} onLogout={logout} onToggleDemo={() => setDemo((d) => !d)} theme={theme} onToggleTheme={() => setTheme((value) => value === 'dark' ? 'light' : 'dark')} />
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto">
          <Suspense fallback={<PageLoading />}>
            <Page demo={demo} />
          </Suspense>
        </main>
      </div>
    </div>
  )
}

function PageLoading() {
  return (
    <div className="space-y-4 animate-pulse" aria-label="Loading page">
      <div className="h-7 w-56 rounded bg-slate-800" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="h-36 rounded-2xl bg-slate-900" />
        <div className="h-36 rounded-2xl bg-slate-900" />
        <div className="h-36 rounded-2xl bg-slate-900" />
      </div>
      <div className="h-80 rounded-2xl bg-slate-900" />
    </div>
  )
}
