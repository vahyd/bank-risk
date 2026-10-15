import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, ErrorBox, Loading, PageTitle } from '../components'

export default function Admin() {
  const [logs, setLogs] = useState<any[]>([])
  const [err, setErr] = useState('')
  const [training, setTraining] = useState(false)
  const [msg, setMsg] = useState('')

  const load = () => api('/admin/audit?limit=100').then(setLogs).catch((e) => setErr(String(e)))

  useEffect(() => {
    load()
  }, [])

  const retrain = async () => {
    setTraining(true)
    setMsg('')
    try {
      await api('/admin/train', { method: 'POST', body: JSON.stringify({}) })
      setMsg('Retraining complete — models refreshed.')
      load()
    } catch (e) {
      setErr(String(e))
    } finally {
      setTraining(false)
    }
  }

  if (err) return <ErrorBox msg={err} />

  return (
    <>
      <PageTitle title="Administration, Permissions & Audit" sub="RBAC · audit trails · retraining pipeline" />
      <Card>
        <button className="btn" onClick={retrain} disabled={training}>
          {training ? 'Retraining…' : 'Re-run data pipeline + retrain all models'}
        </button>
        {msg && <span className="muted" style={{ marginLeft: 12 }}>{msg}</span>}
      </Card>

      <div className="mt">
        <Card title="Audit log (recent 100)">
          <table>
            <thead><tr><th>Time</th><th>User</th><th>Role</th><th>Action</th><th>Resource</th></tr></thead>
            <tbody>
              {logs.map((l: any) => (
                <tr key={l.id}>
                  <td>{l.ts?.slice(0, 19).replace('T', ' ')}</td>
                  <td>{l.user}</td>
                  <td>{l.role}</td>
                  <td>{l.action}</td>
                  <td>{l.resource}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  )
}
