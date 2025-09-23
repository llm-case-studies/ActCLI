import React, { useEffect, useState } from 'react'

type ModelItem = {
  provider: string
  id: string
  source: string
  auth_mechanism?: string
  auth_state?: string | null
  policy_allowed?: boolean
  available: boolean
  hint?: string | null
}

type PricingRow = {
  provider: string
  id: string
  pricing: { model: string, unit?: string, input?: number, output?: number, currency?: string, note?: string }
}

export function ModelsPage({ server }: { server: string }) {
  const [rows, setRows] = useState<ModelItem[]>([])
  const [pricing, setPricing] = useState<PricingRow[]>([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const fetchAll = async () => {
    setLoading(true); setErr('')
    try {
      const r = await fetch(`${server}/models`)
      const j = await r.json()
      setRows(j)
      const p = await fetch(`${server}/pricing`).then(r=>r.json())
      setPricing(p)
    } catch (e:any) { setErr(String(e)) } finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [server])

  const prMap = new Map(pricing.map(p => [`${p.provider}:${p.id}`, p.pricing]))

  return (
    <div>
      <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:12}}>
        <button onClick={fetchAll} disabled={loading} style={{padding:'6px 10px', border:'1px solid #ccc', borderRadius:6}}>Refresh</button>
        {loading && <span>Loading…</span>}
        {err && <span style={{color:'crimson'}}>{err}</span>}
      </div>
      <table style={{ width:'100%', borderCollapse:'collapse' }}>
        <thead>
          <tr>
            <th style={th}>Provider</th>
            <th style={th}>Model</th>
            <th style={th}>Source</th>
            <th style={th}>Auth</th>
            <th style={th}>Policy</th>
            <th style={th}>Available</th>
            <th style={th}>Pricing</th>
            <th style={th}>Hint</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r,i) => {
            const key = `${r.provider}:${r.id}`
            const pr = prMap.get(key)
            return (
              <tr key={i}>
                <td style={td}>{r.provider}</td>
                <td style={td}>{r.id}</td>
                <td style={td}>{r.source}</td>
                <td style={td}>{r.auth_mechanism || ''}{r.auth_state?` (${r.auth_state})`:''}</td>
                <td style={td}>{r.policy_allowed? 'allowed' : 'blocked'}</td>
                <td style={td}>{r.available? 'yes':'no'}</td>
                <td style={td}>{pr? formatPricing(pr): ''}</td>
                <td style={td}>{r.hint || ''}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { textAlign:'left', borderBottom:'1px solid #ddd', padding:6 }
const td: React.CSSProperties = { borderBottom:'1px solid #f0f0f0', padding:6, fontSize:14 }

function formatPricing(p: PricingRow['pricing']) {
  if (p.model === 'subscription') return 'subscription'
  if (p.model === 'per-token') return `${p.input ?? ''}/${p.output ?? ''} per ${p.unit ?? ''}`
  if (p.model === 'free') return 'free'
  return p.note || p.model
}

