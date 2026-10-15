import { useEffect, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, fmt } from '../api'
import { Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function Liquidity() {
  const [customers, setCustomers] = useState<any[]>([])
  const [cid, setCid] = useState<number | null>(null)
  const [scenario, setScenario] = useState('base')
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/customers?limit=200').then((d) => {
      setCustomers(d.items)
      if (d.items?.length) setCid(d.items[0].id)
    }).catch((e) => setErr(String(e)))
  }, [])

  useEffect(() => {
    if (cid === null) return
    setData(null)
    api(`/liquidity/forecast/${cid}?horizon_days=45&scenario=${scenario}`).then(setData).catch((e) => setErr(String(e)))
  }, [cid, scenario])

  if (err) return <ErrorBox msg={err} />

  const chartData = (data?.dates || []).map((d: string, i: number) => ({
    date: d.slice(5),
    closing: data?.closing_balance?.[i],
    inflow: data?.inflow_forecast?.[i],
    outflow: data?.outflow_forecast?.[i],
  }))

  return (
    <>
      <PageTitle title="Liquidity & Cash-Flow Forecasting" sub="ETS/rolling statistical forecast · 45-day horizon · scenario analysis" />
      <Card>
        <div className="row">
          <div className="col">
            <label className="muted">Customer</label>
            <select value={cid ?? ''} onChange={(e) => setCid(Number(e.target.value))}>
              {customers.map((c: any) => <option key={c.id} value={c.id}>{c.legal_name}</option>)}
            </select>
          </div>
          <div className="col">
            <label className="muted">Scenario</label>
            <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
              <option value="base">Base</option>
              <option value="delayed_receivables">Delayed receivables (−30% inflows)</option>
              <option value="sales_drop">Sales drop (−15% in, +5% out)</option>
              <option value="unexpected_outflows">Unexpected outflows (+25% out)</option>
            </select>
          </div>
        </div>
      </Card>

      {!data ? <Loading /> : (
        <>
          <div className="grid kpis mt">
            <Kpi value={fmt(data.current_balance)} label="Current balance" />
            <Kpi value={fmt(data.min_closing_balance)} label="Min closing balance (45d)" />
            <Kpi value={data.shortage_days?.length || 0} label="Shortage days" tone={data.shortage_alert ? 'var(--red)' : undefined} />
            <Kpi value={data.method} label="Method" />
          </div>
          <div className="mt">
            <Card title="Closing balance forecast">
              <div className="chart-box">
                <ResponsiveContainer>
                  <AreaChart data={chartData}>
                    <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
                    <XAxis dataKey="date" stroke="#8fa1bd" fontSize={10} />
                    <YAxis stroke="#8fa1bd" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#16223a', border: '1px solid #22304d', borderRadius: 8 }} />
                    <Area type="monotone" dataKey="closing" stroke="#4f8cff" fill="#4f8cff33" name="Closing balance" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </>
      )}
    </>
  )
}
