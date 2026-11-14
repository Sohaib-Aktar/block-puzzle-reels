import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

interface ComboPulseProps {
  scoreText?: string;
  subText?: string;
}

export const ComboPulse: React.FC<ComboPulseProps> = ({
  scoreText = "COMBO +400",
  subText = "INSANE CLEAR!",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: SPRING_PRESETS.celebrate,
  });

  const glowPulse = 1 + Math.sin(frame * 0.3) * 0.08;

  return (
    <div
      style={{
        position: "absolute",
        top: "46%",
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale * glowPulse})`,
        zIndex: 55,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: "linear-gradient(135deg, rgba(255, 215, 0, 0.95), rgba(255, 143, 0, 0.95))",
          padding: "18px 48px",
          borderRadius: 50,
          border: "4px solid #FFFFFF",
          boxShadow: `0 0 50px ${THEME_COLORS.goldGlow}, 0 10px 30px rgba(0,0,0,0.8)`,
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 54,
            fontWeight: 900,
            color: "#1A1A1A",
            letterSpacing: 1.5,
          }}
        >
          {scoreText}
        </span>
      </div>
      {subText && (
        <span
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 28,
            fontWeight: 800,
            color: THEME_COLORS.textPrimary,
            marginTop: 10,
            textShadow: "0 3px 10px rgba(0,0,0,0.9)",
            letterSpacing: 2,
          }}
        >
          {subText}
        </span>
      )}
    </div>
  );
};
