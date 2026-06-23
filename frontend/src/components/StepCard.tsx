import React, { useState } from 'react'
import { ChevronDown, CheckCircle, XCircle, AlertTriangle, Loader, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react'
import type { AgentStep } from '../types'

interface StepCardProps {
  step: AgentStep
  index: number
  isLast: boolean
}

interface MagicCheck {
  real_mime: string
  expected_mime: string
  convergent: boolean
  mismatch_severity: 'none' | 'warning' | 'critical'
  detail: string
}

const NODE_LABELS: Record<string, string> = {
  extractor: 'Extractor',
  classifier: 'Clasificador',
  web_agent: 'Agente Web',
  crypto_agent: 'Agente Crypto',
  forensic_agent: 'Agente Forense',
  verdict: 'Veredicto',
}

// ── Magic badge ──────────────────────────────────────────────────────────────
const MagicBadge: React.FC<{ magic: MagicCheck }> = ({ magic }) => {
  const [showTooltip, setShowTooltip] = useState(false)

  const styles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontSize: '0.65rem',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    padding: '2px 7px',
    borderRadius: '999px',
    cursor: 'help',
    flexShrink: 0,
    position: 'relative',
    userSelect: 'none',
    transition: 'opacity 0.2s',
  }

  let badgeStyle: React.CSSProperties
  let icon: React.ReactNode
  let label: string

  if (magic.convergent) {
    badgeStyle = {
      ...styles,
      background: 'rgba(0, 255, 136, 0.12)',
      border: '1px solid rgba(0, 255, 136, 0.4)',
      color: 'var(--neon-green, #00ff88)',
    }
    icon = <ShieldCheck size={11} />
    label = 'Firma OK'
  } else if (magic.mismatch_severity === 'critical') {
    badgeStyle = {
      ...styles,
      background: 'rgba(255, 50, 50, 0.15)',
      border: '1px solid rgba(255, 80, 80, 0.6)',
      color: '#ff5555',
      animation: 'pulse 1.8s ease-in-out infinite',
    }
    icon = <ShieldX size={11} />
    label = `CRÍTICO · ${magic.real_mime}`
  } else {
    badgeStyle = {
      ...styles,
      background: 'rgba(255, 180, 0, 0.12)',
      border: '1px solid rgba(255, 180, 0, 0.45)',
      color: '#ffb400',
    }
    icon = <ShieldAlert size={11} />
    label = `Firma: ${magic.real_mime}`
  }

  return (
    <div
      style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span style={badgeStyle}>
        {icon}
        {label}
      </span>
      {showTooltip && (
        <div style={{
          position: 'absolute',
          bottom: 'calc(100% + 6px)',
          right: 0,
          background: 'rgba(15, 15, 25, 0.97)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '6px',
          padding: '8px 10px',
          fontSize: '0.68rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)',
          whiteSpace: 'nowrap',
          zIndex: 100,
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          lineHeight: 1.6,
          minWidth: '220px',
          maxWidth: '340px',
          whiteSpace: 'pre-wrap' as React.CSSProperties['whiteSpace'],
        }}>
          <div style={{ color: 'white', fontWeight: 700, marginBottom: '4px' }}>🔍 Verificación de firma</div>
          <div><span style={{ color: 'rgba(255,255,255,0.5)' }}>Declarado: </span>{magic.expected_mime}</div>
          <div><span style={{ color: 'rgba(255,255,255,0.5)' }}>Real:      </span>{magic.real_mime}</div>
          <div style={{ marginTop: '6px', color: magic.convergent ? 'var(--neon-green, #00ff88)' : '#ff5555', fontSize: '0.63rem' }}>
            {magic.detail}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────

export const StepCard: React.FC<StepCardProps> = ({ step, index, isLast }) => {
  const [expanded, setExpanded] = useState(false)
  const hasResult = step.result && Object.keys(step.result).length > 0

  // Extract magic_check if this is the extractor step
  const magicCheck = step.node === 'extractor' && step.result
    ? (step.result.magic_check as MagicCheck | undefined)
    : undefined

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

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: '2px' }}>
              {String(index + 1).padStart(2, '0')} · {NODE_LABELS[step.node] || step.node}
            </div>
            <div className="step-label">{step.label}</div>
          </div>

          {/* Magic badge — shown immediately in header, no expand needed */}
          {magicCheck && (
            <MagicBadge magic={magicCheck} />
          )}

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
