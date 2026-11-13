import React from "react";
import {
  AbsoluteFill,
  Composition,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface MyDayTwoReelProps {
  videoSrc?: string;
  startFromFrame?: number;
  hookText?: string;
  gameTitle?: string;
  callToAction?: string;
  showComboBadge?: boolean;
}

/**
 * Hook Banner (0:00 - 0:01.5 / Frames 0 - 45)
 */
const HookBanner: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring (frames 0 - 15)
  const scale = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 180, mass: 0.8 },
  });

  // Fade in at start, fade out near frame 45
  const opacity = interpolate(
    frame,
    [0, 10, 35, 45],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 180,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 40px",
        zIndex: 50,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          background: "rgba(13, 13, 13, 0.88)",
          backdropFilter: "blur(16px)",
          border: "2px solid rgba(123, 47, 190, 0.7)",
          boxShadow: "0 10px 40px rgba(123, 47, 190, 0.45), 0 0 20px rgba(255, 215, 0, 0.2)",
          borderRadius: 9999,
          padding: "20px 48px",
          textAlign: "center",
          maxWidth: 960,
        }}
      >
        <h1
          style={{
            margin: 0,
            color: "#FFFFFF",
            fontFamily: "'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            fontSize: 64,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.8), 0 0 25px rgba(255, 215, 0, 0.4)",
          }}
        >
          {text}
        </h1>
      </div>
    </div>
  );
};

/**
 * Combo Score Glowing Pulse Animation (0:10 - 0:13 / Local frames 0 - 90)
 */
const ComboPulseOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Pulse oscillation using spring cycle (scale 1.0 to 1.4)
  const springProgress = spring({
    frame: frame % 30, // Pulse every 1 second (30 frames)
    fps,
    config: { damping: 10, stiffness: 140, mass: 0.6 },
  });

  const pulseScale = interpolate(springProgress, [0, 0.5, 1], [1.0, 1.38, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const glowOpacity = interpolate(
    frame,
    [0, 12, 75, 90],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: "38%",
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
        zIndex: 60,
        opacity: glowOpacity,
      }}
    >
      <div
        style={{
          transform: `scale(${pulseScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          background: "radial-gradient(circle, rgba(123, 47, 190, 0.85) 0%, rgba(13, 13, 13, 0.75) 75%)",
          border: "3px solid #FFD700",
          borderRadius: 32,
          padding: "18px 44px",
          boxShadow: "0 0 50px rgba(255, 215, 0, 0.8), 0 0 90px rgba(123, 47, 190, 0.6)",
        }}
      >
        <span
          style={{
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 36,
            fontWeight: 800,
            color: "#FFD700",
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            textShadow: "0 0 15px rgba(255, 215, 0, 0.9)",
          }}
        >
          COMBO BURST
        </span>
        <span
          style={{
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 88,
            fontWeight: 900,
            color: "#FFFFFF",
            letterSpacing: "-0.03em",
            textShadow: "0 0 30px #FFD700, 0 0 50px #7B2FBE",
          }}
        >
          +400
        </span>
      </div>
    </div>
  );
};

/**
 * End Card (0:13 - 0:15 / Frames 390 - 450)
 */
const EndCard: React.FC<{ title: string; cta: string }> = ({ title, cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Fade to black background
  const bgOpacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.2, 0.8, 0.2, 1),
  });

  // Staggered spring for game title
  const titleScale = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: { damping: 12, stiffness: 160 },
  });

  // Staggered spring for CTA
  const ctaOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: `rgba(13, 13, 13, ${bgOpacity})`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 80,
        padding: "0 50px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${titleScale})`,
          marginBottom: 24,
        }}
      >
        <h2
          style={{
            margin: 0,
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 52,
            fontWeight: 900,
            color: "#FFFFFF",
            letterSpacing: "-0.01em",
            textShadow: "0 0 30px rgba(123, 47, 190, 0.9), 0 0 50px rgba(255, 215, 0, 0.4)",
          }}
        >
          {title}
        </h2>
      </div>

      <div
        style={{
          opacity: ctaOpacity,
          background: "rgba(123, 47, 190, 0.25)",
          border: "1.5px solid rgba(255, 215, 0, 0.6)",
          borderRadius: 24,
          padding: "16px 36px",
          boxShadow: "0 0 30px rgba(123, 47, 190, 0.5)",
        }}
      >
        <p
          style={{
            margin: 0,
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 34,
            fontWeight: 700,
            color: "#FFD700",
            textShadow: "0 2px 8px rgba(0,0,0,0.8)",
          }}
        >
          {cta}
        </p>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Main 15-Second Continuous Gameplay Composition
 */
export const MyDayTwoReelContent: React.FC<MyDayTwoReelProps> = ({
  videoSrc = staticFile("gameplay.mp4"),
  startFromFrame = 0,
  hookText = "Wait for the last piece",
  gameTitle = "Block Puzzle Burst",
  callToAction = "How big is your best combo? 🔥",
  showComboBadge = true,
}) => {
  const frame = useCurrentFrame();

  // Initial fade-in of the entire video (frames 0 - 15)
  const initialFadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0D0D0D",
        opacity: initialFadeIn,
        overflow: "hidden",
      }}
    >
      {/* 
        CONTINUOUS GAMEPLAY VIDEO LAYER
        Segment 1 (0:00 - 0:10 / 300 frames) @ 1.0x normal speed:
        Played 300 source frames.
      */}
      <Sequence from={0} durationInFrames={300} name="Gameplay Normal Speed">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame}
            playbackRate={1.0}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        Segment 2 (0:10 - 0:13 / 90 frames) @ 0.3x slow motion:
        Seamlessly continues from startFromFrame + 300.
        During these 90 frames at 0.3x, it advances by 90 * 0.3 = 27 source frames.
      */}
      <Sequence from={300} durationInFrames={90} name="Gameplay Slow Motion">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame + 300}
            playbackRate={0.3}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* 
        Segment 3 (0:13 - 0:15 / 60 frames):
        Seamlessly continues gameplay underneath while the black end card fades in.
        Starts at startFromFrame + 300 + 27 = startFromFrame + 327.
      */}
      <Sequence from={390} durationInFrames={60} name="Gameplay Outro Continuation">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame + 327}
            playbackRate={1.0}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* TIMELINE OVERLAYS */}

      {/* 0:00 - 0:01.5 (Frames 0 - 45): Hook Banner */}
      <Sequence from={0} durationInFrames={45} name="Hook Overlay">
        <HookBanner text={hookText} />
      </Sequence>

      {/* 0:10 - 0:13 (Frames 300 - 390): Glowing Combo Score Pulse */}
      {showComboBadge && (
        <Sequence from={300} durationInFrames={90} name="Combo Score Pulse">
          <ComboPulseOverlay />
        </Sequence>
      )}

      {/* 0:13 - 0:15 (Frames 390 - 450): Fade to Black & End Card */}
      <Sequence from={390} durationInFrames={60} name="Outro End Card">
        <EndCard title={gameTitle} cta={callToAction} />
      </Sequence>
    </AbsoluteFill>
  );
};

/**
 * Exported Composition Wrapper
 */
export const MyDayTwoReel: React.FC = () => {
  return (
    <Composition
      id="MyDayTwoReel"
      component={MyDayTwoReelContent}
      durationInFrames={450} // 15 seconds @ 30 fps
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        videoSrc: staticFile("gameplay.mp4"),
        startFromFrame: 0,
        hookText: "Wait for the last piece",
        gameTitle: "Block Puzzle Burst",
        callToAction: "How big is your best combo? 🔥",
        showComboBadge: true,
      }}
    />
  );
};
