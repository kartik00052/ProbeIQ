import type { Variants } from 'framer-motion'
import { PRESENTATION, depthTransition } from '../../lib/motion'

export const questionVariants: Variants = {
  initial: { opacity: 0, z: PRESENTATION.questionStartZ, rotateX: -8 },
  animate: {
    opacity: 1,
    z: 0,
    rotateX: 0,
    transition: depthTransition,
  },
  exit: { opacity: 0, z: -80, rotateX: 6, transition: { duration: 0.18 } },
}

export const fadeUpVariants: Variants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: depthTransition },
  exit: { opacity: 0, y: -8, transition: { duration: 0.16 } },
}

export const staggerContainer: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.08 } },
}

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: depthTransition },
}
