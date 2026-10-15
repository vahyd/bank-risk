import { useEffect, useState } from 'react'
import { api, fmt } from '../api'
import { Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function Models() {
  const [quality, setQuality] = useState<any>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/models/quality').then(setQuality).catch((e) => setErr(String(e)))
    api('/models/runs').then(setRuns).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!quality) return <Loading />

  return (
    <>
      <PageTitle title="Model Performance & Data Quality" sub="Reproducible evaluation · versioned model runs · data lineage" />
      <div className="grid kpis">
        <Kpi value={fmt(quality.customers)} label="Customers" />
        <Kpi value={fmt(quality.transactions)} label="Transactions" />
        <Kpi value={quality.missing_reference_pct + '%'} label="Missing references" />
        <Kpi value={quality.missing_counterparty_pct + '%'} label="Missing counterparties" />
        <Kpi value={fmt(quality.duplicate_txn_refs)} label="Duplicate txn refs" />
      </div>

      <div className="mt">
        <Card title="Model registry (training runs)">
          <table>
            <thead><tr><th>Model</th><th>Trained at</th><th>Status</th><th>Key metrics</th></tr></thead>
            <tbody>
              {runs.map((r: any) => (
                <tr key={r.id}>
                  <td>{r.name}</td>
                  <td>{r.trained_at?.slice(0, 19).replace('T', ' ')}</td>
                  <td>{r.status}</td>
                  <td className="muted">{JSON.stringify(r.metrics || {}).slice(0, 160)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  )
}
