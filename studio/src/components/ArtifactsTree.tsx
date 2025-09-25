import React, { useState, useEffect } from 'react'

interface FileEntry {
  name: string
  path: string
  type: 'file' | 'dir'
  size?: number
}

interface ArtifactsTreeProps {
  server: string
  onFileSelect?: (path: string) => void
  selectedPath?: string
}

export function ArtifactsTree({ server, onFileSelect, selectedPath }: ArtifactsTreeProps) {
  const [entries, setEntries] = useState<FileEntry[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['out']))

  const load = async (path: string = 'out') => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${server}/fs/out/list?path=${encodeURIComponent(path)}`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setEntries(data)
    } catch (e: any) {
      setError(String(e))
      setEntries([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [server])

  const toggleDir = (path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
        // Load directory contents when expanding
        load(path)
      }
      return next
    })
  }

  const refresh = () => {
    load()
  }

  const formatFileSize = (bytes: number | undefined): string => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)}KB`
    return `${Math.round(bytes / (1024 * 1024))}MB`
  }

  const renderEntry = (entry: FileEntry, level: number = 0) => {
    const isSelected = selectedPath === entry.path
    const isExpanded = expandedDirs.has(entry.path)
    const indent = level * 16

    return (
      <div key={entry.path}>
        <div
          className={`tree-entry ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: indent }}
          onClick={() => {
            if (entry.type === 'dir') {
              toggleDir(entry.path)
            } else if (onFileSelect) {
              onFileSelect(entry.path)
            }
          }}
        >
          <span className="entry-icon">
            {entry.type === 'dir' ? (isExpanded ? '📂' : '📁') : '📄'}
          </span>
          <span className="entry-name" title={entry.path}>
            {entry.name}
          </span>
          {entry.type === 'file' && entry.size && (
            <span className="entry-size">
              {formatFileSize(entry.size)}
            </span>
          )}
        </div>
      </div>
    )
  }

  if (loading && entries.length === 0) {
    return (
      <div className="artifacts-tree">
        <div className="tree-header">
          <span>📁 Artifacts</span>
          <button onClick={refresh} title="Refresh" disabled>
            🔄
          </button>
        </div>
        <div className="tree-loading">
          <span>⏳</span>
          <span>Loading artifacts...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="artifacts-tree">
        <div className="tree-header">
          <span>📁 Artifacts</span>
          <button onClick={refresh} title="Refresh">
            🔄
          </button>
        </div>
        <div className="tree-error">
          <span>❌</span>
          <span>Error: {error}</span>
        </div>
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="artifacts-tree">
        <div className="tree-header">
          <span>📁 Artifacts</span>
          <button onClick={refresh} title="Refresh">
            🔄
          </button>
        </div>
        <div className="tree-empty">
          <span>📭</span>
          <span>No artifacts found</span>
        </div>
      </div>
    )
  }

  return (
    <div className="artifacts-tree">
      <div className="tree-header">
        <span>📁 Artifacts</span>
        <button onClick={refresh} title="Refresh" disabled={loading}>
          🔄
        </button>
      </div>
      <div className="tree-content">
        {entries.map(entry => renderEntry(entry))}
      </div>
      {loading && (
        <div className="tree-loading-indicator">
          <span>⏳</span>
        </div>
      )}
    </div>
  )
}