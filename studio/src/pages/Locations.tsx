import React, { useEffect, useState } from 'react'

export function LocationsPage({ server }: { server: string }) {
  const [read, setRead] = useState<string>('')
  const [write, setWrite] = useState<string>('')
  const [msg, setMsg] = useState<string>('')
  const load = async () => {
    const d = await fetch(`${server}/locations`).then(r=>r.json())
    setRead((d.read||[]).join('\n'))
    setWrite((d.write||[]).join('\n'))
  }
  useEffect(()=>{ load() }, [server])
  const save = async () => {
    await fetch(`${server}/locations`, { method:'PATCH', headers:{'content-type':'application/json'}, body: JSON.stringify({ read: read.split('\n').filter(Boolean), write: write.split('\n').filter(Boolean) }) })
    setMsg('Saved')
    await load()
  }
  return (
    <div style={{display:'grid', gap:12}}>
      <div>
        <label>Read globs (one per line)</label>
        <textarea value={read} onChange={e=>setRead(e.target.value)} rows={6} style={{width:'100%'}} />
      </div>
      <div>
        <label>Write globs (one per line)</label>
        <textarea value={write} onChange={e=>setWrite(e.target.value)} rows={6} style={{width:'100%'}} />
      </div>
      <div>
        <button onClick={save} style={{padding:'6px 10px', border:'1px solid #ccc', borderRadius:6}}>Save</button>
        {msg && <span style={{marginLeft:8}}>{msg}</span>}
      </div>
    </div>
  )
}

