import React, { useEffect, useRef, useState } from 'react'
import { useStudio } from '../store'

type ParticipantIn = { alias?: string, provider?: string, model_id?: string, bound_params?: any }

export function SeminarPage({ server }: { server: string }) {
  const s = useStudio()
  const [participants, setParticipants] = useState<string>(JSON.stringify([
    { alias:'llama', provider:'ollama', model_id:'codellama:13b' }
  ], null, 2))
  const [sessionId, setSessionId] = useState<string>(s.sessionId)
  const [prompt, setPrompt] = useState<string>('Two sentences on Euler’s number')
  const wsRef = useRef<WebSocket|null>(null)
  const backoffRef = useRef<number>(1000)
  const stoppedRef = useRef<boolean>(false)

  const create = async () => {
    const body = { participants: JSON.parse(participants), window_k: 2 }
    const r = await s.fetcher('POST', `${server}/sessions`, body)
    const j = await r.json()
    const sid = j.session_id
    setSessionId(sid)
    s.setSessionId(sid)
    stoppedRef.current = false
    connectWS(sid)
  }

  const roundStart = async () => {
    if (!sessionId) return
    await s.fetcher('POST', `${server}/sessions/${sessionId}/round/start`, { prompt })
  }
  const roundNext = async () => {
    if (!sessionId) return
    await s.fetcher('POST', `${server}/sessions/${sessionId}/round/next`, { prompt })
  }
  const exportConv = async () => {
    if (!sessionId) return
    await s.fetcher('POST', `${server}/conversations/${sessionId}/export?format=md&compact=window&window_k=2`)
    s.consolePush('Export requested')
  }

  const disconnectWS = () => {
    stoppedRef.current = true
    try { wsRef.current?.close() } catch {}
    s.setWsConnected(false)
  }
  const connectWS = (sid: string) => {
    try {
      const ws = new WebSocket(`${server.replace('http','ws')}/sessions/${sid}/stream`)
      ws.onopen = () => { s.setWsConnected(true); backoffRef.current = 1000 }
      ws.onclose = () => {
        s.setWsConnected(false)
        if (stoppedRef.current) return
        const delay = Math.min(backoffRef.current, 30000)
        backoffRef.current = Math.min(delay * 2, 30000)
        setTimeout(() => { if (!document.hidden) connectWS(sid) }, delay)
      }
      ws.onmessage = (ev) => { const text = ev.data.toString(); s.wsPush(text); s.eventPush(text) }
      wsRef.current = ws
    } catch {}
  }

  return (
    <div style={{display:'grid', gap:12}}>
      {!s.wsConnected && sessionId && (
        <div style={{padding:8, border:'1px solid #cc9', background:'#fffbdd', borderRadius:6, display:'flex', gap:8, alignItems:'center'}}>
          <span>Offline</span>
          <button onClick={()=>{ backoffRef.current = 1000; connectWS(sessionId) }} style={btn}>Retry</button>
          <button onClick={disconnectWS} style={btn}>Disconnect</button>
        </div>
      )}
      <div>
        <label>Participants (JSON array)</label>
        <textarea value={participants} onChange={e=>setParticipants(e.target.value)} rows={8} style={{width:'100%'}} />
      </div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <button onClick={create} style={btn}>Create Session</button>
        <input value={sessionId} onChange={e=>setSessionId(e.target.value)} placeholder="session id" style={{padding:6, border:'1px solid #ddd', borderRadius:6, width:240}} />
        <button onClick={()=>connectWS(sessionId)} style={btn}>Connect WS</button>
        <button onClick={exportConv} style={btn}>Export</button>
      </div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <input value={prompt} onChange={e=>setPrompt(e.target.value)} style={{flex:1, padding:6, border:'1px solid #ddd', borderRadius:6}} />
        <button onClick={roundStart} style={btn}>Start</button>
        <button onClick={roundNext} style={btn}>Next</button>
      </div>
    </div>
  )
}

const btn: React.CSSProperties = { padding:'6px 10px', border:'1px solid #ccc', borderRadius:6, background:'#fafafa', cursor:'pointer' }
