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
import { CANVAS_SPECS, SPRING_PRESETS, THEME_COLORS, THEME_FONTS } from "./theme/tokens";

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG  
// Video: recording_2.mp4  |  720×1600 @ ~48fps  |  201s total
// Puzzle analysis from sample screenshots:
//   Board has ~70% fill (from sample_1 screenshot)
//   Piece A (left tray):   Cyan L-shape  — 2×2 bottom-left corner
//   Piece B (center tray): Yellow 1×3 horizontal bar
//   Piece C (right tray):  Purple 1×1 single block
// Answer intentionally NOT revealed in this Reel (two-part strategy)
// ─────────────────────────────────────────────────────────────────────────────
const CONFIG = {
  // A good action-rich moment visible in recording_2 (~mid-game, board with pieces)
  // Start a few seconds before the dense board state matches sample_1
  hookFrameStart: 300,      // Frame to start showing in Scene 1
  challengeFreeze: 480,     // Freeze frame for the puzzle challenge board
  
  pieces: {
    A: { label: "A", color: "#00BFFF", emoji: "⬜" },
    B: { label: "B", color: "#FFD700", emoji: "⬜" },
    C: { label: "C", color: "#B44FE8", emoji: "⬜" },
  },

  // 20-second reel @ 30fps = 600 frames
  totalFrames: 600,
  fps: 30,
};

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 1 — Attention Hook (0–3s / Frames 0–90)
// ─────────────────────────────────────────────────────────────────────────────
const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({ frame, fps, config: SPRING_PRESETS.pop });
  const subScale = spring({ frame: frame - 10, fps, config: SPRING_PRESETS.pop });
  const tagScale = spring({ frame: frame - 20, fps, config: SPRING_PRESETS.pop });

  const pulsate = 1 + Math.sin(frame * 0.18) * 0.03;
  const scanlineY = ((frame * 4) % 1920);

  return (
    <AbsoluteFill style={{ zIndex: 20, pointerEvents: "none" }}>
      {/* Scanline sweep visual effect */}
      <div
        style={{
          position: "absolute",
          top: scanlineY,
          left: 0,
          right: 0,
          height: 3,
          background: "linear-gradient(90deg, transparent, rgba(123,47,190,0.4), rgba(255,215,0,0.5), rgba(123,47,190,0.4), transparent)",
          zIndex: 1,
        }}
      />

      {/* Top vignette gradient */}
      <div
        style={{
          position: "absolute",
          top: 0, left: 0, right: 0,
          height: 420,
          background: "linear-gradient(to bottom, rgba(5,5,20,0.95) 0%, rgba(5,5,20,0.75) 60%, transparent 100%)",
          zIndex: 15,
        }}
      />

      {/* MAIN HOOK HEADLINE */}
      <div
        style={{
          position: "absolute",
          top: 90,
          left: 0, right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 50,
          transform: `scale(${titleScale * pulsate})`,
          padding: "0 40px",
        }}
      >
        {/* EN Headline */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(123,47,190,0.97), rgba(74,20,140,0.97))",
            border: `4px solid ${THEME_COLORS.goldHighlight}`,
            borderRadius: 24,
            padding: "20px 48px",
            boxShadow: `0 0 60px rgba(255,215,0,0.5), 0 0 30px rgba(123,47,190,0.8), 0 20px 50px rgba(0,0,0,0.9)`,
            textAlign: "center",
            maxWidth: 940,
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 62,
              fontWeight: 900,
              color: "#FFFFFF",
              letterSpacing: 1,
              lineHeight: 1.1,
              textShadow: "0 4px 20px rgba(0,0,0,0.8)",
            }}
          >
            Solve it in
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 80,
              fontWeight: 900,
              background: `linear-gradient(90deg, ${THEME_COLORS.goldHighlight}, #FFB300, ${THEME_COLORS.goldHighlight})`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: 2,
              lineHeight: 1.0,
              textShadow: "none",
            }}
          >
            ONE MOVE!
          </div>
        </div>

        {/* EN sub-headline only — multilingual text goes in captions, never on-screen */}
        <div style={{ transform: `scale(${subScale})`, marginTop: 16, textAlign: "center" }}>
          <div
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 28,
              fontWeight: 700,
              color: "rgba(255,255,255,0.88)",
              textShadow: "0 2px 12px rgba(0,0,0,0.9)",
              letterSpacing: 0.5,
            }}
          >
            🧩 Think. Place. Clear.
          </div>
        </div>

        {/* Brain teaser badge */}
        <div
          style={{
            transform: `scale(${tagScale})`,
            marginTop: 20,
            background: "rgba(255,215,0,0.15)",
            border: "2px solid rgba(255,215,0,0.6)",
            borderRadius: 50,
            padding: "8px 28px",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ fontSize: 28 }}>🧠</span>
          <span
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 26,
              fontWeight: 700,
              color: THEME_COLORS.goldHighlight,
              letterSpacing: 1.5,
            }}
          >
            BRAIN CHALLENGE
          </span>
          <span style={{ fontSize: 28 }}>🧠</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 2 — Show The Challenge (3–7s / Frames 90–210)
