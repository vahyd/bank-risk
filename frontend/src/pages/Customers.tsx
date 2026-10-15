import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, fmt, pct } from '../api'
import { Badge, Card, ErrorBox, Loading, PageTitle } from '../components'

export default function Customers() {
  const [data, setData] = useState<any>(null)
  const [q, setQ] = useState('')
  const [err, setErr] = useState('')

  useEffect(() => {
    api(`/customers?limit=100&q=${encodeURIComponent(q)}`).then(setData).catch((e) => setErr(String(e)))
  }, [q])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  return (
    <>
      <PageTitle title="Corporate Customers" sub="Search & 360° profiles with entity resolution and KYC status" />
      <Card>
        <input placeholder="Search legal name, registration, industry, RM…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="mt">
          <table>
            <thead>
              <tr>
                <th>Customer</th><th>Industry</th><th>Country</th><th>Size</th>
                <th>Turnover</th><th>PD</th><th>Segment</th><th>KYC</th>
              </tr>
            </thead>
            <tbody>
              {(data.items || []).map((c: any) => (
                <tr key={c.id}>
                  <td><Link to={`/customers/${c.id}`}>{c.legal_name}</Link></td>
                  <td>{c.industry}</td>
                  <td>{c.country}</td>
                  <td>{c.size}</td>
                  <td>{fmt(c.annual_turnover / 1e6, 1)}M</td>
                  <td>{pct(c.pd)}</td>
                  <td>{c.segment ?? '—'}</td>
                  <td><Badge text={c.kyc_status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted mt">Showing {data.items?.length || 0} of {data.total}</p>
        </div>
      </Card>
    </>
  )
}
