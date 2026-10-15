import { useEffect, useState } from 'react'
import { api, fmt } from '../api'
import { Badge, Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function Segmentation() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/segmentation').then(setData).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  return (
    <>
      <PageTitle title="Corporate Client Segmentation" sub="K-means + HDBSCAN behavioral segments · validated for stability & business relevance" />
      <div className="grid kpis">
        <Kpi value={fmt(data.metrics?.n_customers)} label="Customers clustered" />
        <Kpi value={fmt(data.metrics?.k)} label="K-means clusters" />
        <Kpi value={data.metrics?.inertia?.toFixed?.(0) ?? '—'} label="Inertia" />
        <Kpi value={data.metrics?.hdbscan_available ? 'Yes' : 'No'} label="HDBSCAN available" />
      </div>

      <div className="mt">
        <Card title="Segment profiles">
          <table>
            <thead>
              <tr><th>Segment</th><th>Label</th><th>Customers</th><th>Avg turnover</th><th>Avg utilization</th><th>Top industries</th></tr>
            </thead>
            <tbody>
              {(data.profiles || []).map((p: any) => (
                <tr key={p.segment_id}>
                  <td><Badge text={`Segment ${p.segment_id}`} tone="blue" /></td>
                  <td>{p.label}</td>
                  <td>{p.n_customers}</td>
                  <td>{fmt(p.avg_turnover / 1e6, 1)}M</td>
                  <td>{p.avg_utilization?.toFixed?.(2)}</td>
                  <td>{(p.top_industries || []).join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <div className="mt">
        <Card title="Customers by segment">
          <table>
            <thead><tr><th>Customer</th><th>Industry</th><th>Size</th><th>Turnover</th><th>Segment</th></tr></thead>
            <tbody>
              {(data.customers || []).slice(0, 80).map((c: any) => (
                <tr key={c.customer_id}>
                  <td>{c.legal_name}</td>
                  <td>{c.industry}</td>
                  <td>{c.size}</td>
                  <td>{fmt(c.annual_turnover / 1e6, 1)}M</td>
                  <td><Badge text={`Segment ${c.segment}`} tone="blue" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  )
}
