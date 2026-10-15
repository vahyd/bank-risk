import { NavLink, Route, Routes } from 'react-router-dom'
import { role, setRole } from './api'
import Overview from './pages/Overview'
import Customers from './pages/Customers'
import CustomerProfile from './pages/CustomerProfile'
import CreditRisk from './pages/CreditRisk'
import Fraud from './pages/Fraud'
import AML from './pages/AML'
import Liquidity from './pages/Liquidity'
import RMWorkspace from './pages/RMWorkspace'
import Segmentation from './pages/Segmentation'
import Models from './pages/Models'
import Admin from './pages/Admin'

const NAV = [
  ['/', '◈', 'Executive Overview'],
  ['/customers', '▤', 'Customers & Profiles'],
  ['/credit-risk', '✓', 'Credit Risk'],
  ['/fraud', '▲', 'Fraud Monitoring'],
  ['/aml', '◉', 'AML & Investigations'],
  ['/liquidity', '≈', 'Liquidity Forecast'],
  ['/rm', '☰', 'RM Workspace'],
  ['/segmentation', '◎', 'Client Segmentation'],
  ['/models', '∑', 'Models & Data Quality'],
  ['/admin', '⚙', 'Admin & Audit'],
]

export default function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <b>Corporate Banking AI</b>
          <small>Open-source platform · v2.0</small>
        </div>
        {NAV.map(([path, ico, label]) => (
          <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span className="ico">{ico}</span>
            <span>{label}</span>
          </NavLink>
        ))}
        <div style={{ marginTop: 'auto', paddingTop: 12, borderTop: '1px solid var(--border)' }}>
          <select value={role()} onChange={(e) => setRole(e.target.value)} title="Demo role for RBAC">
            <option value="admin">admin</option>
            <option value="analyst">analyst</option>
            <option value="rm">rm</option>
            <option value="compliance">compliance</option>
            <option value="treasury">treasury</option>
          </select>
          <small className="muted">RBAC demo role · synthetic data</small>
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/customers/:id" element={<CustomerProfile />} />
          <Route path="/credit-risk" element={<CreditRisk />} />
          <Route path="/fraud" element={<Fraud />} />
          <Route path="/aml" element={<AML />} />
          <Route path="/liquidity" element={<Liquidity />} />
          <Route path="/rm" element={<RMWorkspace />} />
          <Route path="/segmentation" element={<Segmentation />} />
          <Route path="/models" element={<Models />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
    </div>
  )
}
