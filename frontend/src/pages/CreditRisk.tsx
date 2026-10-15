import { useEffect, useState } from 'react'
import { Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, fmt, pct } from '../api'
import { Badge, Card, ErrorBox, Kpi, Loading, PageTitle } from '../components'

export default function CreditRisk() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/credit-risk/portfolio').then(setData).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <ErrorBox msg={err} />
  if (!data) return <Loading />

  const s = data.summary
  const cal = (data.calibration || []).map((c: any) => ({ name: `bin ${c.bin}`, predicted: c.mean_predicted, actual: c.fraction_positive }))

  return (
    <>
      <PageTitle title="Credit Risk Assessment" sub="XGBoost default model + logistic baseline · SHAP-lite explanations · MLflow-tracked" />
      <div className="grid kpis">
        <Kpi value={fmt(s.total_exposure / 1e6, 1) + 'M'} label="Total exposure (EAD)" />
        <Kpi value={fmt(s.total_expected_loss / 1e6, 2) + 'M'} label="Expected loss" />
        <Kpi value={pct(s.coverage_ratio)} label="Coverage ratio" />
        <Kpi value={fmt(s.n_facilities)} label="Facilities" />
      </div>

      <div className="row mt">
        <div className="col">
          <Card title="Model performance">
            <table>
              <tbody>
                <tr><td>AUC (XGBoost)</td><td><b>{data.metrics?.auc_xgboost?.toFixed?.(3) ?? '—'}</b></td></tr>
                <tr><td>AUC (Logistic baseline)</td><td>{data.metrics?.auc_logistic?.toFixed?.(3) ?? '—'}</td></tr>
                <tr><td>Brier score</td><td>{data.metrics?.brier_score?.toFixed?.(4) ?? '—'}</td></tr>
                <tr><td>Precision / Recall / F1</td><td>{data.metrics?.precision?.toFixed?.(2)} / {data.metrics?.recall?.toFixed?.(2)} / {data.metrics?.f1?.toFixed?.(2)}</td></tr>
              </tbody>
            </table>
          </Card>
        </div>
        <div className="col">
          <Card title="Calibration curve (predicted vs actual)">
            <div className="chart-box">
              <ResponsiveContainer>
                <LineChart data={cal}>
                  <CartesianGrid stroke="#22304d" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#8fa1bd" fontSize={10} />
                  <YAxis stroke="#8fa1bd" fontSize={10} />
                  <Tooltip contentStyle={{ background: '#16223a', border: '1px solid #22304d', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="predicted" stroke="#4f8cff" name="Predicted" />
                  <Line type="monotone" dataKey="actual" stroke="#2fbf8f" name="Actual" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>

      <div className="row mt">
        <div className="col" style={{ flex: 2 }}>
          <Card title="Portfolio exposure">
            <table>
              <thead>
                <tr><th>Customer</th><th>Type</th><th>Limit</th><th>EAD</th><th>PD</th><th>LGD</th><th>EL</th><th>Grade</th><th>Status</th></tr>
              </thead>
              <tbody>
                {(data.items || []).slice(0, 60).map((r: any) => (
                  <tr key={r.facility_id}>
                    <td>{r.customer}</td>
                    <td>{r.facility_type}</td>
                    <td>{fmt(r.limit)}</td>
                    <td>{fmt(r.ead)}</td>
                    <td>{pct(r.pd)}</td>
                    <td>{pct(r.lgd)}</td>
                    <td>{fmt(r.expected_loss)}</td>
                    <td><Badge text={r.grade} /></td>
                    <td><Badge text={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
        <div className="col">
          <Card title="Top model drivers (XGBoost importance)">
            <table>
              <thead><tr><th>Feature</th><th>Importance</th></tr></thead>
              <tbody>
                {(data.importances || []).slice(0, 10).map((i: any) => (
                  <tr key={i.feature}><td>{i.feature}</td><td>{i.importance}</td></tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </div>
    </>
  )
}
