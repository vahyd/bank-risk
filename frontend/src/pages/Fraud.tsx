import { useEffect, useState } from 'react'
import { api, fmt } from '../api'
import { Badge, Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function Fraud() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/fraud/dashboard').then(setData).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  const m = data.metrics || {}
  return (
    <>
      <PageTitle title="Fraud Detection & Prevention" sub="PyOD Isolation Forest + rules + NetworkX chains · batch + real-time API" />
      <div className="grid kpis">
        <Kpi value={fmt(data.alerts?.length)} label="Alerted transactions" />
        <Kpi value={m.precision?.toFixed?.(2) ?? '—'} label="Precision" />
        <Kpi value={m.recall?.toFixed?.(2) ?? '—'} label="Recall" />
        <Kpi value={m.auc?.toFixed?.(3) ?? '—'} label="AUC vs planted labels" />
        <Kpi value={data.threshold?.toFixed?.(2)} label="Alert threshold" />
      </div>

      <div className="mt">
        <Card title="Fraud alerts (priority order)">
          <table>
            <thead>
              <tr><th>ID</th><th>Customer</th><th>Severity</th><th>Title</th><th>Amount</th><th>Score</th><th>Status</th></tr>
            </thead>
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
    </>
  )
}
