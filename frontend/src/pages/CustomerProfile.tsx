import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, fmt, pct } from '../api'
import { Badge, Card, ErrorBox, Loading, PageTitle } from '../components'

export default function CustomerProfile() {
  const { id } = useParams()
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api(`/customers/${id}`).then(setData).catch((e) => setErr(String(e)))
  }, [id])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  return (
    <>
      <PageTitle title={data.legal_name} sub={`${data.industry} · ${data.country} · ${data.registration_number}`} />
      <div className="grid kpis">
        <div className="card kpi"><div className="value">{fmt(data.annual_turnover / 1e6, 1)}M</div><div className="label">Annual turnover</div></div>
        <div className="card kpi"><div className="value">{pct(data.pd)}</div><div className="label">Default probability</div></div>
        <div className="card kpi"><div className="value">{data.segment ?? '—'}</div><div className="label">Segment</div></div>
        <div className="card kpi"><div className="value"><Badge text={data.kyc_status} /></div><div className="label">KYC status</div></div>
      </div>

      <div className="row mt">
        <div className="col">
          <Card title="Credit facilities">
            <table>
              <thead><tr><th>Type</th><th>Limit</th><th>Utilization</th><th>Grade</th><th>Status</th><th>Max days late</th></tr></thead>
              <tbody>
                {(data.facilities || []).map((f: any) => (
                  <tr key={f.id}>
                    <td>{f.facility_type}</td>
                    <td>{fmt(f.limit_amount)}</td>
                    <td>{pct(f.utilization)}</td>
                    <td>{f.risk_grade}</td>
                    <td><Badge text={f.status} /></td>
                    <td>{f.max_days_late}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
        <div className="col">
          <Card title="Accounts & activity">
            <table>
              <thead><tr><th>IBAN</th><th>Type</th><th>Balance</th></tr></thead>
              <tbody>
                {(data.accounts || []).map((a: any) => (
                  <tr key={a.id}><td>{a.iban}</td><td>{a.account_type}</td><td>{fmt(a.balance, 2)}</td></tr>
                ))}
              </tbody>
            </table>
            <p className="muted mt">
              {data.transaction_summary?.count} transactions · last activity {data.transaction_summary?.last_activity?.slice(0, 10)}
            </p>
          </Card>
        </div>
      </div>

      <div className="mt">
        <Card title="Recent alerts">
          {data.alerts?.length ? (
            <table>
              <thead><tr><th>App</th><th>Severity</th><th>Title</th><th>Score</th><th>Status</th></tr></thead>
              <tbody>
                {data.alerts.map((a: any) => (
                  <tr key={a.id}>
                    <td>{a.app}</td>
                    <td><Badge text={a.severity} /></td>
                    <td>{a.title}</td>
                    <td>{a.score?.toFixed(3)}</td>
                    <td><Badge text={a.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="muted">No alerts for this customer.</p>}
        </Card>
      </div>
    </>
  )
}
