import React, { useState } from 'react'
import { BookOpen, Copy, Check, Globe, Lock, Search, ChevronDown } from 'lucide-react'

const TEMPLATES = {
  web: {
    icon: Globe,
    label: 'Web',
    color: 'cyan',
    extension: '.yaml',
    description: 'Retos de explotación web: SQLi, XSS, SSRF, File Upload, Auth Bypass, etc.',
    required: ['domain', 'url', 'port', 'http_method', 'endpoint', 'technology_stack', 'authentication_required', 'session_type', 'docker_image'],
    optional: ['size', 'ram'],
    content: `domain: web

# --- CAMPOS REQUERIDOS ---
url: "http://chall.midominio.com"     # URL base del servicio
port: 8080                            # Puerto TCP expuesto (1–65535)
http_method: "GET"                    # GET | POST | PUT | DELETE | PATCH
endpoint: "/login"                    # Ruta de entrada al reto
technology_stack: "Flask"             # Ej: Flask, Django, Node.js, PHP, Spring
authentication_required: false        # true | false
session_type: "NONE"                  # JWT | COOKIE | STATELESS | NONE | SESSION
docker_image: "tu-registro/reto:v1.0" # NUNCA usar :latest — usar versión fija

# --- CAMPOS OPCIONALES ---
size: "30MB"                          # Tamaño estimado de la imagen Docker
ram: "128MB"                          # RAM asignada al contenedor

# --- NOTAS INTERNAS (NO incluir contraseñas reales) ---
# description: "Breve descripción del tipo de vulnerabilidad"
`,
    rules: [
      { type: 'error', text: 'docker_image NO puede usar la etiqueta :latest' },
      { type: 'error', text: 'NO incluir passwords, API keys o secrets en el archivo' },
      { type: 'error', text: 'NO incluir claves privadas (BEGIN PRIVATE KEY)' },
      { type: 'error', text: 'NO escribir la flag directamente: FLAG{...}' },
      { type: 'warn', text: 'session_type debe ser uno de: JWT, COOKIE, STATELESS, NONE, SESSION, TOKEN, OAUTH' },
      { type: 'warn', text: 'http_method debe ser uno de: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS' },
    ]
  },
  crypto: {
    icon: Lock,
    label: 'Crypto',
    color: 'purple',
    extension: '.yaml',
    description: 'Retos de criptografía: RSA, AES, XOR, Vigenere, ECC, hashes, cifrados clásicos.',
    required: ['domain', 'algorithm', 'key_size', 'challenge_files', 'solve_script'],
    optional: [],
    content: `domain: crypto

# --- CAMPOS REQUERIDOS ---
algorithm: "AES"                      # Ej: RSA, AES, XOR, ECDSA, Vigenere, ROT13
key_size: 256                         # Tamaño de clave en bits (RSA ≥ 2048, AES ≥ 128)
challenge_files:                      # Archivos que se entregarán al participante
  - "ciphertext.enc"
  - "encryptor.py"
  - "public_key.pem"
solve_script: "decryptor.py"         # Nombre del script de solución de referencia

# --- REGLAS CRÍTICAS ---
# - NO usar MD5, SHA1 o DES como primitiva principal de cifrado
# - NO exponer la clave privada en este archivo
# - NO escribir la flag directamente: FLAG{...}
`,
    rules: [
      { type: 'error', text: 'NO usar MD5, SHA1 o DES como algoritmo principal' },
      { type: 'error', text: 'NO exponer claves privadas (BEGIN PRIVATE KEY)' },
      { type: 'error', text: 'NO escribir la flag directamente: FLAG{...}' },
      { type: 'warn', text: 'RSA: key_size debe ser ≥ 2048 bits' },
      { type: 'warn', text: 'AES: key_size debe ser ≥ 128 bits' },
    ]
  },
  forensic: {
    icon: Search,
    label: 'Forense',
    color: 'orange',
    extension: '.yaml o .md',
    description: 'Retos de análisis forense: pcap, volcados de memoria, imágenes de disco, logs, esteganografía.',
    required: ['artifact_type', 'artifact_file', 'difficulty', 'tags', 'author'],
    optional: ['required_tools'],
    content: `domain: forensic

# --- CAMPOS REQUERIDOS ---
artifact_type: "memory_dump"          # pcap | image | memory_dump | log | disk
artifact_file: "memory.raw"           # Nombre del archivo artefacto que se entrega
difficulty: "medium"                  # easy | medium | hard | expert
tags:                                 # Etiquetas de categoría del reto
  - "memory"
  - "windows"
  - "forensic"
author: "NombreDelAutor"             # Tu nombre o alias en la plataforma

# --- CAMPOS OPCIONALES ---
required_tools:                       # Herramientas necesarias para resolver el reto
  - "Volatility"
  - "Wireshark"

# --- REGLA CRÍTICA ---
# La flag NUNCA debe estar escrita en esta plantilla.
# Debe estar EMBEBIDA dentro del artefacto (pcap, imagen, dump, etc.)

# ALTERNATIVA: También puedes subir este reto como archivo .md (Markdown).
# El sistema inferirá automáticamente los campos desde el texto libre.
`,
    rules: [
      { type: 'error', text: 'La flag NUNCA se escribe en la plantilla, va embebida en el artefacto' },
      { type: 'error', text: 'artifact_type debe ser uno de: pcap, image, memory_dump, log, disk' },
      { type: 'warn', text: 'Se recomienda documentar las herramientas en required_tools' },
      { type: 'info', text: 'También puedes subir un .md con texto libre — el sistema inferirá los campos automáticamente' },
    ]
  }
}

