import React from "react";
import {
  AbsoluteFill,
  Composition,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  CANVAS_SPECS,
  SPRING_PRESETS,
  THEME_COLORS,
  THEME_FONTS,
} from "./theme/tokens";

export interface DayFourOfflineReelProps {
  videoSrc?: string;
  hookTitle?: string;
  hookSubtitle?: string;
  closingTitle?: string;
  closingSubtitle?: string;
  closingCta?: string;
}

export const DayFourOfflineReelContent: React.FC<DayFourOfflineReelProps> = ({
  videoSrc = staticFile("recording_3_cfr30.mp4"),
  hookTitle = "No WiFi? No problem.",
  hookSubtitle = "100% Offline Gameplay",
  closingTitle = "Play Anywhere. Stay Offline.",
  closingSubtitle = "Trains • Flights • Zero Signal",
  closingCta = "Play Free Today 🧩",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Initial smooth fade in
  const initialFadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#070B14",
        opacity: initialFadeIn,
        overflow: "hidden",
      }}
    >
      {/* 
        -------------------------------------------------------------
        1. SCENE 1: OPENING HOOK (Frames 0 - 60 / 0.0s - 2.0s, 2s)
        Authentic game board view before shade pull
        -------------------------------------------------------------
      */}
      <Sequence from={0} durationInFrames={60} name="Scene 1: Opening Hook">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={0}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        -------------------------------------------------------------
        2. SCENE 2: AIRPLANE MODE TOGGLE (Frames 60 - 120 / 2.0s - 4.0s, 2s)
        Live touch on Aeroplane Mode tile, turning green and activating airplane icon
        Source frames in CFR30: 195 - 255 (6.5s - 8.5s)
        -------------------------------------------------------------
      */}
      <Sequence from={60} durationInFrames={60} name="Scene 2: Airplane Mode Toggle">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={195}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        -------------------------------------------------------------
        3. SCENE 3: RETURN TO GAME (Frames 120 - 150 / 4.0s - 5.0s, 1s)
        Quick settings shade sliding up revealing game board with active airplane icon
        Source frames in CFR30: 255 - 285 (8.5s - 9.5s)
        -------------------------------------------------------------
      */}
      <Sequence from={120} durationInFrames={30} name="Scene 3: Return to Game">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={255}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        -------------------------------------------------------------
        4. SCENE 4: OFFLINE GAMEPLAY (Frames 150 - 390 / 5.0s - 13.0s, 8s)
        8 seconds of genuine, fluid 10x10 puzzle gameplay with airplane icon active
        Source frames in CFR30: 285 - 525 (9.5s - 17.5s)
        -------------------------------------------------------------
      */}
      <Sequence from={150} durationInFrames={240} name="Scene 4: Offline Gameplay">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={285}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        -------------------------------------------------------------
        5. SCENE 5: CLOSING GAMEPLAY (Frames 390 - 450 / 13.0s - 15.0s, 2s)
        Continuous board view under offline mode
        Source frames in CFR30: 525 - 585 (17.5s - 19.5s)
        -------------------------------------------------------------
      */}
      <Sequence from={390} durationInFrames={60} name="Scene 5: Closing Board">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={525}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        =============================================================
        DYNAMIC ON-SCREEN GRAPHICS & TEXT OVERLAYS (ENGLISH ONLY)
        =============================================================
      */}

      {/* OVERLAY 1: Opening Hook Banner (Frames 0 - 65, 0.0s - 2.1s) */}
      <Sequence from={0} durationInFrames={65} name="Overlay: Hook Banner">
        <OpeningHookOverlay title={hookTitle} subtitle={hookSubtitle} />
      </Sequence>

      {/* OVERLAY 2: Airplane Mode Badge (Frames 60 - 120, 2.0s - 4.0s) */}
      <Sequence from={60} durationInFrames={60} name="Overlay: Airplane Mode Pill">
        <FeaturePill text="Airplane Mode: ON ✈️" />
      </Sequence>

      {/* OVERLAY 3: Offline Proof Callout (Frames 150 - 240, 5.0s - 8.0s) */}
      <Sequence from={150} durationInFrames={90} name="Overlay: Zero Data Pill">
        <FeaturePill text="Zero Data • Zero Lag ⚡" />
      </Sequence>

      {/* OVERLAY 4: Closing Message Card (Frames 390 - 450, 13.0s - 15.0s) */}
      <Sequence from={390} durationInFrames={60} name="Overlay: Closing Card">
        <ClosingOverlay
          title={closingTitle}
          subtitle={closingSubtitle}
          cta={closingCta}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

