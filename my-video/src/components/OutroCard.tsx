import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "../theme/tokens";

interface OutroCardProps {
  headline?: string;
  subheadline?: string;
  callToAction?: string;
}

export const OutroCard: React.FC<OutroCardProps> = ({
  headline = "Block Puzzle Burst",
  subheadline = "Can you beat this score?",
  callToAction = "Comment A, B or C below 👇",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: SPRING_PRESETS.smooth,
  });

  const bgOpacity = interpolate(frame, [0, 15], [0, 0.94], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: `rgba(13, 13, 13, ${bgOpacity})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 60px",
        zIndex: 60,
      }}
    >
      <div
        style={{
          transform: `scale(${entrance})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <div
          style={{
            width: 130,
            height: 130,
            borderRadius: 34,
            background: `linear-gradient(135deg, ${THEME_COLORS.purplePrimary}, ${THEME_COLORS.purpleDeep})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 64,
            boxShadow: `0 0 45px ${THEME_COLORS.purpleGlow}`,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            marginBottom: 28,
          }}
        >
          🧩
        </div>

        <h2
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 56,
            fontWeight: 900,
            color: THEME_COLORS.textPrimary,
            margin: "0 0 14px 0",
            textShadow: "0 4px 20px rgba(0,0,0,0.9)",
          }}
        >
          {headline}
        </h2>

        <p
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 32,
            fontWeight: 600,
            color: THEME_COLORS.goldHighlight,
            margin: "0 0 32px 0",
          }}
        >
          {subheadline}
        </p>

        <div
          style={{
            background: "linear-gradient(135deg, rgba(123, 47, 190, 0.9), rgba(74, 26, 122, 0.9))",
            padding: "18px 46px",
            borderRadius: 50,
            border: `2px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 0 25px ${THEME_COLORS.goldGlowSoft}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 30,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
            }}
          >
            {callToAction}
          </span>
        </div>
      </div>
    </div>
  );
};
