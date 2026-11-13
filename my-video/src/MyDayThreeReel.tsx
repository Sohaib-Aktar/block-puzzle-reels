import React from "react";
import {
  AbsoluteFill,
  Composition,
  Easing,
  Freeze,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/**
 * CONFIGURATION - Day 3 Puzzle Challenge
 * Frame 1780 features a 93.2% filled block board with all 3 candidate pieces waiting in the tray.
 */
export const CONFIG = {
  // Exact frame in gameplay.mp4 with 90%+ filled board and all 3 bottom pieces clear
  pauseAtVideoFrame: 1780,

  // Pixel coordinates for candidate piece badges (A, B, C) above each tray piece
  badgePositions: {
    A: { x: 284, y: 1540 },
    B: { x: 540, y: 1540 },
    C: { x: 820, y: 1540 },
  },

  // Glowing highlight solution box on the 8x8 grid where Piece B fits
  solutionBox: {
    x: 390,
    y: 690,
    width: 260,
    height: 260,
  },

  // Winning piece for this puzzle challenge
  correctAnswer: "B" as "A" | "B" | "C",

  // Hook language selector ('EN' | 'BN' | 'HI')
  hookLanguage: "EN" as "EN" | "BN" | "HI",
};

const HOOK_TEXTS: Record<"EN" | "BN" | "HI", string> = {
  EN: "Solve it in ONE move",
  BN: "মাত্র এক চালে সমাধান করুন",
  HI: "सिर्फ़ एक चाल में हल करो",
};

export interface MyDayThreeReelProps {
  videoSrc?: string;
  config?: typeof CONFIG;
}

/**
 * 0:00 - 0:06.5 (Frames 0 - 195): Top Hook Banner
 */
const TopHookBanner: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 180, mass: 0.8 },
  });

  // Fade out smoothly towards frame 195
  const opacity = interpolate(
    frame,
    [0, 15, 180, 195],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 140,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 36px",
        zIndex: 60,
        opacity,
        transform: `scale(${entrance})`,
      }}
    >
      <div
        style={{
          background: "rgba(13, 13, 13, 0.88)",
          backdropFilter: "blur(16px)",
          border: "2px solid #7B2FBE",
          boxShadow:
            "0 10px 40px rgba(123, 47, 190, 0.5), 0 0 25px rgba(255, 215, 0, 0.25)",
          borderRadius: 999,
          padding: "20px 44px",
          textAlign: "center",
          maxWidth: 960,
        }}
      >
        <h1
          style={{
            margin: 0,
            color: "#FFFFFF",
            fontFamily: "'Poppins', 'Inter', -apple-system, sans-serif",
            fontSize: 64,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            textShadow:
              "0 2px 10px rgba(0, 0, 0, 0.9), 0 0 25px rgba(255, 215, 0, 0.4)",
          }}
        >
          {text}
        </h1>
      </div>
    </div>
  );
};

/**
 * 0:01.5 - 0:14.0 (Composition Frames 45 - 420): Animated Candidate Badges A, B, C
 * Note: Inside Sequence from=45, frame is local (0 to 375).
 */
