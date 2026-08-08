import { useMemo, useRef } from 'react'
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

function Core({ state }: { state: PresenceState }) {
  const group = useRef<THREE.Group>(null)
  const core = useRef<THREE.Mesh>(null)
  const points = useRef<THREE.Points>(null)

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
        opacity: 0.6,
        depthWrite: false,
      }),
    [],
  )

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime()
    const groupRef = group.current
    const coreRef = core.current
    if (!groupRef || !coreRef) return

    const base = state === 'thinking' ? 1.4 : 0.6
    const spin = base + (state === 'responding' ? 0.6 : 0)
    groupRef.rotation.y += delta * spin
    groupRef.rotation.x = Math.sin(elapsed * 0.3) * 0.15

    const breathe = 1 + Math.sin(elapsed * 2) * 0.03
    const pulse = state === 'thinking' ? 1.06 : state === 'responding' ? 1.12 : 1
    coreRef.scale.setScalar(breathe * pulse)

    if (points.current) {
      const mat = points.current.material as THREE.PointsMaterial
      mat.opacity = state === 'complete' ? 0.15 : 0.6
    }
  })

  return (
    <group ref={group}>
      <mesh ref={core} geometry={geometry} material={material} />
      <points ref={points} geometry={PARTICLE_GEOMETRY} material={pointsMaterial} />
      <ambientLight intensity={0.4} />
      <pointLight color="#4fd1c5" intensity={12} distance={8} position={[3, 2, 4]} />
    </group>
  )
}

export default function PresenceScene({ state }: { state: PresenceState }) {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 50 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }}
    >
      <Core state={state} />
    </Canvas>
  )
}
