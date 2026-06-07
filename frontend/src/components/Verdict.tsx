import React, { useState, useEffect, useRef } from 'react'
import { CheckCircle, XCircle, AlertTriangle, CheckSquare, AlertOctagon, ShieldAlert } from 'lucide-react'
import type { VerdictData, Finding } from '../types'

interface VerdictProps {
  data: VerdictData
}

const VERDICT_CONFIG = {
  valid: {
    emoji: '✅',
    label: 'VÁLIDO',
    description: 'El reto cumple con todas las reglas de negocio',
    className: 'valid',
    icon: CheckCircle,
  },
  invalid: {
    emoji: '❌',
    label: 'INVÁLIDO',
    description: 'El reto no cumple con los requisitos mínimos',
    className: 'invalid',
    icon: XCircle,
  },
  insecure: {
    emoji: '🔴',
    label: 'INSEGURO',
    description: 'El reto tiene problemas de seguridad críticos',
    className: 'insecure',
    icon: ShieldAlert,
  },
}

const TYPE_CONFIG: Record<string, { emoji: string; label: string }> = {
  web: { emoji: '🌐', label: 'WEB' },
  crypto: { emoji: '🔐', label: 'CRYPTO' },
  forensic: { emoji: '🔍', label: 'FORENSE' },
  unknown: { emoji: '❓', label: 'DESCONOCIDO' },
}

const SEVERITY_FILTERS = ['pass', 'warning', 'error'] as const
type SeverityFilter = typeof SEVERITY_FILTERS[number]

export const Verdict: React.FC<VerdictProps> = ({ data }) => {
  const { verdict, score, type, findings, classification_reason } = data
  const config = VERDICT_CONFIG[verdict] || VERDICT_CONFIG.invalid
  const typeInfo = TYPE_CONFIG[type] || TYPE_CONFIG.unknown

  const [activeFilters, setActiveFilters] = useState<Set<SeverityFilter>>(
    new Set(['pass', 'warning', 'error'])
  )
  const [animatedScore, setAnimatedScore] = useState(0)
  const animRef = useRef<number | null>(null)

  // Animate score ring
  useEffect(() => {
    let start = 0
    const duration = 1500
    const startTime = performance.now()

    const animate = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease out cubic
      setAnimatedScore(Math.round(eased * score))
      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate)
      }
    }

    animRef.current = requestAnimationFrame(animate)
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current) }
  }, [score])

  const toggleFilter = (f: SeverityFilter) => {
    setActiveFilters(prev => {
      const next = new Set(prev)
      if (next.has(f)) {
        if (next.size > 1) next.delete(f) // keep at least 1
      } else {
        next.add(f)
      }
      return next
    })
  }

  const filteredFindings = findings.filter(f => activeFilters.has(f.severity as SeverityFilter))

  // Score ring math
  const RADIUS = 48
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS
  const offset = CIRCUMFERENCE - (animatedScore / 100) * CIRCUMFERENCE

  const passCnt = findings.filter(f => f.severity === 'pass').length
  const warnCnt = findings.filter(f => f.severity === 'warning').length
  const errCnt = findings.filter(f => f.severity === 'error').length

  return (
    <div className={`verdict-card ${config.className}`}>
      {/* Type badge */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem' }}>
        <div className={`type-badge ${type}`}>
          {typeInfo.emoji} {typeInfo.label}
        </div>
      </div>

      {/* Verdict status */}
      <div className="verdict-status">{config.emoji} {config.label}</div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
        {config.description}
      </p>

      {classification_reason && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
          "{classification_reason}"
        </p>
      )}

      {/* Score ring */}
      <div className="score-ring-container">
        <div className="score-ring">
          <svg viewBox="0 0 120 120" width="120" height="120">
            <circle
              className="score-ring-bg"
              cx="60" cy="60"
              r={RADIUS}
            />
            <circle
              className={`score-ring-fill ${config.className}`}
              cx="60" cy="60"
              r={RADIUS}
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="score-text">
            <span className="score-number">{animatedScore}</span>
            <span className="score-label">/ 100</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-box passes">
          <div className="stat-number">{passCnt}</div>
          <div className="stat-label">✓ Superados</div>
        </div>
        <div className="stat-box warnings">
          <div className="stat-number">{warnCnt}</div>
          <div className="stat-label">⚠ Advertencias</div>
        </div>
        <div className="stat-box errors">
          <div className="stat-number">{errCnt}</div>
          <div className="stat-label">✕ Errores</div>
        </div>
      </div>

      {/* Findings filter */}
      {findings.length > 0 && (
        <>
          <div className="findings-filter" style={{ marginTop: '1.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', alignSelf: 'center' }}>Filtrar:</span>
            {SEVERITY_FILTERS.map(f => (
              <button
                key={f}
                id={`filter-${f}`}
                className={`filter-btn ${activeFilters.has(f) ? `active ${f}` : ''}`}
                onClick={() => toggleFilter(f)}
              >
                {f === 'pass' ? '✓ Superados' : f === 'warning' ? '⚠ Warnings' : '✕ Errores'}
                {' '}({findings.filter(fi => fi.severity === f).length})
              </button>
            ))}
          </div>

          <div className="findings">
            {filteredFindings.map((finding, i) => (
              <FindingItem key={i} finding={finding} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

const FindingItem: React.FC<{ finding: Finding }> = ({ finding }) => {
  const icon = {
    pass: <CheckSquare size={14} className="finding-icon" />,
    warning: <AlertTriangle size={14} className="finding-icon" />,
    error: <AlertOctagon size={14} className="finding-icon" />,
  }[finding.severity]

  return (
    <div className={`finding-item ${finding.severity}`}>
      {icon}
      <div className="finding-text">
        {finding.message}
        {finding.field && (
          <div className="finding-rule">campo: {finding.field}</div>
        )}
        <div className="finding-rule">{finding.rule}</div>
      </div>
    </div>
  )
}
