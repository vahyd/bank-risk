import { ReactNode } from 'react'

export function Card({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="card">
      {title && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>{title}</h3>
          {right}
        </div>
      )}
      {children}
    </div>
  )
}

export function Kpi({ value, label, sub, tone }: { value: string; label: string; sub?: string; tone?: string }) {
  return (
    <div className="card kpi">
      <div className="value" style={tone ? { color: tone } : undefined}>{value}</div>
      <div className="label">{label}</div>
      {sub && <div className="sub muted">{sub}</div>}
    </div>
  )
}

export function Badge({ text, tone }: { text: string; tone?: string }) {
  const t = tone || (text.toLowerCase().includes('high') || text.toLowerCase().includes('red') || text.toLowerCase().includes('defaulted')
    ? 'red'
    : text.toLowerCase().includes('amber') || text.toLowerCase().includes('watch') || text.toLowerCase().includes('open')
      ? 'amber'
      : text.toLowerCase().includes('closed') || text.toLowerCase().includes('performing') || text.toLowerCase().includes('passed')
        ? 'green'
        : 'gray')
  return <span className={`badge ${t}`}>{text}</span>
}

export function Loading() {
  return <div className="spin">Loading…</div>
}

export function ErrorBox({ msg }: { msg: string }) {
  return <div className="error">{msg}</div>
}

export function PageTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="topbar">
      <div>
        <h1>{title}</h1>
        {sub && <div className="muted">{sub}</div>}
      </div>
    </div>
  )
}
