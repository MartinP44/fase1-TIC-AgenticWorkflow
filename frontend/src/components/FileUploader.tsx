import React, { useCallback, useState } from 'react'
import { Upload, FileCode, X } from 'lucide-react'

interface FileUploaderProps {
  onFileSelect: (file: File) => void
  disabled?: boolean
}

const ACCEPTED_EXTENSIONS = ['.json', '.yaml', '.yml', '.txt', '.md', '.zip', '.pdf']

export const FileUploader: React.FC<FileUploaderProps> = ({ onFileSelect, disabled }) => {
  const [dragOver, setDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleFile = useCallback((file: File) => {
    setSelectedFile(file)
    onFileSelect(file)
  }, [onFileSelect])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedFile(null)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div>
      <label
        className={`uploader ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{ display: 'block', cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1 }}
      >
        <input
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleInputChange}
          style={{ display: 'none' }}
          disabled={disabled}
          id="file-input"
        />

        <div className="uploader-icon">
          <Upload size={28} />
        </div>

        <p className="uploader-title">
          {dragOver ? '¡Suelta el archivo aquí!' : 'Sube tu plantilla CTF'}
        </p>
        <p className="uploader-subtitle">
          Arrastra y suelta o haz clic para seleccionar
        </p>

        <div className="uploader-formats">
          {ACCEPTED_EXTENSIONS.map(ext => (
            <span key={ext} className="format-badge">{ext}</span>
          ))}
        </div>
      </label>

      {selectedFile && (
        <div className="file-selected">
          <FileCode size={20} className="file-selected-icon" />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="file-selected-name">{selectedFile.name}</div>
            <div className="file-selected-size">{formatSize(selectedFile.size)}</div>
          </div>
          {!disabled && (
            <button
              onClick={clearFile}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: '4px' }}
              title="Quitar archivo"
            >
              <X size={16} />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
