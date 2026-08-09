import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { AppLayout } from '../../layouts/AppLayout'
import { Logo } from '../../components/common/Logo'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { ErrorMessage } from '../../components/common/ErrorMessage'
import { staggerContainer, revealItemVariants } from '../../components/animations/variants'
import { useAuth } from '../../hooks/useAuth'
import { ROUTES } from '../../constants/routes'

export default function Login() {
  const { login, error, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? ROUTES.setup
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!email.trim() || !password || isLoading) return
    try {
      await login(email.trim(), password)
      navigate(from, { replace: true })
    } catch {
      // The store has surfaced the error; the ErrorMessage below renders it.
    }
  }

  return (
    <AppLayout>
      <nav className="flex justify-between py-2">
        <Logo />
        <Link to={ROUTES.register} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
          Create account
        </Link>
      </nav>

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="flex flex-1 flex-col justify-center py-10"
      >
        <motion.div variants={revealItemVariants} className="flex flex-col gap-2">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">Sign in</p>
          <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">Welcome back</h1>
          <p className="mb-6 max-w-lg leading-relaxed text-text-dim">
            Your interviews are tied to your account. Sign in to pick up where you left off.
          </p>
        </motion.div>

        {error && (
          <motion.div variants={revealItemVariants} className="mb-6">
            <ErrorMessage message={error} />
          </motion.div>
        )}

        <motion.div variants={revealItemVariants}>
          <Card className="p-6">
            <form onSubmit={submit} className="flex flex-col gap-5">
              <div>
                <label htmlFor="login-email" className="mb-2 block font-mono text-xs uppercase tracking-widest text-text-dim">
                  Email address
                </label>
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-2xl border border-line bg-surface/80 p-4 text-base text-text focus:border-accent focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="login-password" className="mb-2 block font-mono text-xs uppercase tracking-widest text-text-dim">
                  Password
                </label>
                <input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-2xl border border-line bg-surface/80 p-4 text-base text-text focus:border-accent focus:outline-none"
                />
              </div>
              <div className="flex items-center justify-between gap-3">
                <Link to={ROUTES.register} className="text-sm text-text-dim underline-offset-4 hover:text-accent hover:underline">
                  New here? Register
                </Link>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Signing in…' : 'Sign in'}
                </Button>
              </div>
            </form>
          </Card>
        </motion.div>
      </motion.div>
    </AppLayout>
  )
}
