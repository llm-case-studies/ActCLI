import React, { useEffect, useRef, useState } from 'react'

type ParticipantIn = { alias?: string, provider?: string, model_id?: string, bound_params?: any }

export function SeminarPage({ server }: { server: string }) {
  const [participants, setParticipants] = useState<string>(JSON.stringify([
    { alias:'llama', provider:'ollama', model_id:'codellama:13b' }
  ], null, 2))
  const [sessionId, setSessionId] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('Two sentences on Euler’s number')
  const [events, setEvents] = useState<string[]>([])
  const wsRef = useRef<WebSocket|null>(null)

  const create = async () => {
    const body = { participants: JSON.parse(participants), window_k: 2 }
    const r = await fetch(`${server}/sessions`, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) })
    const j = await r.json()
    const sid = j.session_id
    setSessionId(sid)
    // Open WS
    try {
      const ws = new WebSocket(`${server.replace('http','ws')}/sessions/${sid}/stream`)
      ws.onmessage = (ev) => setEvents(prev => [...prev, ev.data.toString()])
      wsRef.current = ws
    } catch {}
  }

  const roundStart = async () => {
    if (!sessionId) return
    await fetch(`${server}/sessions/${sessionId}/round/start`, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ prompt }) })
  }
  const roundNext = async () => {
    if (!sessionId) return
    await fetch(`${server}/sessions/${sessionId}/round/next`, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ prompt }) })
  }

  return (
    <div style={{display:'grid', gap:12}}>
      <div>
        <label>Participants (JSON array)</label>
        <textarea value={participants} onChange={e=>setParticipants(e.target.value)} rows={8} style={{width:'100%'}} />
      </div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <button onClick={create} style={btn}>Create Session</button>
        <input value={sessionId} onChange={e=>setSessionId(e.target.value)} placeholder="session id" style={{padding:6, border:'1px solid #ddd', borderRadius:6, width:240}} />
      </div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <input value={prompt} onChange={e=>setPrompt(e.target.value)} style={{flex:1, padding:6, border:'1px solid #ddd', borderRadius:6}} />
        <button onClick={roundStart} style={btn}>Start</button>
        <button onClick={roundNext} style={btn}>Next</button>
      </div>
      <div>
        <label>Events</label>
        <pre style={{background:'#fafafa', padding:8, border:'1px solid #eee', borderRadius:6, maxHeight:240, overflow:'auto'}}>{events.join('\n')}</pre>
      </div>
    </div>
  )
}

const btn: React.CSSProperties = { padding:'6px 10px', border:'1px solid #ccc', borderRadius:6, background:'#fafafa', cursor:'pointer' }

