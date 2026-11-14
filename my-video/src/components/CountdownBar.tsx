import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

interface CountdownBarProps {
  totalDots?: number;
  framesPerDot?: number;
  top?: number;
}

export const CountdownBar: React.FC<CountdownBarProps> = ({
  totalDots = 5,
  framesPerDot = 30,
  top = 310,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Pulse animation for remaining dots
  const pulseScale = 1 + Math.sin(frame * 0.25) * 0.05;

  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        zIndex: 50,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          gap: 16,
          background: "rgba(13, 13, 13, 0.75)",
          padding: "12px 28px",
          borderRadius: 40,
          border: `2px solid ${THEME_COLORS.purpleBorder}`,
          backdropFilter: "blur(6px)",
          alignItems: "center",
        }}
      >
        {Array.from({ length: totalDots }).map((_, index) => {
          // Dots deactivate as countdown progresses
          const isRemaining = frame < (index + 1) * framesPerDot;

          const dotSpring = spring({
            frame: frame - index * 6,
            fps,
            config: SPRING_PRESETS.pop,
          });

          return (
            <div
              key={index}
              style={{
                width: 22,
                height: 22,
                borderRadius: "50%",
                transform: `scale(${dotSpring * (isRemaining ? pulseScale : 0.8)})`,
                background: isRemaining
                  ? `linear-gradient(135deg, ${THEME_COLORS.goldHighlight}, #FF8F00)`
                  : "rgba(255, 255, 255, 0.2)",
                boxShadow: isRemaining
                  ? `0 0 16px ${THEME_COLORS.goldGlow}`
                  : "none",
                border: isRemaining
                  ? "2px solid #FFFFFF"
                  : "2px solid rgba(255,255,255,0.15)",
                transition: "all 0.15s ease",
              }}
            />
          );
        })}
      </div>
      <p
        style={{
          fontFamily: THEME_FONTS.main,
          fontSize: 26,
          fontWeight: 700,
          color: THEME_COLORS.goldHighlight,
          margin: "8px 0 0 0",
          textShadow: "0 2px 8px rgba(0,0,0,0.9)",
          letterSpacing: 1,
        }}
      >
        Where does it fit?
      </p>
    </div>
  );
};
