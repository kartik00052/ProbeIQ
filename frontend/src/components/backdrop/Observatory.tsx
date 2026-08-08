import type { CSSProperties } from 'react'
import { STAR_LAYERS } from './starfield'
import type { Star } from './starfield'

function StarDot({ star }: { star: Star }) {
  const style: CSSProperties = {
    left: `${star.x}%`,
    top: `${star.y}%`,
    width: star.size,
    height: star.size,
    ['--star-opacity' as string]: star.opacity,
  }
  return (
    <span
      aria-hidden="true"
      className={`observatory-star absolute rounded-full ${star.teal ? 'observatory-star--teal' : ''}`}
      style={style}
    />
  )
}

interface ObservatoryProps {
  className?: string
}

export function Observatory({ className }: ObservatoryProps) {
  return (
    <div className={`pointer-events-none absolute inset-0 ${className ?? ''}`} aria-hidden="true">
      <div className="absolute -inset-[10%] bg-[radial-gradient(ellipse_at_50%_120%,rgba(79,209,197,0.08),transparent_60%)]" />
      {STAR_LAYERS.map((layer) => (
        <div key={layer.z} className="absolute inset-0">
          {layer.stars.map((star, i) => (
            <StarDot key={`${layer.z}-${i}`} star={star} />
          ))}
        </div>
      ))}
    </div>
  )
}
