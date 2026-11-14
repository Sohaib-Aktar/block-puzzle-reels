/**
 * Design Tokens & Visual Standards for Block Puzzle Reels
 * Consistent palette, typography, and spring physics across all 30 days.
 */

export const THEME_COLORS = {
  // Foundations
  background: "#0D0D0D",
  surfaceDark: "rgba(13, 13, 13, 0.85)",
  surfacePill: "rgba(30, 20, 50, 0.85)",

  // Brand Accents
  purplePrimary: "#7B2FBE",
  purpleDeep: "#4A1A7A",
  purpleGlow: "rgba(123, 47, 190, 0.6)",
  purpleBorder: "rgba(180, 100, 255, 0.5)",

  // Highlights & Accents
  goldHighlight: "#FFD700",
  goldGlow: "rgba(255, 215, 0, 0.8)",
  goldGlowSoft: "rgba(255, 215, 0, 0.4)",

  // Typography
  textPrimary: "#FFFFFF",
  textMuted: "#E0E0E0",
  textDim: "rgba(255, 255, 255, 0.4)",

  // States
  successGreen: "#00E676",
  dangerRed: "#FF1744",
} as const;

export const THEME_FONTS = {
  main: "'Poppins', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  headings: "'Poppins', 'Inter', system-ui, -apple-system, sans-serif",
} as const;

export const SPRING_PRESETS = {
  // Snappy, energetic bounce for badges and popups
  pop: {
    damping: 12,
    stiffness: 160,
    mass: 0.8,
  },
  // Smooth easing for cards and transitions
  smooth: {
    damping: 16,
    stiffness: 120,
    mass: 1.0,
  },
  // High-energy celebration bounce
  celebrate: {
    damping: 9,
    stiffness: 190,
    mass: 0.7,
  },
} as const;

export const CANVAS_SPECS = {
  width: 1080,
  height: 1920,
  fps: 30,
  defaultDurationInFrames: 450, // 15 seconds
} as const;
