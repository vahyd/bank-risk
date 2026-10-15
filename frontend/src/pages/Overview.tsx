import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, fmt } from '../api'
import { Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function Overview() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/dashboard/overview').then(setData).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  const segData = Object.entries(data.segment_distribution || {}).map(([name, value]) => ({ name, value }))
  const industryData = (data.industry_mix || []).slice(0, 8).map((i: any) => ({ name: i.industry, value: i.count }))

  return (
    <>
      <PageTitle title="Executive Overview" sub="Synthetic corporate banking data · all six AI applications live" />
      <div className="grid kpis">
        <Kpi value={fmt(data.total_customers)} label="Corporate customers" />
        <Kpi value={fmt(data.total_transaction_value / 1e6, 1) + 'M'} label="Transaction value (total)" />
        <Kpi value={fmt(data.total_transaction_volume)} label="Transactions" />
        <Kpi value={fmt(data.credit_exposure / 1e6, 1) + 'M'} label="Credit exposure (EAD)" />
        <Kpi value={fmt(data.high_risk_customers)} label="High-risk customers" tone="var(--red)" />
        <Kpi value={fmt(data.fraud_alerts_open)} label="Fraud alerts open" tone="var(--amber)" />
        <Kpi value={fmt(data.aml_alerts_open)} label="AML alerts open" tone="var(--amber)" />
        <Kpi value={fmt(data.investigation_cases_open)} label="Investigations open" />
      </div>

      <div className="row mt">
        <div className="col">
          <Card title="Client segment distribution">
            <div className="chart-box">
              <ResponsiveContainer>
                <BarChart data={segData}>
                  <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#8fa1bd" fontSize={11} />
                  <YAxis stroke="#8fa1bd" fontSize={11} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#16223a', border: '1px solid #22304d', borderRadius: 8 }} />
                  <Bar dataKey="value" fill="#4f8cff" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
        <div className="col">
          <Card title="Industry mix">
            <table>
              <thead><tr><th>Industry</th><th>Customers</th></tr></thead>
              <tbody>
                {industryData.map((i: any) => (
                  <tr key={i.name}><td>{i.name}</td><td>{i.value}</td></tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </div>
      <p className="muted mt">
        Synthetic data only — for prototyping and demos. Models trained at {data.models_trained_at || 'startup'}.
      </p>
    </>
  )
}
