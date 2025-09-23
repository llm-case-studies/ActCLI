import React, { useEffect, useState } from 'react'
import { useStudio } from '../store'

type Status = { mode: 'OFFLINE'|'HYBRID', cloud_share: boolean, window_k: number, max_rounds?: number|null, read: string[], write: string[] }

export function StatusPage({ server }: { server: string }) {
  const s = useStudio()
  const [st, setSt] = useState<Status|null>(null)
  const [err, setErr] = useState('')
  const load = async () => {
    setErr('')
    try { setSt(await (await s.fetcher('GET', `${server}/status`)).json()) } catch(e:any){ setErr(String(e)) }
  }
  useEffect(()=>{ load() }, [server])

  const save = async () => {
    if (!st) return
    await s.fetcher('PATCH', `${server}/status`, st)
    await load()
  }

  if (!st) return <div>Loading… {err}</div>
  return (
    <div style={{display:'grid', gap:12}}>
      <div>
        <label>Mode: </label>
        <select value={st.mode} onChange={e=>setSt({...st, mode: e.target.value as any})}>
          <option>OFFLINE</option>
          <option>HYBRID</option>
        </select>
        <label style={{marginLeft:12}}>
          <input type='checkbox' checked={st.cloud_share} onChange={e=>setSt({...st, cloud_share:e.target.checked})} /> cloud_share
        </label>
      </div>
      <div>
        <label>window_k</label>
        <input type='number' value={st.window_k} onChange={e=>setSt({...st, window_k: parseInt(e.target.value||'0',10)})} />
        <label style={{marginLeft:12}}>max_rounds</label>
        <input type='number' value={st.max_rounds ?? ''} onChange={e=>setSt({...st, max_rounds: e.target.value? parseInt(e.target.value,10): null})} />
      </div>
      <div>
        <button onClick={save} style={{padding:'6px 10px', border:'1px solid #ccc', borderRadius:6}}>Save</button>
      </div>
    </div>
  )
}
