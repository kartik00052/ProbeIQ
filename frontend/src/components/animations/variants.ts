import type { Variants } from 'framer-motion'
import { depthTransition, springs } from '../../lib/motion'

export const questionVariants: Variants = {
  initial: { opacity: 0, z: -80, rotateX: -3 },
  animate: {
    opacity: 1,
    z: 0,
    rotateX: 0,
    transition: springs.snappy,
  },
  exit: { opacity: 0, z: -60, rotateX: 2, transition: { duration: 0.16 } },
}

export const fadeUpVariants: Variants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0, transition: depthTransition },
  exit: { opacity: 0, y: -8, transition: { duration: 0.16 } },
}
