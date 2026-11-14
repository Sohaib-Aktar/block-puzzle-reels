import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

interface SolutionBoxProps {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
}

export const SolutionBox: React.FC<SolutionBoxProps> = ({
  x,
  y,
  width,
  height,
  label = "WINNING MOVE!",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  const pulse = 1 + Math.sin(frame * 0.2) * 0.04;

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width,
        height,
        borderRadius: 16,
        border: `4px solid ${THEME_COLORS.goldHighlight}`,
        background: "rgba(255, 215, 0, 0.22)",
        boxShadow: `0 0 35px ${THEME_COLORS.goldGlow}, inset 0 0 20px ${THEME_COLORS.goldGlowSoft}`,
        transform: `scale(${entrance * pulse})`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 35,
        pointerEvents: "none",
      }}
    >
      <span
        style={{
          fontFamily: THEME_FONTS.headings,
          fontSize: 22,
          fontWeight: 900,
          color: THEME_COLORS.goldHighlight,
          background: "rgba(13, 13, 13, 0.85)",
          padding: "4px 12px",
          borderRadius: 8,
          border: `1px solid ${THEME_COLORS.goldHighlight}`,
          textShadow: "0 2px 4px rgba(0,0,0,0.8)",
          letterSpacing: 0.5,
        }}
      >
        {label}
      </span>
    </div>
  );
};
