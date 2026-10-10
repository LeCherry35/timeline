import { useEffect, useState } from 'react'

type BackendStatus = 'connecting' | 'ok' | 'unavailable'

function App() {
  const [status, setStatus] = useState<BackendStatus>('connecting')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => setStatus(response.ok ? 'ok' : 'unavailable'))
      .catch(() => setStatus('unavailable'))
  }, [])

  return (
    <main>
      <h1>Timeline</h1>
      <p>Backend: {status}</p>
    </main>
  )
}

export default App
