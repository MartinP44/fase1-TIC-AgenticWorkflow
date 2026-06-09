import React, { useEffect, useRef } from 'react'
import { Terminal as TerminalIcon } from 'lucide-react'

interface TerminalProps {
  logs: string[]
}

export const Terminal: React.FC<TerminalProps> = ({ logs }) => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs])

  const formatLine = (line: string, index: number) => {
    let color = 'rgba(34, 197, 94, 0.85)' // Default: matrix green
    let fontWeight = 'normal'

    // Simple parser to colorize log lines based on prefixes
    if (line.startsWith('>>> LLM CALL')) {
      color = 'var(--neon-cyan)'
      fontWeight = 'bold'
    } else if (line.startsWith('<<< LLM RESPONSE')) {
      color = 'var(--neon-green)'
      fontWeight = 'bold'
    } else if (line.startsWith('!!! LLM ERROR')) {
      color = 'var(--neon-red)'
      fontWeight = 'bold'
    } else if (line.startsWith('--- SYSTEM MESSAGE') || line.startsWith('--- SYSTEM')) {
      color = 'var(--neon-blue)'
      fontWeight = '600'
    } else if (line.startsWith('--- USER MESSAGE') || line.startsWith('--- USER')) {
      color = 'var(--neon-purple)'
      fontWeight = '600'
    } else if (line.startsWith('=')) {
      color = 'var(--text-muted)'
    } else if (line.startsWith('---') && line.endsWith('---')) {
      color = 'var(--text-secondary)'
    }

    return (
      <div 
        key={index} 
        style={{ 
          color, 
          fontWeight, 
          marginBottom: '2px', 
          whiteSpace: 'pre-wrap', 
          wordBreak: 'break-all',
          lineHeight: '1.4'
        }}
      >
        {line}
      </div>
    )
  }

  // Split logs into individual lines to allow line-by-line formatting
  const lines = logs.flatMap(log => log.split('\n'))

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '400px' }}>
      <div className="card-title" style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center' }}>
        <TerminalIcon size={14} style={{ color: 'var(--neon-cyan)' }} />
        Consola de Ejecución Ollama
        <span 
          style={{ 
            marginLeft: 'auto', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.4rem', 
            color: logs.length > 0 ? 'var(--neon-green)' : 'var(--text-muted)', 
            fontSize: '0.7rem',
            fontWeight: 500
          }}
        >
          {logs.length > 0 ? (
            <>
              <span className="step-status-dot completed" style={{ width: '6px', height: '6px', animation: 'pulse 1.5s infinite' }} />
              LIVE LOGGING
            </>
          ) : (
            'KERNEL IDLE'
          )}
        </span>
      </div>

      <div
        ref={containerRef}
        style={{
          flex: 1,
          backgroundColor: '#030712',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          overflowY: 'auto',
          scrollBehavior: 'smooth',
          boxShadow: 'inset 0 0 12px rgba(0, 0, 0, 0.9)'
        }}
      >
        {lines.length === 0 ? (
          <div 
            style={{ 
              color: 'var(--text-muted)', 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center', 
              height: '100%', 
              gap: '0.5rem' 
            }}
          >
            <div style={{ fontSize: '1.5rem', opacity: 0.5 }}>📟</div>
            <div>[NÚCLEO ESCUCHANDO] Esperando análisis para volcar logs de Ollama...</div>
          </div>
        ) : (
          lines.map((line, idx) => formatLine(line, idx))
        )}
      </div>
    </div>
  )
}