// ─────────────────────────────────────────────────────────────────────────────
const ChallengeScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, config: SPRING_PRESETS.pop });

  // Piece badges A, B, C with staggered entrance
  const badgeA = spring({ frame: frame - 0, fps, config: SPRING_PRESETS.pop });
  const badgeB = spring({ frame: frame - 15, fps, config: SPRING_PRESETS.pop });
  const badgeC = spring({ frame: frame - 30, fps, config: SPRING_PRESETS.pop });

  const questionPulse = 1 + Math.sin(frame * 0.15) * 0.025;

  const pieces = [
    { label: "A", color: "#00BFFF", glow: "rgba(0,191,255,0.7)", scale: badgeA, x: 190 },
    { label: "B", color: "#FFD700", glow: "rgba(255,215,0,0.7)", scale: badgeB, x: 540 },
    { label: "C", color: "#B44FE8", glow: "rgba(180,79,232,0.7)", scale: badgeC, x: 890 },
  ];

  return (
    <AbsoluteFill style={{ zIndex: 20, pointerEvents: "none" }}>
      {/* Top overlay banner */}
      <div
        style={{
          position: "absolute",
          top: 0, left: 0, right: 0,
          height: 380,
          background: "linear-gradient(to bottom, rgba(5,5,20,0.92) 0%, rgba(5,5,20,0.65) 70%, transparent 100%)",
          zIndex: 15,
        }}
      />

      {/* Question banner */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: 0, right: 0,
          display: "flex",
          justifyContent: "center",
          zIndex: 50,
          transform: `scale(${entrance * questionPulse})`,
          padding: "0 40px",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, rgba(13,13,30,0.96), rgba(30,10,60,0.96))",
            border: "3px solid rgba(255,215,0,0.7)",
            borderRadius: 20,
            padding: "18px 44px",
            textAlign: "center",
            boxShadow: "0 0 40px rgba(255,215,0,0.3), 0 15px 40px rgba(0,0,0,0.9)",
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 46,
              fontWeight: 900,
              color: "#FFFFFF",
              textShadow: "0 3px 15px rgba(0,0,0,0.9)",
            }}
          >
            Which piece would you
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 56,
              fontWeight: 900,
              color: THEME_COLORS.goldHighlight,
              textShadow: `0 0 25px ${THEME_COLORS.goldGlow}`,
            }}
          >
            place first? 🤔
          </div>
        </div>
      </div>

      {/* Bottom tray labels panel */}
      <div
        style={{
          position: "absolute",
          bottom: 0, left: 0, right: 0,
          height: 480,
          background: "linear-gradient(to top, rgba(5,5,20,0.95) 0%, rgba(5,5,20,0.7) 60%, transparent 100%)",
          zIndex: 15,
        }}
      />

      {/* A, B, C badges above pieces */}
      <div
        style={{
          position: "absolute",
          bottom: 320,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          gap: 160,
          zIndex: 60,
        }}
      >
        {pieces.map((p) => (
          <div
            key={p.label}
            style={{
              width: 90,
              height: 90,
              borderRadius: "50%",
              background: `radial-gradient(circle at 35% 35%, ${p.color}, ${p.color}88)`,
              border: "4px solid #FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transform: `scale(${p.scale})`,
              boxShadow: `0 0 35px ${p.glow}, 0 8px 25px rgba(0,0,0,0.8)`,
            }}
          >
            <span
              style={{
                fontFamily: THEME_FONTS.headings,
                fontSize: 46,
                fontWeight: 900,
                color: p.label === "B" ? "#1A1A1A" : "#FFFFFF",
                textShadow: p.label !== "B" ? "0 2px 6px rgba(0,0,0,0.6)" : "none",
              }}
            >
              {p.label}
            </span>
          </div>
        ))}
      </div>

      {/* Arrow pointing down to tray */}
      <div
        style={{
          position: "absolute",
          bottom: 290,
          left: 0, right: 0,
          display: "flex",
          justifyContent: "center",
          zIndex: 55,
          transform: `translateY(${Math.sin(frame * 0.2) * 8}px)`,
        }}
      >
        <span style={{ fontSize: 48 }}>👇</span>
      </div>

      {/* Bottom label: "Choose wisely!" */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 0, right: 0,
          textAlign: "center",
          zIndex: 60,
        }}
      >
        <div
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 32,
            fontWeight: 700,
            color: "rgba(255,255,255,0.9)",
            textShadow: "0 3px 12px rgba(0,0,0,0.9)",
            letterSpacing: 1,
          }}
        >
          👆 Choose wisely!
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 3 — Thinking Countdown (7–12s / Frames 210–360)
// ─────────────────────────────────────────────────────────────────────────────
const ThinkingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 5 dots, each active for 30 frames (1 second each)
  const activeDot = Math.floor(frame / 30); // 0,1,2,3,4
  const dotProgress = (frame % 30) / 30;

  const entrance = spring({ frame, fps, config: SPRING_PRESETS.pop });
  const thinkingPulse = 1 + Math.sin(frame * 0.12) * 0.02;

  const secondsLeft = Math.max(0, 5 - Math.floor(frame / 30));

  return (
    <AbsoluteFill style={{ zIndex: 20, pointerEvents: "none" }}>
      {/* Full overlay darkening */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(0,0,5,0.45)",
          zIndex: 10,
        }}
      />

      {/* Top thinking banner */}
      <div
        style={{
          position: "absolute",
          top: 70,
          left: 0, right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 50,
          transform: `scale(${entrance})`,
          padding: "0 40px",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, rgba(10,5,30,0.97), rgba(50,20,100,0.97))",
            border: "3px solid rgba(180,79,232,0.8)",
            borderRadius: 20,
            padding: "16px 42px",
            textAlign: "center",
            boxShadow: "0 0 40px rgba(123,47,190,0.6), 0 12px 35px rgba(0,0,0,0.9)",
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 46,
              fontWeight: 900,
              color: "#FFFFFF",
              textShadow: "0 3px 15px rgba(0,0,0,0.9)",
            }}
          >
            🤔 Think carefully!
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 28,
              fontWeight: 600,
              color: "rgba(255,215,0,0.9)",
              marginTop: 6,
            }}
          >
            Time is running out...
          </div>
        </div>
      </div>

      {/* Big countdown number */}
      <div
        style={{
          position: "absolute",
          top: "36%",
          left: 0, right: 0,
          display: "flex",
          justifyContent: "center",
          zIndex: 55,
          transform: `scale(${thinkingPulse})`,
        }}
      >
        <div
          style={{
            width: 200,
            height: 200,
            borderRadius: "50%",
            background: "linear-gradient(135deg, rgba(123,47,190,0.9), rgba(74,20,140,0.9))",
            border: `6px solid ${THEME_COLORS.goldHighlight}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 0 60px ${THEME_COLORS.goldGlow}, 0 0 30px rgba(123,47,190,0.8)`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 110,
              fontWeight: 900,
              color: THEME_COLORS.goldHighlight,
              textShadow: `0 0 30px ${THEME_COLORS.goldGlow}`,
              lineHeight: 1,
            }}
          >
            {secondsLeft === 0 ? "!" : secondsLeft}
          </span>
        </div>
      </div>

      {/* 5-dot countdown bar */}
      <div
        style={{
          position: "absolute",
          bottom: 240,
          left: 0, right: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          zIndex: 50,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 20,
            background: "rgba(5,5,20,0.88)",
            padding: "16px 36px",
            borderRadius: 50,
            border: "2px solid rgba(123,47,190,0.6)",
            backdropFilter: "blur(8px)",
          }}
        >
          {[0, 1, 2, 3, 4].map((i) => {
            const isActive = i === activeDot;
            const isPast = i < activeDot;
            const isFuture = i > activeDot;

            return (
              <div
                key={i}
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background: isPast
                    ? "rgba(255,255,255,0.15)"
                    : isActive
                    ? THEME_COLORS.goldHighlight
                    : `rgba(255,215,0,0.5)`,
                  boxShadow: isActive
                    ? `0 0 20px ${THEME_COLORS.goldGlow}, 0 0 8px #FFFFFF`
                    : isPast
                    ? "none"
                    : `0 0 8px ${THEME_COLORS.goldGlowSoft}`,
                  border: isActive
                    ? "3px solid #FFFFFF"
                    : isPast
                    ? "2px solid rgba(255,255,255,0.15)"
                    : `2px solid rgba(255,215,0,0.5)`,
                  transform: `scale(${isActive ? 1.3 : 1.0})`,
                  transition: "all 0.1s ease",
                }}
              />
            );
          })}
        </div>

        <div
          style={{
            marginTop: 14,
            fontFamily: THEME_FONTS.main,
            fontSize: 28,
            fontWeight: 700,
            color: THEME_COLORS.goldHighlight,
            textShadow: "0 2px 8px rgba(0,0,0,0.9)",
            letterSpacing: 1,
          }}
        >
          A, B or C? 🤔
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 4 — Audience Interaction (12–16s / Frames 360–480)
// ─────────────────────────────────────────────────────────────────────────────
const InteractionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, config: SPRING_PRESETS.pop });
  const aEntrance = spring({ frame: frame - 0, fps, config: SPRING_PRESETS.celebrate });
  const bEntrance = spring({ frame: frame - 12, fps, config: SPRING_PRESETS.celebrate });
  const cEntrance = spring({ frame: frame - 24, fps, config: SPRING_PRESETS.celebrate });

  const ctaPulse = 1 + Math.sin(frame * 0.2) * 0.025;

  const options = [
    { label: "A", color: "#00BFFF", glow: "rgba(0,191,255,0.8)", scale: aEntrance },
    { label: "B", color: "#FFD700", glow: "rgba(255,215,0,0.8)", scale: bEntrance },
    { label: "C", color: "#B44FE8", glow: "rgba(180,79,232,0.8)", scale: cEntrance },
  ];

  return (
    <AbsoluteFill style={{ zIndex: 20, pointerEvents: "none" }}>
      {/* Dark overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(0,0,10,0.75)",
          zIndex: 10,
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 36,
          zIndex: 50,
          padding: "0 40px",
        }}
      >
        {/* CTA Headline */}
        <div
          style={{
            transform: `scale(${entrance * ctaPulse})`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 56,
              fontWeight: 900,
              color: "#FFFFFF",
              textShadow: "0 4px 20px rgba(0,0,0,0.9)",
              lineHeight: 1.2,
            }}
          >
            Which one would
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 56,
              fontWeight: 900,
              color: "#FFFFFF",
              lineHeight: 1.2,
            }}
          >
            you choose?
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 46,
              fontWeight: 800,
              color: THEME_COLORS.goldHighlight,
              marginTop: 12,
              textShadow: `0 0 25px ${THEME_COLORS.goldGlow}`,
            }}
          >
            Comment A, B or C! 👇
          </div>
        </div>

        {/* Large A/B/C option cards */}
        <div
          style={{
            display: "flex",
            gap: 28,
            justifyContent: "center",
          }}
        >
          {options.map((opt) => (
            <div
              key={opt.label}
              style={{
                width: 200,
                height: 200,
                borderRadius: 28,
                background: `linear-gradient(135deg, ${opt.color}22, ${opt.color}44)`,
                border: `5px solid ${opt.color}`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                transform: `scale(${opt.scale})`,
                boxShadow: `0 0 50px ${opt.glow}, 0 10px 30px rgba(0,0,0,0.8)`,
              }}
            >
              <span
                style={{
                  fontFamily: THEME_FONTS.headings,
                  fontSize: 90,
                  fontWeight: 900,
                  color: opt.color,
                  textShadow: `0 0 25px ${opt.glow}`,
                  lineHeight: 1,
                }}
              >
                {opt.label}
              </span>
              <span
                style={{
                  fontFamily: THEME_FONTS.main,
                  fontSize: 22,
                  fontWeight: 700,
                  color: "rgba(255,255,255,0.75)",
                  marginTop: 4,
                }}
              >
                COMMENT
              </span>
            </div>
          ))}
        </div>

        {/* EN-only CTA sub-line — captions file holds BN/HI translations */}
        <div
          style={{
            textAlign: "center",
            background: "rgba(5,5,20,0.8)",
            padding: "14px 36px",
            borderRadius: 16,
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 26,
              fontWeight: 700,
              color: THEME_COLORS.goldHighlight,
              letterSpacing: 0.5,
            }}
          >
            Drop your answer below! 👇
          </div>
        </div>

        {/* "Answer in next Reel" teaser */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(123,47,190,0.6), rgba(74,20,140,0.6))",
            border: "2px solid rgba(255,215,0,0.5)",
            borderRadius: 50,
            padding: "12px 36px",
            textAlign: "center",
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 26,
              fontWeight: 700,
              color: THEME_COLORS.goldHighlight,
              letterSpacing: 0.5,
            }}
          >
            🔔 Answer in the next Reel!
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 5 — Game Promotion (16–20s / Frames 480–600)
// ─────────────────────────────────────────────────────────────────────────────
const PromoScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({ frame, fps, config: SPRING_PRESETS.smooth });
  const ctaScale = spring({ frame: frame - 15, fps, config: SPRING_PRESETS.celebrate });
  const logoScale = spring({ frame: frame - 5, fps, config: SPRING_PRESETS.pop });

  const bgOpacity = interpolate(frame, [0, 20], [0, 0.9], {
    extrapolateRight: "clamp",
  });

  const playPulse = 1 + Math.sin(frame * 0.25) * 0.04;

  return (
    <AbsoluteFill style={{ zIndex: 20, pointerEvents: "none" }}>
      {/* Full overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: `rgba(5,5,15,${bgOpacity})`,
          zIndex: 10,
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 32,
          zIndex: 50,
          padding: "0 50px",
        }}
      >
        {/* Game icon / logo area */}
        <div
          style={{
            transform: `scale(${logoScale})`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            style={{
              width: 160,
              height: 160,
              borderRadius: 40,
              background: "linear-gradient(135deg, #7B2FBE, #4A1A7A)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 80,
              boxShadow: `0 0 60px rgba(123,47,190,0.8), 0 20px 50px rgba(0,0,0,0.9)`,
              border: `4px solid ${THEME_COLORS.goldHighlight}`,
            }}
          >
            🧩
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 54,
              fontWeight: 900,
              color: "#FFFFFF",
              textShadow: "0 4px 20px rgba(0,0,0,0.9)",
              textAlign: "center",
            }}
          >
            Block Puzzle Burst
          </div>
        </div>

        {/* Want to play line */}
        <div
          style={{
            transform: `scale(${entrance})`,
            textAlign: "center",
            background: "rgba(5,5,20,0.7)",
            padding: "16px 40px",
            borderRadius: 20,
            border: "1px solid rgba(255,255,255,0.1)",
          }}
        >
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 42,
              fontWeight: 800,
              color: "#FFFFFF",
              textShadow: "0 3px 15px rgba(0,0,0,0.9)",
            }}
          >
            Want to play this puzzle?
          </div>
          <div
            style={{
              fontFamily: THEME_FONTS.main,
              fontSize: 30,
              fontWeight: 600,
              color: "rgba(255,255,255,0.75)",
              marginTop: 8,
            }}
          >
            It's FREE & super addictive! 🔥
          </div>
        </div>

        {/* PLAY NOW button */}
        <div
          style={{
            transform: `scale(${ctaScale * playPulse})`,
            background: `linear-gradient(135deg, ${THEME_COLORS.goldHighlight}, #FFA000)`,
            padding: "22px 72px",
            borderRadius: 60,
            border: "4px solid #FFFFFF",
            boxShadow: `0 0 60px ${THEME_COLORS.goldGlow}, 0 15px 40px rgba(0,0,0,0.9)`,
            textAlign: "center",
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 54,
              fontWeight: 900,
              color: "#1A1A1A",
              letterSpacing: 2,
            }}
          >
            PLAY NOW 🎮
          </span>
        </div>

        {/* Link in bio CTA */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            background: "rgba(5,5,20,0.85)",
            padding: "14px 40px",
            borderRadius: 50,
            border: "2px solid rgba(255,215,0,0.5)",
            boxShadow: "0 8px 25px rgba(0,0,0,0.7)",
          }}
        >
          <span style={{ fontSize: 36 }}>🔗</span>
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 36,
              fontWeight: 800,
              color: THEME_COLORS.goldHighlight,
              letterSpacing: 1,
            }}
          >
            Link in Bio!
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPOSITION
// ─────────────────────────────────────────────────────────────────────────────
export const SolveItReelContent: React.FC = () => {
  const frame = useCurrentFrame();

  // Determine which scene we're in for video source control
  const videoSrc = staticFile("gameplay2.mp4");

  // Source frame mapping:
  // The video is ~201s at ~48fps = ~9746 frames
  // We pick a mid-game dense board moment ~ around t=100s
  // t=100s → approximately frame 4800 in source
  const SOURCE_HOOK_START = 4200;    // Dense board, active gameplay
  const SOURCE_CHALLENGE  = 4320;    // Board state matching screenshots (paused)
  const SOURCE_RESUME     = 4800;    // Resume after reveal
  
  // Initial fade in
  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME_COLORS.background,
        overflow: "hidden",
        opacity: fadeIn,
      }}
    >
      {/* ── VIDEO LAYER ── */}

      {/* Scene 1 (0–90): Live gameplay action hook */}
      <Sequence from={0} durationInFrames={90} name="S1 Video">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={SOURCE_HOOK_START}
            playbackRate={1.2}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* Scene 2 (90–210): Freeze board to show challenge */}
      <Sequence from={90} durationInFrames={120} name="S2 Video">
        <AbsoluteFill>
          <Freeze frame={SOURCE_CHALLENGE}>
            <OffthreadVideo
              src={videoSrc}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </Freeze>
        </AbsoluteFill>
      </Sequence>

      {/* Scene 3 (210–360): Frozen board during countdown */}
      <Sequence from={210} durationInFrames={150} name="S3 Video">
        <AbsoluteFill>
          <Freeze frame={SOURCE_CHALLENGE}>
            <OffthreadVideo
              src={videoSrc}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </Freeze>
        </AbsoluteFill>
      </Sequence>

      {/* Scene 4 (360–480): Dark overlay, board less prominent */}
      <Sequence from={360} durationInFrames={120} name="S4 Video">
        <AbsoluteFill>
          <Freeze frame={SOURCE_CHALLENGE}>
            <OffthreadVideo
              src={videoSrc}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </Freeze>
        </AbsoluteFill>
      </Sequence>

      {/* Scene 5 (480–600): Live gameplay as background */}
      <Sequence from={480} durationInFrames={120} name="S5 Video">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={SOURCE_RESUME}
            playbackRate={1.0}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ── OVERLAY SCENES ── */}

      {/* Scene 1: Attention Hook (0–90) */}
      <Sequence from={0} durationInFrames={90} name="S1 Overlay">
        <HookScene />
      </Sequence>

      {/* Scene 2: Show Challenge (90–210) */}
      <Sequence from={90} durationInFrames={120} name="S2 Overlay">
        <ChallengeScene />
      </Sequence>

      {/* Scene 3: Countdown (210–360) */}
      <Sequence from={210} durationInFrames={150} name="S3 Overlay">
        <ThinkingScene />
      </Sequence>

      {/* Scene 4: Interaction CTA (360–480) */}
      <Sequence from={360} durationInFrames={120} name="S4 Overlay">
        <InteractionScene />
      </Sequence>

      {/* Scene 5: Game Promo (480–600) */}
      <Sequence from={480} durationInFrames={120} name="S5 Overlay">
        <PromoScene />
      </Sequence>

      {/* Global bottom-of-screen safe zone Instagram handle hint */}
      {frame >= 90 && frame < 480 && (
        <div
          style={{
            position: "absolute",
            bottom: 24,
            right: 36,
            fontFamily: THEME_FONTS.main,
            fontSize: 22,
            fontWeight: 600,
            color: "rgba(255,255,255,0.45)",
            zIndex: 100,
            pointerEvents: "none",
          }}
        >
          @BlockPuzzleBurst
        </div>
      )}
    </AbsoluteFill>
  );
};

export const SolveItReel: React.FC = () => {
  return (
    <Composition
      id="SolveItReel"
      component={SolveItReelContent}
      durationInFrames={CONFIG.totalFrames}
      fps={CONFIG.fps}
      width={CANVAS_SPECS.width}
      height={CANVAS_SPECS.height}
      defaultProps={{}}
    />
  );
};
