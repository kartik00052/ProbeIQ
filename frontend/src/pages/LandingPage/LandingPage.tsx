import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { AppLayout } from '../../layouts/AppLayout'
import { Logo } from '../../components/common/Logo'
import { Button } from '../../components/ui/Button'
import { staggerContainer, revealItemVariants } from '../../components/animations/variants'
import { ROUTES } from '../../constants/routes'

export default function LandingPage() {
  return (
    <AppLayout>
      <nav className="flex justify-between py-2">
        <Logo />
        <Link to={ROUTES.setup} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
          Skip intro
        </Link>
      </nav>

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="flex flex-1 flex-col items-center justify-center gap-8 text-center"
      >
        <motion.p variants={revealItemVariants} className="font-mono text-xs uppercase tracking-[0.3em] text-accent">
          AI technical interview agent
        </motion.p>
        <motion.h1 variants={revealItemVariants} className="max-w-2xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Prove your skills with a <span className="text-accent">human-calibrated</span> AI interviewer.
        </motion.h1>
        <motion.p variants={revealItemVariants} className="max-w-lg text-lg leading-relaxed text-text-dim">
          A 31-day AI-cohort curriculum becomes a live, adaptive interview. Your answers are probed in depth and
          turned into an honest post-interview report.
        </motion.p>
        <motion.div variants={revealItemVariants} className="flex flex-col gap-3 sm:flex-row">
          <Link to={ROUTES.setup}>
            <Button>Begin interview</Button>
          </Link>
        </motion.div>
      </motion.div>
    </AppLayout>
  )
}
