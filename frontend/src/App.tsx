import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'

export default function App() {
  useEffect(() => {
    useAuthStore.getState().refreshSession()
  }, [])

  return <Outlet />
}