const CandidateBadges: React.FC<{
  positions: typeof CONFIG.badgePositions;
  correctAnswer: "A" | "B" | "C";
}> = ({ positions, correctAnswer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Local stagger frames: A at 0 (comp 45), B at 15 (comp 60), C at 30 (comp 75)
  const keys: Array<"A" | "B" | "C"> = ["A", "B", "C"];
  const staggerFrames = { A: 0, B: 15, C: 30 };

  // Answer reveal begins at local frame 300 (composition frame 345)
  const isReveal = frame >= 300;
  const revealProgress = spring({
    frame: Math.max(0, frame - 300),
    fps,
    config: { damping: 10, stiffness: 150, mass: 0.6 },
  });

  return (
    <>
      {keys.map((key) => {
        const startFrame = staggerFrames[key];
        const isCorrect = key === correctAnswer;

        const entranceSpring = spring({
          frame: Math.max(0, frame - startFrame),
          fps,
          config: { damping: 12, stiffness: 180, mass: 0.7 },
        });

        if (frame < startFrame) {
          return null;
        }

        let scale = entranceSpring;
        let opacity = 1;
        let bg = "#7B2FBE";
        let textColor = "#FFFFFF";
        let shadow =
          "0 8px 24px rgba(123, 47, 190, 0.7), 0 0 15px rgba(255, 215, 0, 0.3)";

        if (isReveal) {
          if (isCorrect) {
            scale = 1 + revealProgress * 0.5; // Scales up to 1.5x
            bg = "#FFD700";
            textColor = "#0D0D0D";
            shadow = "0 0 40px #FFD700, 0 0 70px rgba(255, 215, 0, 0.9)";
          } else {
            opacity = interpolate(frame, [300, 315], [1, 0.35], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            shadow = "none";
          }
        }

        const pos = positions[key];

        return (
          <div
            key={key}
            style={{
              position: "absolute",
              left: pos.x - 40,
              top: pos.y - 40,
              width: 80,
              height: 80,
              borderRadius: 20,
              backgroundColor: bg,
              color: textColor,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              fontFamily: "'Poppins', 'Inter', sans-serif",
              fontSize: 48,
              fontWeight: 900,
              boxShadow: shadow,
              zIndex: 70,
              transform: `scale(${scale})`,
              opacity,
              border:
                isCorrect && isReveal
                  ? "3px solid #FFFFFF"
                  : "2px solid rgba(255, 255, 255, 0.3)",
            }}
          >
            {key}
          </div>
        );
      })}
    </>
  );
};

/**
 * 0:06.5 - 0:11.5 (Composition Frames 195 - 345): Thinking Countdown
 * Note: Inside Sequence from=195, frame is local (0 to 150).
 */
const ThinkingCountdown: React.FC = () => {
  const frame = useCurrentFrame();

  const textPulse = 0.825 + 0.175 * Math.sin(frame * 0.2);
  const activeDotCount = Math.min(5, Math.floor(frame / 30) + 1);
  const clockScale = 1 + 0.1 * Math.sin(frame * 0.25);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 130,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 65,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 20,
          opacity: textPulse,
          background: "rgba(13, 13, 13, 0.75)",
          padding: "12px 28px",
          borderRadius: 999,
          border: "1.5px solid rgba(123, 47, 190, 0.6)",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.6)",
        }}
      >
        <span
          style={{
            fontSize: 34,
            transform: `scale(${clockScale})`,
            display: "inline-block",
          }}
        >
          ⏱️
        </span>
        <span
          style={{
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 36,
            fontWeight: 800,
            color: "#FFFFFF",
            letterSpacing: "-0.01em",
            textShadow:
              "0 2px 10px rgba(0,0,0,0.9), 0 0 20px rgba(123,47,190,0.8)",
          }}
        >
          Where does the piece go?
        </span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 22,
          background: "rgba(13, 13, 13, 0.85)",
          padding: "16px 36px",
          borderRadius: 999,
          border: "2px solid rgba(123, 47, 190, 0.5)",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.7)",
        }}
      >
        {[1, 2, 3, 4, 5].map((dotNum) => {
          const isActive = dotNum <= activeDotCount;
          return (
            <div
              key={dotNum}
              style={{
                width: 24,
                height: 24,
                borderRadius: "50%",
                backgroundColor:
                  isActive ? "#FFD700" : "rgba(255, 255, 255, 0.2)",
                border: isActive
                  ? "2px solid #FFFFFF"
                  : "1.5px solid rgba(123, 47, 190, 0.4)",
                boxShadow: isActive
                  ? "0 0 20px #FFD700, 0 0 35px rgba(255, 215, 0, 0.8)"
                  : "none",
                transform: isActive ? "scale(1.2)" : "scale(1.0)",
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

/**
 * 0:11.5 - 0:14.0 (Composition Frames 345 - 420): Glowing Solution Box Highlight
 * Note: Inside Sequence from=345, frame is local (0 to 75).
 */
const SolutionHighlight: React.FC<{ box: typeof CONFIG.solutionBox }> = ({
  box,
}) => {
  const frame = useCurrentFrame();
  const pulse = 1 + 0.04 * Math.sin(frame * 0.2);

  const opacity = interpolate(
    frame,
    [0, 15, 65, 75],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        left: box.x,
        top: box.y,
        width: box.width,
        height: box.height,
        border: "4px solid #FFD700",
        borderRadius: 16,
        boxShadow:
          "0 0 35px #FFD700, inset 0 0 30px rgba(255, 215, 0, 0.4), 0 0 70px rgba(123, 47, 190, 0.6)",
        transform: `scale(${pulse})`,
        zIndex: 55,
        opacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -36,
          left: "50%",
          transform: "translateX(-50%)",
          background: "#FFD700",
          color: "#0D0D0D",
          padding: "4px 16px",
          borderRadius: 8,
          fontFamily: "'Poppins', 'Inter', sans-serif",
          fontSize: 20,
          fontWeight: 900,
          letterSpacing: "0.1em",
          boxShadow: "0 0 15px #FFD700",
        }}
      >
        TARGET
      </div>
    </div>
  );
};

/**
 * 0:14.0 - 0:15.0 (Composition Frames 420 - 450): Outro Call-To-Action Card
 * Note: Inside Sequence from=420, frame is local (0 to 30).
 */
const OutroEndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bgOpacity = interpolate(frame, [0, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.2, 0.8, 0.2, 1),
  });

  const ctaScale = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: { damping: 12, stiffness: 160 },
  });

  const subOpacity = interpolate(frame, [10, 22], [0, 1], {
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
        zIndex: 90,
        padding: "0 40px",
        textAlign: "center",
      }}
    >
      <div
        style={{
          transform: `scale(${ctaScale})`,
          marginBottom: 24,
          background: "rgba(123, 47, 190, 0.25)",
          border: "2px solid #7B2FBE",
          borderRadius: 28,
          padding: "24px 44px",
          boxShadow: "0 0 40px rgba(123, 47, 190, 0.6)",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 44,
            fontWeight: 900,
            color: "#FFFFFF",
            letterSpacing: "-0.01em",
            textShadow: "0 0 25px rgba(255, 255, 255, 0.4)",
          }}
        >
          Comment A, B or C below 👇
        </h2>
      </div>

      <div style={{ opacity: subOpacity }}>
        <p
          style={{
            margin: 0,
            fontFamily: "'Poppins', 'Inter', sans-serif",
            fontSize: 30,
            fontWeight: 700,
            color: "#FFD700",
            textShadow: "0 0 20px rgba(255, 215, 0, 0.6)",
          }}
        >
          Did you spot it in time? 🧩
        </p>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Main Day 3 Reel Composition (450 frames @ 30fps)
 */
export const MyDayThreeReelContent: React.FC<MyDayThreeReelProps> = ({
  videoSrc = staticFile("gameplay.mp4"),
  config = CONFIG,
}) => {
  const frame = useCurrentFrame();

  const initialFadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const hookText = HOOK_TEXTS[config.hookLanguage] || HOOK_TEXTS.EN;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0D0D0D",
        opacity: initialFadeIn,
        overflow: "hidden",
      }}
    >
      {/* 
        GAMEPLAY VIDEO TIMELINE:
        Using objectFit: "contain" ensures 100% of the mobile phone screen
        (board, score, and all 3 bottom candidate pieces) is visible without being cropped!
        1. Frames 0 - 45: Play video smoothly into the pause point (frames 1735 to 1780)
      */}
      <Sequence from={0} durationInFrames={45} name="Opening Gameplay">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={Math.max(0, config.pauseAtVideoFrame - 45)}
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
        2. Frames 45 - 345 (300 frames / 10 sec):
        Freeze board at pauseAtVideoFrame (93.2% filled board, all 3 pieces clear)
      */}
      <Sequence from={45} durationInFrames={300} name="Frozen Puzzle Challenge">
        <AbsoluteFill>
          <Freeze frame={config.pauseAtVideoFrame}>
            <OffthreadVideo
              src={videoSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                objectPosition: "center",
              }}
            />
          </Freeze>
        </AbsoluteFill>
      </Sequence>

      {/* 
        3. Frames 345 - 420 (75 frames / 2.5 sec):
        Unfreeze gameplay so viewer sees Piece B dragged and line-clear combo burst!
      */}
      <Sequence from={345} durationInFrames={75} name="Answer Reveal Gameplay">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={config.pauseAtVideoFrame}
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
        4. Frames 420 - 450 (30 frames / 1 sec):
        Continue background motion while outro card fades in
      */}
      <Sequence from={420} durationInFrames={30} name="Gameplay Outro Underlay">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={config.pauseAtVideoFrame + 75}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* OVERLAYS */}

      {/* 0:00 - 0:06.5 (Frames 0 - 195): Top Hook Banner */}
      <Sequence from={0} durationInFrames={195} name="Top Hook Banner">
        <TopHookBanner text={hookText} />
      </Sequence>

      {/* 0:01.5 - 0:14.0 (Frames 45 - 420): Candidate Badges A, B, C */}
      <Sequence from={45} durationInFrames={375} name="Badges Overlay">
        <CandidateBadges
          positions={config.badgePositions}
          correctAnswer={config.correctAnswer}
        />
      </Sequence>

      {/* 0:06.5 - 0:11.5 (Frames 195 - 345): Thinking Pause & 5-Dot Countdown */}
      <Sequence from={195} durationInFrames={150} name="Thinking Phase">
        <ThinkingCountdown />
      </Sequence>

      {/* 0:11.5 - 0:14.0 (Frames 345 - 420): Glowing Solution Box Highlight */}
      <Sequence from={345} durationInFrames={75} name="Solution Highlight">
        <SolutionHighlight box={config.solutionBox} />
      </Sequence>

      {/* 0:14.0 - 0:15.0 (Frames 420 - 450): Outro Call-To-Action Card */}
      <Sequence from={420} durationInFrames={30} name="Outro End Card">
        <OutroEndCard />
      </Sequence>
    </AbsoluteFill>
  );
};

export const MyDayThreeReel: React.FC = () => {
  return (
    <Composition
      id="MyDayThreeReel"
      component={MyDayThreeReelContent}
      durationInFrames={450} // 15 seconds @ 30 fps
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        videoSrc: staticFile("gameplay.mp4"),
        config: CONFIG,
      }}
    />
  );
};
