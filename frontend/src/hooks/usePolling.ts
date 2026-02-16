import { useEffect, useRef, useCallback } from 'react'

/**
 * Poll a callback at a fixed interval with smart lifecycle management.
 *
 * - Pauses when the browser tab is hidden
 * - Fires immediately when the tab becomes visible again
 * - Cleans up on unmount or when disabled
 */
export function usePolling(
  callback: () => void | Promise<void>,
  intervalMs: number,
  enabled: boolean = true
) {
  const savedCallback = useRef(callback)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  const startPolling = useCallback(() => {
    if (intervalRef.current) return
    intervalRef.current = setInterval(() => {
      savedCallback.current()
    }, intervalMs)
  }, [intervalMs])

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!enabled) {
      stopPolling()
      return
    }

    startPolling()

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopPolling()
      } else {
        savedCallback.current()
        startPolling()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      stopPolling()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, startPolling, stopPolling])
}
