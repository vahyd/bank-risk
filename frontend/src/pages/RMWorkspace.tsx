import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, ErrorBox, Loading, PageTitle } from '../components'

export default function RMWorkspace() {
  const [customers, setCustomers] = useState<any[]>([])
  const [cid, setCid] = useState<number | null>(null)
  const [brief, setBrief] = useState<any>(null)
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    api('/customers?limit=200').then((d) => {
      setCustomers(d.items)
      if (d.items?.length) setCid(d.items[0].id)
    }).catch((e) => setErr(String(e)))
  }, [])

  useEffect(() => {
    if (cid === null) return
    api(`/rm/brief/${cid}`).then(setBrief).catch((e) => setErr(String(e)))
  }, [cid])

  const ask = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await api('/rm/chat', {
        method: 'POST',
        body: JSON.stringify({ query, customer_id: cid }),
      })
      setAnswer(r)
    } catch (e) {
      setErr(String(e))
    } finally {
      setLoading(false)
    }
  }

  if (err) return <ErrorBox msg={err} />

  return (
    <>
      <PageTitle title="Relationship Manager Workspace" sub="RAG over customer records + open-source LLM (Ollama Llama 3.1 / Mistral)" />
      <Card>
        <label className="muted">Customer</label>
        <select value={cid ?? ''} onChange={(e) => setCid(Number(e.target.value))}>
          {customers.map((c: any) => <option key={c.id} value={c.id}>{c.legal_name}</option>)}
        </select>
      </Card>

      {brief && (
        <div className="mt">
          <Card title="Meeting brief">
            <p><b>{brief.meeting_brief?.profile}</b></p>
            <p className="muted">Risk snapshot: {brief.meeting_brief?.risk_snapshot}</p>
            <ul>
              {(brief.meeting_brief?.recommended_actions || []).map((a: string, i: number) => <li key={i}>{a}</li>)}
            </ul>
          </Card>
        </div>
      )}

      <div className="mt">
        <Card title="Ask the RM copilot">
          <div className="row">
            <div className="col" style={{ flex: 3 }}>
              <input
                placeholder="e.g. Summarize this client's credit exposure and open alerts"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && ask()}
              />
            </div>
            <div className="col">
              <button className="btn" onClick={ask} disabled={loading}>{loading ? 'Thinking…' : 'Ask'}</button>
            </div>
          </div>
          {answer && (
            <div className="mt">
              <div className="card" style={{ background: 'var(--panel-2)' }}>
                <p style={{ whiteSpace: 'pre-wrap' }}>{answer.answer}</p>
                {answer.extractive_answer && (
                  <p className="muted">Extractive fallback: {answer.extractive_answer}</p>
                )}
                <p className="muted">Provider: {answer.provider} · model: {answer.model}</p>
                {answer.retrieved?.length ? (
                  <div>
                    <small className="muted">Sources:</small>
                    <ul>
                      {answer.retrieved.map((s: any, i: number) => (
                        <li key={i} className="muted">{s.title} ({s.source})</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </Card>
      </div>
    </>
  )
}
