import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import type { PresenceState } from '../../hooks/usePresenceState'

const PARTICLE_COUNT = 600

const PARTICLE_GEOMETRY = (() => {
  const positions = new Float32Array(PARTICLE_COUNT * 3)
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const radius = 1.6 + Math.random() * 2.2
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
    positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
    positions[i * 3 + 2] = radius * Math.cos(phi)
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  return geometry
})()

interface StateTarget {
  coreScale: number
  shellScale: number
  emissive: number
  lightIntensity: number
  pointsOpacity: number
  rotation: number
}

const STATE_TARGETS: Record<PresenceState, StateTarget> = {
  idle: { coreScale: 1, shellScale: 1, emissive: 0.4, lightIntensity: 7, pointsOpacity: 0.35, rotation: 0 },
  thinking: { coreScale: 0.82, shellScale: 0.76, emissive: 0.6, lightIntensity: 6, pointsOpacity: 0.14, rotation: 0.3 },
  responding: { coreScale: 1, shellScale: 0.94, emissive: 0.5, lightIntensity: 7.5, pointsOpacity: 0.3, rotation: 0 },
  waiting: { coreScale: 0.98, shellScale: 0.98, emissive: 0.46, lightIntensity: 7, pointsOpacity: 0.3, rotation: 0 },
  complete: { coreScale: 0.84, shellScale: 0.78, emissive: 0.1, lightIntensity: 2.2, pointsOpacity: 0.05, rotation: 0 },
}

const DAMPING = 4
const ROTATION_DAMPING = 1.8
const INTERVIEW_WEIGHT = 0.66
const INTERVIEW_DEPTH = -0.7

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function Core({ state, interviewing }: { state: PresenceState; interviewing: boolean }) {
  const group = useRef<THREE.Group>(null)
  const core = useRef<THREE.Mesh>(null)
  const points = useRef<THREE.Points>(null)
  const light = useRef<THREE.PointLight>(null)

  const prevState = useRef(state)
  const release = useRef(0)
  const cur = useRef({
    core: 1,
    shell: 1,
    emissive: 0.4,
    light: 7,
    points: 0.35,
    weight: 1,
    depth: 0,
    angle: 0,
    spin: 0,
  })

  const geometry = useMemo(() => new THREE.IcosahedronGeometry(0.8, 2), [])
  const material = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#4fd1c5', emissive: '#0b3d38', roughness: 0.3, metalness: 0.6 }),
    [],
  )

  const pointsMaterial = useMemo(
    () =>
      new THREE.PointsMaterial({
        color: '#4fd1c5',
        size: 0.02,
        transparent: true,
        opacity: 0.35,
        depthWrite: false,
      }),
    [],
  )

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime()
    const groupRef = group.current
    const coreRef = core.current
    const pointsRef = points.current
    const lightRef = light.current
    if (!groupRef || !coreRef || !pointsRef || !lightRef) return

    const dt = Math.min(delta, 0.05)

    if (state !== prevState.current) {
      prevState.current = state
      if (state === 'responding') release.current = 1
    }
    release.current = THREE.MathUtils.damp(release.current, 0, 1.2, dt)
    const ack = release.current

    const target = STATE_TARGETS[state]
    const damp = (value: number, goal: number) => THREE.MathUtils.damp(value, goal, DAMPING, dt)

    cur.current.core = damp(cur.current.core, target.coreScale)
    cur.current.shell = damp(cur.current.shell, target.shellScale)
    cur.current.emissive = damp(cur.current.emissive, target.emissive)
    cur.current.light = damp(cur.current.light, target.lightIntensity)
    cur.current.points = damp(cur.current.points, target.pointsOpacity)
    cur.current.spin = THREE.MathUtils.damp(cur.current.spin, target.rotation, ROTATION_DAMPING, dt)
    cur.current.angle += cur.current.spin * dt
    cur.current.weight = damp(cur.current.weight, interviewing ? INTERVIEW_WEIGHT : 1)
    cur.current.depth = damp(cur.current.depth, interviewing ? INTERVIEW_DEPTH : 0)

    const weight = cur.current.weight
    const glow = 0.45 + 0.55 * weight

    const stillness = state === 'waiting' ? 0.3 : state === 'complete' ? 0.25 : 1
    const breathe = 1 + Math.sin(elapsed * 1.4) * 0.016 * stillness
    const internalPulse = state === 'thinking' ? Math.sin(elapsed * 1.8) * 0.02 : 0

    const coreScale = cur.current.core * breathe + internalPulse * 0.5
    coreRef.scale.setScalar(Math.max(coreScale, 0.01))
    pointsRef.scale.setScalar(Math.max(cur.current.shell, 0.01))
    groupRef.position.z = cur.current.depth
    groupRef.position.y = Math.sin(elapsed * 0.3) * 0.03 * weight * stillness
    groupRef.rotation.y = cur.current.angle

    const coreMaterial = coreRef.material as THREE.MeshStandardMaterial
    const pointsMaterialRef = pointsRef.material as THREE.PointsMaterial
    coreMaterial.emissiveIntensity = clamp(cur.current.emissive * glow + internalPulse + ack * 0.12, 0, 2)
    pointsMaterialRef.opacity = clamp(cur.current.points * glow + ack * 0.06, 0, 1)
    lightRef.intensity = cur.current.light * glow + ack * 1.5
  })

  return (
    <group ref={group}>
      <mesh ref={core} geometry={geometry} material={material} />
      <points ref={points} geometry={PARTICLE_GEOMETRY} material={pointsMaterial} />
      <ambientLight intensity={0.4} />
      <pointLight ref={light} color="#4fd1c5" intensity={7} distance={8} position={[3, 2, 4]} />
    </group>
  )
}

export default function PresenceScene({
  state,
  interviewing,
}: {
  state: PresenceState
  interviewing: boolean
}) {
  const [hidden, setHidden] = useState(() => document.hidden)

  useEffect(() => {
    const onVisibilityChange = () => setHidden(document.hidden)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [])

  const paused = hidden || (interviewing && state === 'complete')
  return (
    <Canvas
      frameloop={paused ? 'never' : 'always'}
      camera={{ position: [0, 0, 5], fov: 50 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }}
    >
      <Core state={state} interviewing={interviewing} />
    </Canvas>
  )
}
