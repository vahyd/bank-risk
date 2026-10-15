import { useEffect, useState } from 'react'
import { api, fmt } from '../api'
import { Badge, Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function AML() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/aml/dashboard').then(setData).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  const m = data.metrics || {}
  const g = data.graph_patterns || {}
  return (
    <>
      <PageTitle title="AML Monitoring & Investigations" sub="Rules + NetworkX circular-flow detection + anomaly prioritization" />
      <div className="grid kpis">
        <Kpi value={fmt(data.alerts?.length)} label="Suspicious alerts" />
        <Kpi value={fmt(g.circular_flows?.length || 0)} label="Circular transfer loops" />
        <Kpi value={fmt(g.rapid_movement?.length || 0)} label="Rapid movement patterns" />
        <Kpi value={m.precision?.toFixed?.(2) ?? '—'} label="Alert precision" />
        <Kpi value={fmt(data.reporting_threshold)} label="Reporting threshold" />
      </div>

      <div className="row mt">
        <div className="col" style={{ flex: 2 }}>
          <Card title="Suspicious activity alerts">
            <table>
              <thead><tr><th>ID</th><th>Customer</th><th>Severity</th><th>Title</th><th>Amount</th><th>Score</th><th>Status</th></tr></thead>
              <tbody>
                {(data.alerts || []).map((a: any) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>
                    <td>{a.customer_id}</td>
                    <td><Badge text={a.severity} /></td>
                    <td>{a.title}</td>
                    <td>{fmt(a.amount)}</td>
                    <td>{a.score?.toFixed?.(3)}</td>
                    <td><Badge text={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
        <div className="col">
          <Card title="Investigation cases">
            <table>
              <thead><tr><th>ID</th><th>Status</th><th>Analyst</th><th>Outcome</th></tr></thead>
              <tbody>
                {(data.cases || []).map((c: any) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td><Badge text={c.status} /></td>
                    <td>{c.analyst || '—'}</td>
                    <td>{c.outcome || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </div>

      <div className="mt">
        <Card title="Detected graph patterns (NetworkX)">
          <table>
            <thead><tr><th>Pattern</th><th>Detail</th><th>Amount</th></tr></thead>
            <tbody>
              {(g.circular_flows || []).slice(0, 10).map((c: any, i: number) => (
                <tr key={i}><td>Circular transfer</td><td>{JSON.stringify(c.accounts)}</td><td>{fmt(c.total_amount)}</td></tr>
              ))}
              {(g.rapid_movement || []).slice(0, 10).map((r: any, i: number) => (
                <tr key={`r${i}`}><td>Rapid movement</td><td>account {r.account_id} · in→out within {r.hours_between}h</td><td>{fmt(r.amount_in)}</td></tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  )
}
