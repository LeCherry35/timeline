import { render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import App from './App.tsx'

afterEach(() => {
  vi.unstubAllGlobals()
})

test('shows backend status', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }))

  render(<App />)

  expect(await screen.findByText('Backend: ok')).toBeTruthy()
})
