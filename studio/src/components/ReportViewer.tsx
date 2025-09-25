import React, { useState, useEffect } from 'react'

interface ReportViewerProps {
  server: string
  path?: string
  onClose?: () => void
}

export function ReportViewer({ server, path, onClose }: ReportViewerProps) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    if (!path) {
      setContent('')
      return
    }

    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${server}/fs/out/get?path=${encodeURIComponent(path)}`)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        const text = await response.text()
        setContent(text)
      } catch (e: any) {
        setError(String(e))
        setContent('')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [server, path])

  if (!path) {
    return (
      <div className="report-viewer-empty">
        <div className="empty-state">
          <span>📄</span>
          <p>Select a file to view its contents</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="report-viewer-loading">
        <div className="loading-state">
          <span>⏳</span>
          <p>Loading {path}...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="report-viewer-error">
        <div className="error-state">
          <span>❌</span>
          <p>Error loading {path}</p>
          <pre>{error}</pre>
        </div>
      </div>
    )
  }

  const isMarkdown = path.toLowerCase().endsWith('.md')
  const isJson = path.toLowerCase().endsWith('.json')

  return (
    <div className="report-viewer">
      <div className="report-viewer-header">
        <span className="file-path">{path}</span>
        <div className="actions">
          <button onClick={() => navigator.clipboard?.writeText(content)} title="Copy to clipboard">
            📋
          </button>
          {onClose && (
            <button onClick={onClose} title="Close">
              ✕
            </button>
          )}
        </div>
      </div>
      <div className="report-viewer-content">
        {isMarkdown ? (
          <div className="markdown-content">
            <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
              {content}
            </pre>
          </div>
        ) : isJson ? (
          <div className="json-content">
            <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
              {JSON.stringify(JSON.parse(content), null, 2)}
            </pre>
          </div>
        ) : (
          <div className="text-content">
            <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
              {content}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}