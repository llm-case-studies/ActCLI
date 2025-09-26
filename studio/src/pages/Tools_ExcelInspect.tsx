import React, { useState, useEffect, useCallback } from 'react'
import { useStudio } from '../store'
import { ReportViewer } from '../components/ReportViewer'
import { ArtifactsTree } from '../components/ArtifactsTree'

interface FileEntry {
  name: string
  path: string
  type: 'file' | 'dir'
  size?: number
}

interface JobStatus {
  id: string
  tool: string
  params: any
  created_at: number
  completed_at?: number
  ok?: boolean
  error?: string
  cancel_requested: boolean
}

export function ExcelInspectPage({ server }: { server: string }) {
  const s = useStudio()
  const [filePath, setFilePath] = useState<string>('')
  const [roFiles, setRoFiles] = useState<FileEntry[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [selectedArtifact, setSelectedArtifact] = useState<string>('')
  const [showArtifacts, setShowArtifacts] = useState<boolean>(false)

  // Advanced options
  const [password, setPassword] = useState<string>('')
  const [timeBudget, setTimeBudget] = useState<number>(30)
  const [skipVba, setSkipVba] = useState<boolean>(false)

  const loadRoFiles = async () => {
    try {
      const response = await s.fetcher('GET', `${server}/fs/ro/list?path=/mnt/ro&limit=100`)
      const data = await response.json()
      setRoFiles(data)
    } catch (e: any) {
      s.consolePush(`Failed to load RO files: ${e}`)
    }
  }

  useEffect(() => {
    loadRoFiles()
  }, [server])

  const startInspection = async () => {
    if (!filePath) {
      setError('Please select a file to inspect')
      return
    }

    setLoading(true)
    setError('')
    setJobId('')
    setJobStatus(null)

    try {
      // Prepare MCP call parameters
      const params = {
        path: filePath,
        ...(password && { password }),
        time_budget_s: timeBudget,
        skip_vba: skipVba,
      }

      const response = await s.fetcher('POST', `${server}/mcp`, {
        jsonrpc: '2.0',
        id: 'excel-inspect-' + Date.now(),
        method: 'tools/call',
        params: {
          name: 'excel_inspect',
          arguments: params,
        },
      }, {
        'MCP-Protocol-Version': '2025-06-18',
      })

      const result = await response.json()

      if (result.error) {
        throw new Error(result.error.message || 'MCP call failed')
      }

      const jobIdFromResult = result.result?.structuredContent?.job_id
      if (!jobIdFromResult) {
        throw new Error('No job ID returned from MCP call')
      }

      setJobId(jobIdFromResult)
      s.consolePush(`Excel inspection started: ${jobIdFromResult}`)

      // Start polling job status
      pollJobStatus(jobIdFromResult)
    } catch (e: any) {
      setError(String(e))
      s.consolePush(`Excel inspection failed: ${e}`)
    } finally {
      setLoading(false)
    }
  }

  const pollJobStatus = useCallback(async (id: string) => {
    if (!id) return

    try {
      const response = await s.fetcher('GET', `${server}/mcp/job/${id}`)
      const status = await response.json()
      setJobStatus(status)

      if (status.completed_at) {
        s.consolePush(`Excel inspection completed: ${status.ok ? 'SUCCESS' : 'FAILED'}`)
        if (status.ok) {
          // Show artifacts panel when job completes successfully
          setShowArtifacts(true)
        }
      } else {
        // Continue polling if not completed
        setTimeout(() => pollJobStatus(id), 2000)
      }
    } catch (e: any) {
      s.consolePush(`Job status check failed: ${e}`)
    }
  }, [server, s])

  const cancelJob = async () => {
    if (!jobId) return

    try {
      await s.fetcher('POST', `${server}/mcp/job/${jobId}/cancel`)
      s.consolePush(`Job cancellation requested: ${jobId}`)
    } catch (e: any) {
      s.consolePush(`Cancel failed: ${e}`)
    }
  }

  const renderFileSelector = () => (
    <div className="file-selector">
      <h3>📁 Select Excel File</h3>
      <div className="file-input-group">
        <input
          type="text"
          value={filePath}
          onChange={e => setFilePath(e.target.value)}
          placeholder="/mnt/ro/path/to/file.xlsx"
          className="file-path-input"
        />
        <button onClick={loadRoFiles} title="Refresh file list">
          🔄
        </button>
      </div>

      {roFiles.length > 0 && (
        <div className="file-list">
          <div className="file-list-header">Available files in /mnt/ro:</div>
          <div className="file-entries">
            {roFiles.map(file => (
              <div
                key={file.path}
                className={`file-entry ${filePath === file.path ? 'selected' : ''}`}
                onClick={() => setFilePath(file.path)}
              >
                <span className="file-icon">
                  {file.type === 'dir' ? '📁' :
                   file.name.toLowerCase().match(/\.(xlsx?|xlsm)$/i) ? '📊' : '📄'}
                </span>
                <span className="file-name">{file.name}</span>
                {file.size && <span className="file-size">({Math.round(file.size / 1024)}KB)</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderAdvancedOptions = () => (
    <div className="advanced-options">
      <h3>⚙️ Options</h3>
      <div className="option-group">
        <label>
          Password (for encrypted files):
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Optional password"
          />
        </label>
      </div>
      <div className="option-group">
        <label>
          Time budget (seconds):
          <input
            type="number"
            value={timeBudget}
            onChange={e => setTimeBudget(parseInt(e.target.value) || 30)}
            min="5"
            max="300"
          />
        </label>
      </div>
      <div className="option-group">
        <label>
          <input
            type="checkbox"
            checked={skipVba}
            onChange={e => setSkipVba(e.target.checked)}
          />
          Skip VBA analysis (faster)
        </label>
      </div>
    </div>
  )

  const renderJobStatus = () => {
    if (!jobId && !jobStatus) return null

    return (
      <div className="job-status">
        <h3>🔄 Inspection Status</h3>
        {jobId && (
          <div className="job-id">
            Job ID: <code>{jobId}</code>
          </div>
        )}

        {jobStatus && (
          <div className="status-details">
            <div className="status-row">
              <span>Status:</span>
              <span className={`status-badge ${jobStatus.completed_at ? (jobStatus.ok ? 'success' : 'error') : 'running'}`}>
                {jobStatus.completed_at
                  ? (jobStatus.ok ? '✅ Completed' : '❌ Failed')
                  : '⏳ Running'
                }
              </span>
            </div>

            {jobStatus.error && (
              <div className="status-row error">
                <span>Error:</span>
                <span>{jobStatus.error}</span>
              </div>
            )}

            <div className="status-row">
              <span>Started:</span>
              <span>{new Date(jobStatus.created_at * 1000).toLocaleString()}</span>
            </div>

            {jobStatus.completed_at && (
              <div className="status-row">
                <span>Completed:</span>
                <span>{new Date(jobStatus.completed_at * 1000).toLocaleString()}</span>
              </div>
            )}
          </div>
        )}

        {jobStatus && !jobStatus.completed_at && (
          <button onClick={cancelJob} className="cancel-btn">
            ⏹️ Cancel Inspection
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="excel-inspect-page">
      <div className="page-header">
        <h1>📊 Excel Inspector</h1>
        <p>Analyze Excel workbooks safely with detailed reports and security scanning.</p>
      </div>

      <div className="page-content">
        <div className="left-panel">
          {renderFileSelector()}
          {renderAdvancedOptions()}

          <div className="action-section">
            <button
              onClick={startInspection}
              disabled={loading || !filePath}
              className="inspect-btn"
            >
              {loading ? '⏳ Starting...' : '🔍 Start Inspection'}
            </button>
            {error && <div className="error-message">{error}</div>}
          </div>

          {renderJobStatus()}
        </div>

        {showArtifacts && (
          <div className="right-panel">
            <div className="artifacts-section">
              <div className="artifacts-tree-container">
                <ArtifactsTree
                  server={server}
                  onFileSelect={setSelectedArtifact}
                  selectedPath={selectedArtifact}
                />
              </div>

              <div className="report-viewer-container">
                <ReportViewer
                  server={server}
                  path={selectedArtifact}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}