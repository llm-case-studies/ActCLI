import React, { useEffect, useMemo, useState } from 'react'
import { useStudio } from '../store'

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
  const s = useStudio()
  const [rows, setRows] = useState<ModelItem[]>([])
  const [pricing, setPricing] = useState<PricingRow[]>([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [providerFilter, setProviderFilter] = useState<string>('')
  const [availableOnly, setAvailableOnly] = useState<boolean>(false)
  const [detail, setDetail] = useState<ModelItem|null>(null)

  const fetchAll = async () => {
    setLoading(true); setErr('')
    try {
      const r = await s.fetcher('GET', `${server}/models`)
      const j = await r.json()
      setRows(j)
      const p = await (await s.fetcher('GET', `${server}/pricing`)).json()
      setPricing(p)
    } catch (e:any) { setErr(String(e)) } finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [server])

  const prMap = new Map(pricing.map(p => [`${p.provider}:${p.id}`, p.pricing]))
  const filtered = useMemo(() => rows.filter(r => (
    (!providerFilter || r.provider.includes(providerFilter)) && (!availableOnly || r.available)
  )), [rows, providerFilter, availableOnly])

  return (
    <div style={{position:'relative'}}>
      <div style={{display:'flex', gap:8, alignItems:'center', marginBottom:12}}>
        <button onClick={fetchAll} disabled={loading} style={{padding:'6px 10px', border:'1px solid #ccc', borderRadius:6}}>Refresh</button>
        {loading && <span>Loading…</span>}
        {err && <span style={{color:'crimson'}}>{err}</span>}
        <input placeholder='Filter provider…' value={providerFilter} onChange={e=>setProviderFilter(e.target.value)} style={{padding:6, border:'1px solid #ccc', borderRadius:6}} />
        <label><input type='checkbox' checked={availableOnly} onChange={e=>setAvailableOnly(e.target.checked)} /> available</label>
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
          {filtered.map((r,i) => {
            const key = `${r.provider}:${r.id}`
            const pr = prMap.get(key)
            return (
              <tr key={i} onClick={()=>setDetail(r)} style={{cursor:'pointer'}} title='Open details'>
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

      {detail && (
        <ModelDetailDrawer
          server={server}
          item={detail}
          onClose={()=>setDetail(null)}
        />
      )}
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

const btn: React.CSSProperties = { padding:'6px 10px', border:'1px solid #ccc', borderRadius:6, background:'#fafafa', cursor:'pointer' }

function ModelDetailDrawer({ server, item, onClose }: { server: string, item: ModelItem, onClose: ()=>void }) {
  const s = useStudio()
  const [pricing, setPricing] = useState<PricingRow['pricing']|null>(null)
  const [history, setHistory] = useState<any[]>([])
  const [busy, setBusy] = useState(false)
  const [prompt, setPrompt] = useState('Quick sanity check: 2 lines about strengths and limits for actuarial use.')
  const [raw, setRaw] = useState(true)
  const [disableTools, setDisableTools] = useState(true)
  const [result, setResult] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [sessions, setSessions] = useState<any[]>([])
  const [targetSession, setTargetSession] = useState<string>('')

  useEffect(() => {
    (async()=>{
      // Pricing
      try {
        const plist: PricingRow[] = await (await s.fetcher('GET', `${server}/pricing`)).json()
        const key = `${item.provider}:${item.id}`
        const pr = plist.find(p => `${p.provider}:${p.id}`===key)?.pricing
        setPricing(pr || (item.source.includes('cli')? { model:'subscription', note:'CLI subscription/free tier' } as any : null))
      } catch {}
      // History
      try {
        const h = await (await s.fetcher('GET', `${server}/history?provider=${encodeURIComponent(item.provider)}&id=${encodeURIComponent(item.id)}&limit=50`)).json()
        setHistory(h)
      } catch {}
      // Sessions list
      try {
        const ss = await (await s.fetcher('GET', `${server}/sessions`)).json()
        setSessions(ss)
        if (!targetSession && ss.length>0) setTargetSession(ss[0].id)
      } catch {}
    })()
  }, [server, item.provider, item.id])

  const runChat = async () => {
    setBusy(true); setError(''); setResult('')
    try {
      const body = { provider: item.provider, model_id: item.id, prompt, raw, disable_tools: disableTools, timeout_s: 25 }
      const r = await s.fetcher('POST', `${server}/chat/one`, body)
      const j = await r.json()
      if (j.error) setError(j.error)
      setResult(j.text || '')
    } catch (e:any) { setError(String(e)) } finally { setBusy(false) }
  }

  const openSession = (sid: string) => { s.setSessionId(sid); s.openTab('seminar'); s.setActivePage('seminar' as any) }

  const addToSeminar = async () => {
    try {
      if (targetSession) {
        const participants = [{ alias: item.id, provider: item.provider, model_id: item.id }]
        await s.fetcher('PATCH', `${server}/sessions/${targetSession}`, { participants })
        s.consolePush(`Added ${item.provider}:${item.id} to ${targetSession}`)
        openSession(targetSession)
      } else {
        const body = { participants: [{ alias: item.id, provider: item.provider, model_id: item.id }], window_k: 2 }
        const r = await s.fetcher('POST', `${server}/sessions`, body)
        const j = await r.json(); const sid = j.session_id
        s.consolePush(`Created session ${sid} with ${item.provider}:${item.id}`)
        openSession(sid)
      }
    } catch (e:any) {
      s.consolePush(`Add to seminar failed: ${e}`)
    }
  }

  const useFastModel = async () => {
    const prov = item.provider
    let model = ''
    if (prov === 'codex_cli') model = 'gpt-5-codex'
    else if (prov === 'gemini_cli') model = 'gemini-1.5-flash-latest'
    else if (prov === 'claude_cli') model = 'claude-3-5-sonnet-20241022'
    else { s.consolePush('Fast model switch only for CLI providers'); return }
    try {
      const r = await s.fetcher('POST', `${server}/providers/cli/model`, { provider: prov, model })
      const j = await r.json();
      s.consolePush(j.ok? `Switched ${prov} to ${model}` : (j.hint || 'Switch failed'))
    } catch (e:any) { s.consolePush(`Switch failed: ${e}`) }
  }

  return (
    <div className='drawer'>
      <div className='drawer-head'>
        <div><strong>{item.provider}:{item.id}</strong></div>
        <div className='badges'>
          <span className='badge'>{item.available? 'available':'unavailable'}</span>
          <span className='badge'>{item.source}</span>
          {item.auth_mechanism && <span className='badge'>{item.auth_mechanism}{item.auth_state?`/${item.auth_state}`:''}</span>}
          <span className='badge'>{item.policy_allowed? 'policy:allowed':'policy:blocked'}</span>
        </div>
        <button onClick={onClose} className='drawer-x'>✕</button>
      </div>
      <div className='drawer-body'>
        <section>
          <h4>Identity</h4>
          <div className='kv'><span>provider</span><span>{item.provider}</span></div>
          <div className='kv'><span>id</span><span>{item.id}</span></div>
          <div className='kv'><span>source</span><span>{item.source}</span></div>
          {item.hint && <div className='kv'><span>hint</span><span>{item.hint}</span></div>}
        </section>
        <section>
          <h4>Pricing</h4>
          <div>{pricing? formatPricing(pricing) : '—'}</div>
        </section>
        <section>
          <h4>1×1 Chat</h4>
          <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} rows={4} style={{width:'100%'}} />
          <div style={{display:'flex', gap:12, alignItems:'center', margin:'6px 0'}}>
            <label><input type='checkbox' checked={raw} onChange={e=>setRaw(e.target.checked)} /> raw</label>
            <label><input type='checkbox' checked={disableTools} onChange={e=>setDisableTools(e.target.checked)} /> disable_tools</label>
            <button onClick={runChat} disabled={busy} style={btn}>Run</button>
          </div>
          {error && <div style={{color:'crimson', whiteSpace:'pre-wrap'}}>{error}</div>}
          {result && <pre style={{background:'#00000020', padding:8, borderRadius:6, whiteSpace:'pre-wrap'}}>{result}</pre>}
        </section>
        <section>
          <h4>Actions</h4>
          <div style={{display:'grid', gap:8}}>
            <div style={{display:'flex', gap:8, alignItems:'center'}}>
              <select value={targetSession} onChange={e=>setTargetSession(e.target.value)}>
                <option value=''>Create new session…</option>
                {sessions.map((x:any)=> (<option key={x.id} value={x.id}>{x.id} (r{x.round_idx})</option>))}
              </select>
              <button onClick={addToSeminar} style={btn}>Add to Seminar</button>
            </div>
            {(item.provider.endsWith('_cli')) && (
              <div>
                <button onClick={useFastModel} style={btn}>Use fast model</button>
              </div>
            )}
          </div>
        </section>
        <section>
          <h4>Recent Usage</h4>
          <div className='history'>
            {history.map((h:any, i:number) => (
              <div key={i} className='history-row'>
                <span className={h.ok? 'ok':'dim'}>{h.ok? 'ok':'err'}</span>
                <span>{h.latency_ms}ms</span>
                <button className='link' onClick={()=>openSession(h.session_id)} title='Open session in Seminar'>{h.session_id}</button>
                <span>r{h.round_index}</span>
                <span className='flex1 dim'>{h.text_excerpt}</span>
              </div>
            ))}
            {history.length===0 && <div className='dim'>No history yet</div>}
          </div>
        </section>
      </div>
    </div>
  )
}
