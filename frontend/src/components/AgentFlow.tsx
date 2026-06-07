import React from 'react'
import { GitBranch, Loader2 } from 'lucide-react'
import type { AgentStep } from '../types'
import { StepCard } from './StepCard'

interface AgentFlowProps {
  steps: AgentStep[]
  isStreaming: boolean
}

export const AgentFlow: React.FC<AgentFlowProps> = ({ steps, isStreaming }) => {
  return (
    <div className="card">
      <div className="card-title">
        <GitBranch size={14} />
        Pipeline de Agentes
        {isStreaming && (
          <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--neon-blue)', fontSize: '0.75rem', fontWeight: 500 }}>
            <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
            Procesando...
          </span>
        )}
      </div>

      {steps.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🤖</div>
          <p style={{ fontSize: '0.875rem' }}>El pipeline de agentes aparecerá aquí</p>
        </div>
      ) : (
        <div className="pipeline">
          {steps.map((step, i) => (
            <StepCard
              key={`${step.node}-${i}`}
              step={step}
              index={i}
              isLast={i === steps.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
