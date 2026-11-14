import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

interface HookBannerProps {
  title: string;
  subtitle?: string;
  top?: number;
}

export const HookBanner: React.FC<HookBannerProps> = ({
  title,
  subtitle,
  top = 180,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

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
        transform: `scale(${scale})`,
        zIndex: 50,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: "linear-gradient(135deg, rgba(123, 47, 190, 0.95), rgba(74, 26, 122, 0.95))",
          padding: "16px 42px",
          borderRadius: 60,
          border: `3px solid ${THEME_COLORS.goldHighlight}`,
          boxShadow: `0 10px 40px rgba(0,0,0,0.6), 0 0 25px ${THEME_COLORS.purpleGlow}`,
          textAlign: "center",
          maxWidth: 920,
        }}
      >
        <h1
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 48,
            fontWeight: 800,
            color: THEME_COLORS.textPrimary,
            margin: 0,
            textShadow: "0 4px 12px rgba(0,0,0,0.8)",
            letterSpacing: 0.5,
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 28,
              fontWeight: 600,
              color: THEME_COLORS.goldHighlight,
              margin: "6px 0 0 0",
              textShadow: "0 2px 8px rgba(0,0,0,0.8)",
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
