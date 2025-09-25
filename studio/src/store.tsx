import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

type Page = 'seminar' | 'models' | 'providers' | 'status' | 'locations' | 'excel-inspect'
type PanelTab = 'events' | 'requests' | 'ws' | 'console'

type RequestLog = { method: string, url: string, status: number, ms: number }
type StatusShape = { mode: 'OFFLINE'|'HYBRID', cloud_share: boolean, window_k: number, max_rounds?: number|null, read: string[], write: string[] }

type StudioCtx = {
  server: string; setServer: (v: string) => void
  status: StatusShape | null; setStatus: (s: StatusShape|null) => void
  theme: 'theme-dark' | 'theme-light'; toggleTheme: () => void
  openTabs: Page[]; activePage: Page; setActivePage: (p: Page) => void; openTab: (p: Page) => void; closeTab: (p: Page) => void
  panelTab: PanelTab; setPanelTab: (t: PanelTab) => void
  sessionId: string; setSessionId: (id: string) => void; recentSessions: string[]
  wsConnected: boolean; setWsConnected: (b: boolean) => void
  events: string[]; eventPush: (e: string) => void
  ws: string[]; wsPush: (e: string) => void
  requests: RequestLog[]; fetcher: (method: string, url: string, body?: any, headers?: Record<string,string>) => Promise<Response>
  console: string[]; consolePush: (m: string) => void
  paletteOpen: boolean; setPaletteOpen: (b: boolean) => void
  commands: { start: ()=>void, next: ()=>void, export: ()=>void, startOrNext: ()=>void }
}

const C = createContext<StudioCtx|null>(null)

export function StudioProvider({ children }: { children: React.ReactNode }) {
  const [server, setServerState] = useState<string>(() => localStorage.getItem('semhost_url') || 'http://127.0.0.1:7530')
  const [status, setStatus] = useState<StatusShape|null>(null)
  const [theme, setTheme] = useState<'theme-dark'|'theme-light'>(() => (localStorage.getItem('theme') as any) || 'theme-dark')
  const [openTabs, setOpenTabs] = useState<Page[]>(() => (JSON.parse(localStorage.getItem('open_tabs')||'null') as Page[]|null) || ['seminar'])
  const [activePage, setActivePage] = useState<Page>(() => (localStorage.getItem('active_page') as Page) || 'seminar')
  const [panelTab, setPanelTab] = useState<PanelTab>('events')
  const [sessionId, setSessionIdState] = useState<string>(() => localStorage.getItem('session_id') || '')
  const [recentSessions, setRecentSessions] = useState<string[]>(() => (JSON.parse(localStorage.getItem('recent_sessions')||'[]')))
  const [wsConnected, setWsConnected] = useState<boolean>(false)
  const [events, setEvents] = useState<string[]>([])
  const [ws, setWs] = useState<string[]>([])
  const [requests, setRequests] = useState<RequestLog[]>([])
  const [consoleMsgs, setConsoleMsgs] = useState<string[]>([])
  const [paletteOpen, setPaletteOpen] = useState<boolean>(false)

  useEffect(() => { localStorage.setItem('semhost_url', server) }, [server])
  useEffect(() => { localStorage.setItem('theme', theme) }, [theme])
  useEffect(() => { localStorage.setItem('open_tabs', JSON.stringify(openTabs)) }, [openTabs])
  useEffect(() => { localStorage.setItem('active_page', activePage) }, [activePage])
  useEffect(() => { localStorage.setItem('session_id', sessionId); if (sessionId) setRecentSessions(prev => {
    const next = Array.from(new Set([sessionId, ...prev])).slice(0, 8)
    localStorage.setItem('recent_sessions', JSON.stringify(next))
    return next
  }) }, [sessionId])

  // Load status occasionally
  useEffect(() => {
    (async()=>{ try { const j = await fetch(`${server}/status`).then(r=>r.json()); setStatus(j) } catch {} })()
  }, [server])

  const setServer = (v: string) => setServerState(v)
  const toggleTheme = () => setTheme(prev => prev==='theme-dark'?'theme-light':'theme-dark')
  const openTab = (p: Page) => setOpenTabs(tabs => tabs.includes(p)? tabs : [...tabs, p])
  const closeTab = (p: Page) => setOpenTabs(tabs => tabs.filter(x => x!==p))
  const setSessionId = (id: string) => setSessionIdState(id)
  const eventPush = (e: string) => setEvents(prev => [...prev, e])
  const wsPush = (e: string) => setWs(prev => [...prev, e])
  const consolePush = (m: string) => setConsoleMsgs(prev => [...prev, m])
  const fetcher = async (method: string, url: string, body?: any, headers?: Record<string,string>) => {
    const t0 = performance.now()
    const r = await fetch(url, { method, headers: { 'content-type':'application/json', ...(headers||{}) }, body: body? JSON.stringify(body): undefined })
    const ms = Math.round(performance.now()-t0)
    setRequests(prev => [...prev, { method, url, status: r.status, ms }])
    return r
  }

  const commands = useMemo(() => ({
    start: async () => { if (!sessionId) return; await fetcher('POST', `${server}/sessions/${sessionId}/round/start`, { prompt: ' ' }) },
    next: async () => { if (!sessionId) return; await fetcher('POST', `${server}/sessions/${sessionId}/round/next`, { prompt: ' ' }) },
    export: async () => { if (!sessionId) return; const r = await fetcher('POST', `${server}/conversations/${sessionId}/export?format=md&compact=window&window_k=2`); if (r.ok) consolePush('Export created') },
    startOrNext: async () => { if (!sessionId) return; await commands.next() },
  }), [sessionId, server])

  const value: StudioCtx = {
    server, setServer,
    status, setStatus,
    theme, toggleTheme,
    openTabs, activePage, setActivePage, openTab, closeTab,
    panelTab, setPanelTab,
    sessionId, setSessionId, recentSessions,
    wsConnected, setWsConnected,
    events, eventPush,
    ws, wsPush,
    requests, fetcher,
    console: consoleMsgs, consolePush,
    paletteOpen, setPaletteOpen,
    commands,
  }

  return (
    <C.Provider value={value}>
      <div className={theme}>
        {children}
      </div>
    </C.Provider>
  )
}

export function useStudio() {
  const ctx = useContext(C)
  if (!ctx) throw new Error('StudioProvider missing')
  return ctx
}