type Domain = keyof typeof TEMPLATES

const COLOR_MAP = {
  cyan: {
    border: 'rgba(34,211,238,0.3)', bg: 'rgba(34,211,238,0.08)', text: '#22d3ee',
    tabActive: 'rgba(34,211,238,0.15)', badgeBg: 'rgba(34,211,238,0.1)', badgeBorder: 'rgba(34,211,238,0.25)'
  },
  purple: {
    border: 'rgba(168,85,247,0.3)', bg: 'rgba(168,85,247,0.08)', text: '#a855f7',
    tabActive: 'rgba(168,85,247,0.15)', badgeBg: 'rgba(168,85,247,0.1)', badgeBorder: 'rgba(168,85,247,0.25)'
  },
  orange: {
    border: 'rgba(249,115,22,0.3)', bg: 'rgba(249,115,22,0.08)', text: '#f97316',
    tabActive: 'rgba(249,115,22,0.15)', badgeBg: 'rgba(249,115,22,0.1)', badgeBorder: 'rgba(249,115,22,0.25)'
  },
}

const RULE_COLORS = {
  error: { bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)', text: '#fca5a5', dot: '#ef4444' },
  warn:  { bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.2)', text: '#fde68a', dot: '#fbbf24' },
  info:  { bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.2)', text: '#a5f3fc', dot: '#22d3ee' },
}