// Opening Hook Overlay Component (Central Full-Text Focal Presentation)
const OpeningHookOverlay: React.FC<{ title: string; subtitle?: string }> = ({
  title,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy professional spring entrance pop
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 14,
      stiffness: 180,
      mass: 0.8,
    },
  });

  // Hold completely stable until frame 48, then smooth dissolution before Scene 2 (frame 60)
  const exitOpacity = interpolate(frame, [48, 58], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 700, // Central viewing area of the 1080x1920 gameplay screen (empty board zone)
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${scale})`,
        opacity: exitOpacity,
        zIndex: 50,
        pointerEvents: "none",
        padding: "0 30px",
      }}
    >
      <div
        style={{
          background:
            "linear-gradient(135deg, rgba(88, 28, 135, 0.96), rgba(30, 15, 60, 0.96))",
          padding: "18px 50px",
          borderRadius: 48,
          border: `3.5px solid ${THEME_COLORS.goldHighlight}`,
          boxShadow: `0 16px 48px rgba(0,0,0,0.85), 0 0 25px ${THEME_COLORS.purpleGlow}`,
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 54,
            fontWeight: 900,
            color: THEME_COLORS.textPrimary,
            letterSpacing: 0.5,
            textShadow: "0 4px 16px rgba(0,0,0,0.95), 0 2px 4px rgba(0,0,0,0.8)",
            lineHeight: 1.15,
            margin: 0,
            whiteSpace: "nowrap",
          }}
        >
          {title}
        </span>
        {subtitle && (
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 30,
              fontWeight: 800,
              color: THEME_COLORS.goldHighlight,
              marginTop: 8,
              letterSpacing: 0.5,
              textShadow: "0 2px 10px rgba(0,0,0,0.9)",
              lineHeight: 1.15,
              whiteSpace: "nowrap",
            }}
          >
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};

// Feature Pill Component for subtle informational overlays
const FeaturePill: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 220, // Respecting top safe area
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 50,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          transform: `scale(${entrance})`,
          background: "rgba(10, 20, 40, 0.90)",
          border: `2px solid ${THEME_COLORS.goldHighlight}`,
          boxShadow: "0 8px 30px rgba(0,0,0,0.8)",
          borderRadius: 50,
          padding: "12px 36px",
        }}
      >
        <span
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 32,
            fontWeight: 800,
            color: THEME_COLORS.textPrimary,
            letterSpacing: 0.5,
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

// Closing Overlay Card Component
const ClosingOverlay: React.FC<{
  title: string;
  subtitle: string;
  cta: string;
}> = ({ title, subtitle, cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: SPRING_PRESETS.smooth,
  });

  const bgFade = interpolate(frame, [0, 15], [0, 0.90], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: `rgba(7, 11, 20, ${bgFade})`,
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
            width: 120,
            height: 120,
            borderRadius: 32,
            background: `linear-gradient(135deg, ${THEME_COLORS.purplePrimary}, ${THEME_COLORS.purpleDeep})`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 58,
            boxShadow: `0 0 40px ${THEME_COLORS.purpleGlow}`,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            marginBottom: 24,
          }}
        >
          ✈️
        </div>

        <h2
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 52,
            fontWeight: 900,
            color: THEME_COLORS.textPrimary,
            margin: "0 0 12px 0",
            textShadow: "0 4px 18px rgba(0,0,0,0.9)",
          }}
        >
          {title}
        </h2>

        <p
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 30,
            fontWeight: 600,
            color: THEME_COLORS.goldHighlight,
            margin: "0 0 28px 0",
            letterSpacing: 0.5,
          }}
        >
          {subtitle}
        </p>

        <div
          style={{
            background: "linear-gradient(135deg, rgba(123, 47, 190, 0.95), rgba(74, 26, 122, 0.95))",
            padding: "16px 44px",
            borderRadius: 50,
            border: `2px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 0 30px ${THEME_COLORS.goldGlowSoft}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 28,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
            }}
          >
            {cta}
          </span>
        </div>

        <div
          style={{
            marginTop: 24,
            fontSize: 22,
            fontFamily: THEME_FONTS.main,
            fontWeight: 600,
            color: "rgba(255, 255, 255, 0.6)",
          }}
        >
          Pyapiras Games
        </div>
      </div>
    </div>
  );
};

export const DayFourOfflineReel: React.FC = () => {
  return (
    <Composition
      id="DayFourOfflineReel"
      component={DayFourOfflineReelContent}
      durationInFrames={450} // Exactly 15.00 seconds at 30fps
      fps={30}
      width={CANVAS_SPECS.width} // 1080
      height={CANVAS_SPECS.height} // 1920
    />
  );
};
