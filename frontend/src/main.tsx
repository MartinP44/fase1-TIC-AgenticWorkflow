import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/index.css'

// Suppress third-party Chrome extension message channel errors to prevent console clutter
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    if (
      event.reason &&
      typeof event.reason.message === 'string' &&
      (event.reason.message.includes('A listener indicated an asynchronous response') ||
       event.reason.message.includes('message channel closed before a response was received'))
    ) {
      event.preventDefault()
      event.stopPropagation()
    }
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

