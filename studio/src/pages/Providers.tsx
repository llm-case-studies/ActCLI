import React, { useEffect, useState } from 'react'
import { useStudio } from '../store'

type DoctorRow = { provider: string, binary: string, version: string, auth: string, hint: string }

export function ProvidersPage({ server }: { server: string }) {
  const s = useStudio()
  const [rows, setRows] = useState<DoctorRow[]>([])
  const [timeoutS, setTimeoutS] = useState<number>(12)
  const [debug, setDebug] = useState<boolean>(false)
  const [msg, setMsg] = useState<string>('')

  const load = async () => {
    setMsg('')
    const settings = await (await s.fetcher('GET', `${server}/providers/settings`)).json()
    setTimeoutS(settings.cli_probe_timeout_s)
    setDebug(!!settings.cli_debug)
    const d = await (await s.fetcher('GET', `${server}/providers/doctor`)).json()
    setRows(d)
  }
  useEffect(()=>{ load() }, [server])

  const saveSettings = async () => {
    await s.fetcher('PATCH', `${server}/providers/settings`, { cli_probe_timeout_s: timeoutS, cli_debug: debug })
    setMsg('Saved settings')
    await load()
  }

  const login = async (provider: string) => {
    await s.fetcher('POST', `${server}/auth/cli/login`, { provider })
    setMsg(`Launched ${provider}`)
  }

  const switchModel = async (provider: string) => {
    const model = prompt(`Model for ${provider} (e.g., gpt-5-codex, gemini-1.5-flash-latest)`)
    if (!model) return
    const r = await s.fetcher('POST', `${server}/providers/cli/model`, { provider, model })
    const j = await r.json()
    setMsg(j.ok? 'Model verified' : (j.hint || 'Model switch failed'))
  }

  return (
    <div>
      <div style={{display:'flex', gap:12, alignItems:'center', marginBottom:12}}>
        <button onClick={load} style={btn}>Refresh</button>
        <label>probe timeout (s)</label>
        <input type='number' value={timeoutS} onChange={e=>setTimeoutS(parseInt(e.target.value||'0',10))} style={{width:80, padding:6, border:'1px solid #ddd', borderRadius:6}} />
        <label><input type='checkbox' checked={debug} onChange={e=>setDebug(e.target.checked)} /> debug</label>
        <button onClick={saveSettings} style={btn}>Save</button>
        {msg && <span style={{color:'#555'}}>{msg}</span>}
      </div>
      <table style={{ width:'100%', borderCollapse:'collapse' }}>
        <thead>
          <tr><th style={th}>Provider</th><th style={th}>Binary</th><th style={th}>Version</th><th style={th}>Auth</th><th style={th}>Hint</th><th style={th}>Actions</th></tr>
        </thead>
        <tbody>
          {rows.map((r,i) => (
            <tr key={i}>
              <td style={td}>{r.provider}</td>
              <td style={td}>{r.binary}</td>
              <td style={td}>{r.version}</td>
              <td style={td}>{r.auth}</td>
              <td style={td}>{r.hint}</td>
              <td style={td}>
                <button onClick={()=>login(r.provider)} style={btn}>Login</button>
                <button onClick={()=>switchModel(r.provider)} style={btn}>Model…</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const th: React.CSSProperties = { textAlign:'left', borderBottom:'1px solid #ddd', padding:6 }
const td: React.CSSProperties = { borderBottom:'1px solid #f0f0f0', padding:6, fontSize:14 }
const btn: React.CSSProperties = { padding:'6px 10px', border:'1px solid #ccc', borderRadius:6, background:'#fafafa', cursor:'pointer' }
