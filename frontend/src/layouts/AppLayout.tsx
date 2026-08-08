import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Presence } from '../components/three/Presence'
import { usePresenceState } from '../hooks/usePresenceState'
import { fadeUpVariants } from '../components/animations/variants'

interface AppLayoutProps {
  children: ReactNode
  showPresence?: boolean
}

export function AppLayout({ children, showPresence = true }: AppLayoutProps) {
  const presence = usePresenceState()

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg text-text" style={{ perspective: '1200px' }}>
      {showPresence && <Presence state={presence} />}
      <motion.main
        variants={fadeUpVariants}
        initial="initial"
        animate="animate"
        className="relative z-10 mx-auto flex min-h-screen w-full max-w-3xl flex-col px-6 py-8"
      >
        {children}
      </motion.main>
    </div>
  )
}
