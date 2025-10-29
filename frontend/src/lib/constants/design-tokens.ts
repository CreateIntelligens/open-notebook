export const colorTokens = {
  accent: '#4f46e5',
  accentGradient: 'linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%)',
  accentSoft: 'rgba(79, 70, 229, 0.1)',
  outline: 'rgba(79, 70, 229, 0.35)'
} as const

export const radiusTokens = {
  xl: '1.25rem',
  lg: '1rem'
} as const

export const shadowTokens = {
  focus: '0 0 0 2px rgba(79, 70, 229, 0.35)',
  overlay: '0 18px 45px -20px rgba(15, 23, 42, 0.25)'
} as const

export const motionTokens = {
  duration: {
    short: 0.18,
    medium: 0.26
  },
  easing: {
    standard: [0.22, 0.61, 0.36, 1],
    out: [0.16, 1, 0.3, 1]
  },
  spring: {
    type: 'spring' as const,
    damping: 20,
    stiffness: 240,
    mass: 0.8
  }
} as const

