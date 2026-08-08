import { Component, type ReactNode } from 'react'

interface PresenceErrorBoundaryProps {
  children: ReactNode
  fallback: ReactNode
}

interface PresenceErrorBoundaryState {
  failed: boolean
}

export class PresenceErrorBoundary extends Component<PresenceErrorBoundaryProps, PresenceErrorBoundaryState> {
  state: PresenceErrorBoundaryState = { failed: false }

  static getDerivedStateFromError(): PresenceErrorBoundaryState {
    return { failed: true }
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}
