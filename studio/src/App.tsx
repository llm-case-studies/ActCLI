import React, { useMemo, useState, useEffect } from 'react'
import { ModelsPage } from './pages/Models'
import { ProvidersPage } from './pages/Providers'
import { SeminarPage } from './pages/Seminar'
import { StatusPage } from './pages/Status'
import { LocationsPage } from './pages/Locations'

type Tab = 'models' | 'providers' | 'seminar' | 'status' | 'locations'

export default function App() {
  const [tab, setTab] = useState<Tab>('models')
  const [server, setServer] = useState<string>(() => localStorage.getItem('semhost_url') || 'http://127.0.0.1:7530')

  useEffect(() => {
    localStorage.setItem('semhost_url', server)
  }, [server])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', color: '#222' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderBottom: '1px solid #eee' }}>
        <strong>ActCLI Studio</strong>
        <nav style={{ display: 'flex', gap: 8 }}>
          {(['models','providers','seminar','status','locations'] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ddd', background: tab===t ? '#eef' : '#fafafa', cursor:'pointer' }}>{t}</button>
          ))}
        </nav>
        <div style={{ marginLeft: 'auto', display:'flex', alignItems:'center', gap:8 }}>
          <label>Server</label>
          <input value={server} onChange={e=>setServer(e.target.value)} style={{ padding:6, border:'1px solid #ddd', borderRadius:6, width: 260 }} />
        </div>
      </header>
      <main style={{ padding: 16 }}>
        {tab==='models' && <ModelsPage server={server} />}
        {tab==='providers' && <ProvidersPage server={server} />}
        {tab==='seminar' && <SeminarPage server={server} />}
        {tab==='status' && <StatusPage server={server} />}
        {tab==='locations' && <LocationsPage server={server} />}
      </main>
    </div>
  )
}

