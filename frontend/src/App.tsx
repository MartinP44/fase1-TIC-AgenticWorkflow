import React, { useState } from 'react'
import { ShieldAlert, FileText, Cpu, RefreshCw } from 'lucide-react'
import { FileUploader } from './components/FileUploader'
import { AgentFlow } from './components/AgentFlow'
import { Verdict } from './components/Verdict'
import { TemplateGuide } from './components/TemplateGuide'
import type { AgentStep, VerdictData, ReviewPhase } from './types'

export default function App() {
  const [phase, setPhase] = useState<ReviewPhase>('idle')
  const [file, setFile] = useState<File | null>(null)
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [verdict, setVerdict] = useState<VerdictData | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile)
    setPhase('uploading')
    setSteps([])
    setVerdict(null)
    setErrorMsg(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('/api/review/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Error subiendo el archivo')
      }

      const { job_id } = await response.json()
      startStreaming(job_id)
    } catch (err: any) {
      setErrorMsg(err.message || 'Error en la conexión con el servidor')
      setPhase('error')
    }
  }

  const startStreaming = (jobId: string) => {
    setPhase('streaming')
    const eventSource = new EventSource(`/api/review/stream/${jobId}`)

    eventSource.addEventListener('pipeline_start', (event) => {
      console.log('Pipeline started:', event.data)
    })

    eventSource.addEventListener('agent_step', (event) => {
      try {
        const step = JSON.parse(event.data) as AgentStep
        setSteps((prev) => {
          const idx = prev.findIndex((s) => s.node === step.node)
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = step
            return next
          }
          return [...prev, step]
        })
      } catch (e) {
        console.error('Error parsing agent_step:', e)
      }
    })

    eventSource.addEventListener('verdict', (event) => {
      try {
        const data = JSON.parse(event.data) as VerdictData
        setVerdict(data)
      } catch (e) {
        console.error('Error parsing verdict:', e)
      }
    })

    eventSource.addEventListener('done', () => {
      setPhase('done')
      eventSource.close()
    })

    eventSource.addEventListener('error', (event: any) => {
      try {
        const data = JSON.parse(event.data)
        setErrorMsg(data.message || 'Error durante el análisis')
      } catch {
        setErrorMsg('El pipeline falló inesperadamente')
      }
      setPhase('error')
      eventSource.close()
    })

    eventSource.onerror = () => {
      eventSource.close()
      setPhase((currentPhase) => {
        if (currentPhase === 'streaming') {
          setErrorMsg('Error en la conexión del streaming')
          return 'error'
        }
        return currentPhase
      })
    }
  }

  const reset = () => {
    setFile(null)
    setSteps([])
    setVerdict(null)
    setErrorMsg(null)
    setPhase('idle')
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">
          <div className="header-icon">
            <Cpu size={20} style={{ color: 'white' }} />
          </div>
          <div>
            <h1 className="header-title">Reviewer de Retos CTF</h1>
            <div className="header-subtitle">Sistema de Verificación Multi-Agente</div>
          </div>
        </div>
        <div className="header-badge">OLLAMA ENGINE</div>
      </header>

      <main className="main">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '2rem' }}>
          {/* Columna Izquierda: Carga de Archivos / Resultados */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div className="card">
              <div className="card-title">
                <FileText size={14} />
                Analizar Plantilla
              </div>
              <FileUploader
                onFileSelect={handleFileSelect}
                disabled={phase === 'uploading' || phase === 'streaming'}
              />

              {phase === 'error' && errorMsg && (
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.08)', borderRadius: '8px', border: '1px solid var(--neon-red)', display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                  <ShieldAlert size={16} style={{ color: 'var(--neon-red)', flexShrink: 0, marginTop: '2px' }} />
                  <div style={{ fontSize: '0.85rem', color: '#fca5a5' }}>
                    <div style={{ fontWeight: 600, marginBottom: '2px' }}>Error de Análisis</div>
                    {errorMsg}
                  </div>
                </div>
              )}

              {(phase === 'done' || phase === 'error') && (
                <button className="btn-primary" onClick={reset}>
                  <RefreshCw size={16} />
                  Analizar otro archivo
                </button>
              )}
            </div>

            {/* Guía de plantillas para autores de retos */}
            <TemplateGuide />

            {verdict && <Verdict data={verdict} />}
          </div>

          {/* Columna Derecha: Pipeline de Agentes */}
          <div>
            <AgentFlow steps={steps} isStreaming={phase === 'streaming'} />
          </div>
        </div>
      </main>
    </div>
  )
}
