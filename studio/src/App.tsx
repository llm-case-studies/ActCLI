import React, { useEffect, useMemo, useState } from 'react'
import { ModelsPage } from './pages/Models'
import { ProvidersPage } from './pages/Providers'
import { SeminarPage } from './pages/Seminar'
import { StatusPage } from './pages/Status'
import { LocationsPage } from './pages/Locations'
import { ExcelInspectPage } from './pages/Tools_ExcelInspect'
import { StudioProvider, useStudio } from './store'
import './theme.css'

type Page = 'seminar' | 'models' | 'providers' | 'status' | 'locations' | 'excel-inspect'

export default function App() {
  return (
    <StudioProvider>
      <VSCodeShell />
    </StudioProvider>
  )
}

function VSCodeShell() {
  const s = useStudio()
  const [sideWidth, setSideWidth] = useState<number>(() => Number(localStorage.getItem('side_w') || 280))
  const [panelH, setPanelH] = useState<number>(() => Number(localStorage.getItem('panel_h') || 180))
  const [resizing, setResizing] = useState<'side'|'panel'|null>(null)

  useEffect(()=> localStorage.setItem('side_w', String(sideWidth)), [sideWidth])
  useEffect(()=> localStorage.setItem('panel_h', String(panelH)), [panelH])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (resizing==='side') setSideWidth(Math.max(200, e.clientX - 56))
      if (resizing==='panel') setPanelH(Math.max(120, window.innerHeight - e.clientY - 24))
    }
    const onUp = () => setResizing(null)
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [resizing])

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMeta = e.ctrlKey || e.metaKey
      if (isMeta && e.key.toLowerCase()==='k') { e.preventDefault(); s.setPaletteOpen(true) }
      if (isMeta && e.key.toLowerCase()==='s') { e.preventDefault(); s.commands.export() }
      if (isMeta && e.key === 'Enter') { e.preventDefault(); s.commands.startOrNext() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [s])

  return (
    <div className={`app ${s.theme}`} style={{ ['--side-w' as any]: `${sideWidth}px` }}>
      {/* Activity Bar */}
      <div className="activity-bar">
        {ACTIVITIES.map(a => (
          <button key={a.id}
            className={s.activePage===a.id? 'active':''}
            title={a.label}
            onClick={() => s.openTab(a.id as Page)}>
            {a.icon}
          </button>
        ))}
        <div style={{flex:1}} />
        <button title="Toggle Theme" onClick={s.toggleTheme}>🌓</button>
      </div>

      {/* Side Bar */}
      <div className="side-bar">
        <SideBarContent />
      </div>
      <div className="side-resizer" onMouseDown={()=>setResizing('side')} />

      {/* Main Column */}
      <div className="main-col">
        {/* Editor Tabs */}
        <div className="editor-tabs">
          {s.openTabs.map(t => (
            <div key={t}
              className={`tab ${s.activePage===t? 'active':''}`}
              onClick={() => s.setActivePage(t)}>
              <span>{LABELS[t]}</span>
              {t!=='seminar' && <button className="tab-x" onClick={(e)=>{ e.stopPropagation(); s.closeTab(t) }}>✕</button>}
            </div>
          ))}
        </div>
        {/* Editor */}
        <div className="editor">
          {s.activePage==='seminar' && <SeminarPage server={s.server} />}
          {s.activePage==='models' && <ModelsPage server={s.server} />}
          {s.activePage==='providers' && <ProvidersPage server={s.server} />}
          {s.activePage==='status' && <StatusPage server={s.server} />}
          {s.activePage==='locations' && <LocationsPage server={s.server} />}
          {s.activePage==='excel-inspect' && <ExcelInspectPage server={s.server} />}
        </div>
        {/* Panel */}
        <div className="panel-resizer" onMouseDown={()=>setResizing('panel')} />
        <div className="panel" style={{ height: panelH }}>
          <div className="panel-tabs">
            {(['events','requests','ws','console'] as const).map(pt => (
              <button key={pt} className={s.panelTab===pt? 'active':''} onClick={()=>s.setPanelTab(pt)}>{pt}</button>
            ))}
          </div>
          <div className="panel-body">
            {s.panelTab==='events' && <pre>{s.events.join('\n')}</pre>}
            {s.panelTab==='requests' && (
              <div className="reqs">
                {s.requests.slice().reverse().map((r,i)=> (
                  <div key={i} className="req">
                    <span className={`status s${r.status}`}>{r.status}</span>
                    <span className="method">{r.method}</span>
                    <span className="url">{r.url}</span>
                    <span className="ms">{r.ms}ms</span>
                  </div>
                ))}
              </div>
            )}
            {s.panelTab==='ws' && <pre>{s.ws.join('\n')}</pre>}
            {s.panelTab==='console' && <pre>{s.console.join('\n')}</pre>}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="left">
          <strong>{s.status?.mode || 'OFFLINE'}</strong>
          <span>cloud_share:{String(s.status?.cloud_share ?? false)}</span>
        </div>
        <div className="center">
          <span>{LABELS[s.activePage]}</span>
          {s.sessionId && <span>session:{s.sessionId}</span>}
        </div>
        <div className="right">
          <input value={s.server} onChange={e=>s.setServer(e.target.value)} title="Semhost URL" />
          <span className={s.wsConnected? 'ok':'dim'}>{s.wsConnected? 'WS connected':'WS'}</span>
        </div>
      </div>

      {/* Command Palette */}
      {s.paletteOpen && <CommandPalette onClose={()=>s.setPaletteOpen(false)} />}
    </div>
  )
}

