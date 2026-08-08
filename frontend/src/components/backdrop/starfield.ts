export interface Star {
  x: number
  y: number
  size: number
  opacity: number
  teal: boolean
}

export interface StarLayer {
  z: number
  factor: number
  stars: Star[]
}

function mulberry32(seed: number): () => number {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const rand = mulberry32(1337)

function makeStars(count: number, sizeRange: [number, number], opacityRange: [number, number]): Star[] {
  return Array.from({ length: count }, () => ({
    x: rand() * 100,
    y: rand() * 100,
    size: sizeRange[0] + rand() * (sizeRange[1] - sizeRange[0]),
    opacity: opacityRange[0] + rand() * (opacityRange[1] - opacityRange[0]),
    teal: rand() < 0.12,
  }))
}

export const STAR_LAYERS: StarLayer[] = [
  { z: -340, factor: 0.3, stars: makeStars(70, [1, 1.6], [0.18, 0.4]) },
  { z: -170, factor: 0.55, stars: makeStars(46, [1.2, 2], [0.28, 0.5]) },
  { z: -60, factor: 0.85, stars: makeStars(26, [1.5, 2.6], [0.4, 0.7]) },
]