export const TemplateGuide: React.FC = () => {
  const [activeDomain, setActiveDomain] = useState<Domain>('web')
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(true)

  const tpl = TEMPLATES[activeDomain]
  const colors = COLOR_MAP[tpl.color as keyof typeof COLOR_MAP]
  const Icon = tpl.icon

  const handleCopy = () => {
    navigator.clipboard.writeText(tpl.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Header */}
      <div
        className="card-title"
        style={{ cursor: 'pointer', userSelect: 'none', marginBottom: expanded ? '1.25rem' : 0 }}
        onClick={() => setExpanded(v => !v)}
      >
        <BookOpen size={14} />
        Guía de Plantillas para Autores de Retos
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 400 }}>
          Cómo subir un reto
          <ChevronDown size={13} style={{ transition: 'transform 0.25s', transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }} />
        </span>
      </div>

      {expanded && (
        <>
          {/* Domain tabs */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
            {(Object.keys(TEMPLATES) as Domain[]).map(d => {
              const t = TEMPLATES[d]
              const c = COLOR_MAP[t.color as keyof typeof COLOR_MAP]
              const DIcon = t.icon
              const active = d === activeDomain
              return (
                <button
                  key={d}
                  id={`guide-tab-${d}`}
                  onClick={() => setActiveDomain(d)}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem',
                    padding: '0.5rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${active ? c.border : 'var(--border)'}`,
                    background: active ? c.tabActive : 'transparent',
                    color: active ? c.text : 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: active ? 700 : 500,
                    transition: 'all 0.2s ease',
                  }}
                >
                  <DIcon size={13} />
                  {t.label}
                </button>
              )
            })}
          </div>

          {/* Description */}
          <div style={{
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
          }}>
            <Icon size={15} style={{ color: colors.text, flexShrink: 0 }} />
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {tpl.description}
            </span>
          </div>

          {/* Required / Optional fields */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                Campos Obligatorios
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {tpl.required.map(f => (
                  <span key={f} style={{
                    fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.15rem 0.5rem',
                    borderRadius: '4px', background: colors.badgeBg, border: `1px solid ${colors.badgeBorder}`,
                    color: colors.text
                  }}>{f}</span>
                ))}
              </div>
            </div>
            {tpl.optional.length > 0 && (
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                  Campos Opcionales
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                  {tpl.optional.map(f => (
                    <span key={f} style={{
                      fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.15rem 0.5rem',
                      borderRadius: '4px', background: 'rgba(71,85,105,0.2)', border: '1px solid rgba(71,85,105,0.3)',
                      color: 'var(--text-muted)'
                    }}>{f}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Template code block */}
          <div style={{ position: 'relative', marginBottom: '1rem' }}>
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '0.4rem 0.75rem',
              background: 'rgba(0,0,0,0.4)',
              borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
              border: '1px solid var(--border)', borderBottom: 'none',
            }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                plantilla_{activeDomain}{tpl.extension}
              </span>
              <button
                id={`copy-template-${activeDomain}`}
                onClick={handleCopy}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.35rem',
                  padding: '0.25rem 0.6rem', borderRadius: '4px',
                  background: copied ? 'rgba(34,197,94,0.15)' : 'rgba(79,142,247,0.1)',
                  border: `1px solid ${copied ? 'rgba(34,197,94,0.4)' : 'rgba(79,142,247,0.25)'}`,
                  color: copied ? '#86efac' : 'var(--neon-blue)',
                  cursor: 'pointer', fontSize: '0.7rem', fontWeight: 600,
                  transition: 'all 0.2s',
                }}
              >
                {copied ? <Check size={11} /> : <Copy size={11} />}
                {copied ? 'Copiado' : 'Copiar'}
              </button>
            </div>
            <pre style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.73rem',
              background: 'rgba(0,0,0,0.35)',
              border: '1px solid var(--border)',
              borderRadius: '0 0 var(--radius-sm) var(--radius-sm)',
              padding: '1rem',
              overflowX: 'auto',
              color: 'var(--text-code)',
              lineHeight: 1.7,
              margin: 0,
              maxHeight: '280px',
              overflowY: 'auto',
            }}>
              {tpl.content}
            </pre>
          </div>

          {/* Rules */}
          <div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
              Reglas de Validación
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {tpl.rules.map((r, i) => {
                const rc = RULE_COLORS[r.type as keyof typeof RULE_COLORS]
                return (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                    padding: '0.45rem 0.7rem',
                    borderRadius: 'var(--radius-sm)',
                    background: rc.bg, border: `1px solid ${rc.border}`,
                    fontSize: '0.78rem', color: rc.text, lineHeight: 1.4,
                  }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: rc.dot, flexShrink: 0, marginTop: '0.3rem' }} />
                    {r.text}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Footer tip */}
          <div style={{
            marginTop: '1rem',
            padding: '0.65rem 0.875rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(79,142,247,0.05)',
            border: '1px solid rgba(79,142,247,0.15)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
          }}>
            💡 <strong style={{ color: 'var(--neon-blue)' }}>Tip:</strong> Copia la plantilla, rellena los campos con los datos de tu reto y guarda el archivo. Luego arrástralo o selecciónalo en el panel de la izquierda para analizarlo.
          </div>
        </>
      )}
    </div>
  )
}
