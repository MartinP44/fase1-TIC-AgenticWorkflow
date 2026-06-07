// Shared types for CTF Reviewer frontend

export interface AgentStep {
  node: string
  status: 'running' | 'completed' | 'error' | 'pending'
  label: string
  result: Record<string, unknown> | null
}

export interface Finding {
  severity: 'pass' | 'warning' | 'error'
  rule: string
  message: string
  field: string | null
}

export interface VerdictData {
  verdict: 'valid' | 'invalid' | 'insecure'
  score: number
  type: string
  findings: Finding[]
  classification_reason: string
}

export type ReviewPhase =
  | 'idle'
  | 'uploading'
  | 'streaming'
  | 'done'
  | 'error'