function SideBarContent() {
  const s = useStudio()
  // Basic Explorer with Sessions (recent), Artifacts (placeholder), Reports shortcuts
  const [health, setHealth] = useState<string>('')
  useEffect(()=>{
    (async()=>{
      try { const j = await fetch(`${s.server}/health`).then(r=>r.json()); setHealth(j.ok? 'healthy':'unknown') } catch { setHealth('unreachable') }
    })()
  }, [s.server])
  return (
    <div className="explorer">
      <div className="section">
        <div className="section-title">Server</div>
        <div className="kv"><span>URL</span><span title={s.server}>{s.server}</span></div>
        <div className="kv"><span>Health</span><span>{health}</span></div>
      </div>
      <div className="section">
        <div className="section-title">Sessions</div>
        <div className="list">
          {s.recentSessions.map(id => (
            <button key={id} onClick={()=>s.setSessionId(id)}>{id}</button>
          ))}
          {s.recentSessions.length===0 && <div className="dim">No recent sessions</div>}
        </div>
      </div>
      <div className="section">
        <div className="section-title">Artifacts</div>
        <div className="dim">Exports appear after running Export</div>
      </div>
      <div className="section">
        <div className="section-title">Reports</div>
        <a href="/docs/seminar-reports/2025-09-21-authentication-exam-seminar.md" target="_blank">Authentication Exam</a>
      </div>
    </div>
  )
}

function CommandPalette({ onClose }: { onClose: ()=>void }) {
  const s = useStudio()
  const [q, setQ] = useState('')
  const items = useMemo(() => [
    { id:'start', label:'Start Round', run: s.commands.start },
    { id:'next', label:'Next Round', run: s.commands.next },
    { id:'export', label:'Export Conversation', run: s.commands.export },
    { id:'open_models', label:'Open Models', run: () => s.openTab('models') },
    { id:'open_providers', label:'Open Providers', run: () => s.openTab('providers') },
    { id:'open_status', label:'Open Status', run: () => s.openTab('status') },
    { id:'open_locations', label:'Open Locations', run: () => s.openTab('locations') },
    { id:'refresh_models', label:'Refresh Models', run: () => s.consolePush('TODO: trigger models refresh') },
  ].filter(it => it.label.toLowerCase().includes(q.toLowerCase())), [q, s])
  return (
    <div className="palette" onClick={onClose}>
      <div className="palette-inner" onClick={e=>e.stopPropagation()}>
        <input autoFocus placeholder="Type a command" value={q} onChange={e=>setQ(e.target.value)} />
        <div className="palette-items">
          {items.map(it => (
            <button key={it.id} onClick={()=>{ it.run(); onClose() }}>{it.label}</button>
          ))}
          {items.length===0 && <div className="dim" style={{padding:8}}>No commands match</div>}
        </div>
      </div>
    </div>
  )
}

const ACTIVITIES = [
  { id:'seminar', label:'Seminar', icon:'📋' },
  { id:'models', label:'Models', icon:'📦' },
  { id:'providers', label:'Providers', icon:'🔌' },
  { id:'status', label:'Status', icon:'📶' },
  { id:'locations', label:'Locations', icon:'📁' },
  { id:'excel-inspect', label:'Excel Inspector', icon:'📊' },
] as const

const LABELS: Record<Page,string> = {
  seminar: 'Seminar', models: 'Models', providers: 'Providers', status: 'Status', locations: 'Locations', 'excel-inspect': 'Excel Inspector'
}
