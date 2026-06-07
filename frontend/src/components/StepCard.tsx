import React, { useState } from 'react'
import { ChevronDown, CheckCircle, XCircle, AlertTriangle, Loader } from 'lucide-react'
import type { AgentStep } from '../types'

interface StepCardProps {
  step: AgentStep
  index: number
  isLast: boolean
}

const NODE_LABELS: Record<string, string> = {
  extractor: 'Extractor',
  classifier: 'Clasificador',
  web_agent: 'Agente Web',
  crypto_agent: 'Agente Crypto',
  forensic_agent: 'Agente Forense',
  verdict: 'Veredicto',
}

export const StepCard: React.FC<StepCardProps> = ({ step, index, isLast }) => {
  const [expanded, setExpanded] = useState(false)
  const hasResult = step.result && Object.keys(step.result).length > 0

  const StatusIcon = () => {
    switch (step.status) {
      case 'running':
        return <div className="step-spinner" />
      case 'completed':
        return <CheckCircle size={16} style={{ color: 'var(--neon-green)', flexShrink: 0 }} />
      case 'error':
        return <XCircle size={16} style={{ color: 'var(--neon-red)', flexShrink: 0 }} />
      default:
        return <AlertTriangle size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
    }
  }

  return (
    <>
      <div
        className={`step-card ${step.status}`}
        style={{ animationDelay: `${index * 0.1}s` }}
      >
        <div
          className="step-header"
          onClick={() => hasResult && setExpanded(!expanded)}
          style={{ cursor: hasResult ? 'pointer' : 'default' }}
        >
          <div className={`step-status-dot ${step.status}`} />

          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>
              {String(index + 1).padStart(2, '0')} · {NODE_LABELS[step.node] || step.node}
            </div>
            <div className="step-label">{step.label}</div>
          </div>

          <StatusIcon />

          {hasResult && (
            <ChevronDown
              size={16}
              className={`step-chevron ${expanded ? 'expanded' : ''}`}
              style={{ marginLeft: '0.25rem' }}
            />
          )}
        </div>

        {expanded && hasResult && (
          <div className="step-body">
            <pre className="step-result">
              {JSON.stringify(step.result, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {!isLast && <div className="step-connector" />}
    </>
  )
}
