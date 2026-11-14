import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

export interface CandidateBadgeProps {
  label: string;
  x: number;
  y: number;
  isCorrect: boolean;
  isRevealed: boolean;
  staggerDelay: number;
  badgeSize?: number;
}

export const CandidateBadge: React.FC<CandidateBadgeProps> = ({
  label,
  x,
  y,
  isCorrect,
  isRevealed,
  staggerDelay,
  badgeSize = 84,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animation with stagger offset
  const entranceSpring = spring({
    frame: frame - staggerDelay,
    fps,
    config: SPRING_PRESETS.pop,
  });

  // Reveal transition scaling
  const revealProgress = isRevealed
    ? spring({
        frame: frame - 300,
        fps,
        config: SPRING_PRESETS.celebrate,
      })
    : 0;

  // Reveal state: winning badge scales up, others dim
  const scale = isRevealed
    ? isCorrect
      ? 1 + revealProgress * 0.45
      : Math.max(0.7, 1 - revealProgress * 0.25)
    : entranceSpring;

  const opacity = isRevealed && !isCorrect ? Math.max(0.35, 1 - revealProgress * 0.65) : 1;

  const isGold = isRevealed && isCorrect;

  return (
    <div
      style={{
        position: "absolute",
        left: x - badgeSize / 2,
        top: y - badgeSize / 2,
        width: badgeSize,
        height: badgeSize,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity,
        background: isGold
          ? `linear-gradient(135deg, ${THEME_COLORS.goldHighlight}, #FFA000)`
          : `linear-gradient(135deg, ${THEME_COLORS.purplePrimary}, ${THEME_COLORS.purpleDeep})`,
        border: `3px solid ${isGold ? "#FFFFFF" : THEME_COLORS.goldHighlight}`,
        boxShadow: isGold
          ? `0 0 35px ${THEME_COLORS.goldGlow}, 0 8px 24px rgba(0,0,0,0.7)`
          : `0 0 20px ${THEME_COLORS.purpleGlow}, 0 6px 18px rgba(0,0,0,0.6)`,
        zIndex: isGold ? 40 : 30,
        pointerEvents: "none",
      }}
    >
      <span
        style={{
          fontFamily: THEME_FONTS.headings,
          fontSize: 42,
          fontWeight: 900,
          color: isGold ? "#1A1A1A" : THEME_COLORS.textPrimary,
          textShadow: isGold ? "none" : "0 2px 6px rgba(0,0,0,0.6)",
        }}
      >
        {label}
      </span>
    </div>
  );
};
