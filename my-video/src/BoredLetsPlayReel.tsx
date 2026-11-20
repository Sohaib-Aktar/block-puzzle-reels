import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  Img,
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

// ─────────────────────────────────────────────────────────────────────────────
// COMPOSITION CONSTANTS
// Duration: 20 seconds @ 30fps = 600 frames
// Lifestyle clip: lifestyle_commute_cfr30.mp4 (10s / 300 frames @ 30fps)
// Gameplay clip:  gameplay_bored_cfr30.mp4 (20s / converted from 55s–75s of recording_1)
// BGM: bgm_bored_lets_play.m4a (25s, apalonbeats upbeat no-copyright)
// ─────────────────────────────────────────────────────────────────────────────

const TOTAL_FRAMES = 600; // 20.0s @ 30fps
const FPS = 30;

// Scene frame boundaries (at 30fps)
// Scene 1: Office tired          0 → 75   (0.0s – 2.5s = 2.5s)
// Scene 2: Metro bored           75 → 180  (2.5s – 6.0s = 3.5s)
// Scene 3: Phone discovery       180 → 260 (6.0s – 8.67s = 2.67s)
// Scene 4: Splash screen & zoom  260 → 330 (8.67s – 11.0s = 2.33s)
// Scene 5: Gameplay active       330 → 525 (11.0s – 17.5s = 6.5s)
// Scene 6: Branded outro         525 → 600 (17.5s – 20.0s = 2.5s)

const S1_START = 0;
const S1_END = 75;
const S2_START = 75;
const S2_END = 180;
const S3_START = 180;
const S3_END = 250;
const S4_START = 250;
const S4_END = 330;
const S5_START = 330;
const S5_END = 525;
const S6_START = 525;
const S6_END = 600;

// Lifestyle source timecodes (source is 10s = 300 frames at 30fps)
// Scene 1 uses source 0s–2.5s   → startFrom=0
// Scene 2 uses source 2.5s–6.5s → startFrom=75 (but OffthreadVideo is shared; we reuse from S2 start)
// We use ONE OffthreadVideo for the lifestyle clip beneath all scenes 1–3,
// and a second OffthreadVideo for scene 4 (the phone hold-up with white screen)

// ─────────────────────────────────────────────────────────────────────────────
// CONTENT COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export const BoredLetsPlayReelContent: React.FC = () => {
  const frame = useCurrentFrame();
  useVideoConfig();

  // Master fade-in / fade-out
  const masterFadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const masterFadeOut = interpolate(frame, [585, 600], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const masterOpacity = masterFadeIn * masterFadeOut;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#070B14",
        opacity: masterOpacity,
        overflow: "hidden",
      }}
    >
      {/* ───────────────────────────────────────────────────────────────────
          AUDIO: Background Music (full reel, fades in/out)
      ─────────────────────────────────────────────────────────────────── */}
      <Audio
        src={staticFile("bgm_bored_lets_play.m4a")}
        volume={(f) =>
          interpolate(
            f,
            [0, 20, S5_START, S5_START + 15, S5_END - 15, S5_END, S6_END - 15, S6_END],
            [0,  0.55, 0.55,  0.25,           0.25,          0.55,  0.55,         0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          )
        }
      />

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 1: OFFICE — TIRED (0 → 75 frames / 0s–2.5s)
          Source: lifestyle_commute_cfr30.mp4 starting at frame 0
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S1_START} durationInFrames={S1_END - S1_START} name="Scene 1: Office Tired">
        <LifestyleClipScene
          src={staticFile("lifestyle_commute_cfr30.mp4")}
          srcStartFrame={0}
          sceneDuration={S1_END - S1_START}
          overlayText="Tired after a long day? 😴"
          textDelay={8}
          wipeIn
          watermarkCover
          includeAudio={false}
        />
      </Sequence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 2: METRO — BORED COMMUTE (75 → 180 / 2.5s–6.0s)
          Source: lifestyle clip from 2.5s (frame 75)
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S2_START} durationInFrames={S2_END - S2_START} name="Scene 2: Bored Commute">
        <LifestyleClipScene
          src={staticFile("lifestyle_commute_cfr30.mp4")}
          srcStartFrame={75}
          sceneDuration={S2_END - S2_START}
          overlayText="Long commute. Nothing to do? 😑"
          textDelay={12}
          wipeIn
          watermarkCover
          includeAudio={false}
        />
      </Sequence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 3: PHONE DISCOVERY (180 → 260 / 6.0s–8.67s)
          Source: lifestyle clip from 6.0s (frame 180) — man looks at phone
          Ends at frame 260 BEFORE the phone turns forward to camera
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S3_START} durationInFrames={S3_END - S3_START} name="Scene 3: Phone Discovery">
        <LifestyleClipScene
          src={staticFile("lifestyle_commute_cfr30.mp4")}
          srcStartFrame={180}
          sceneDuration={S3_END - S3_START}
          overlayText="Why stay bored? 🤔"
          textDelay={10}
          wipeIn
          watermarkCover
          zoomPulse
          includeAudio={false}
        />
      </Sequence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 4: PHONE REVEAL & SPLASH SCREEN → ZOOM TO GAMEPLAY (260 → 330 / 8.67s–11.0s)
          Source: lifestyle_splash_cfr30.mp4 (phone screen 100% displays official splash screen)
          Zero white screen, zero fake bezels, seamless cinematic zoom into gameplay
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S4_START} durationInFrames={S4_END - S4_START} name="Scene 4: Splash Screen & Zoom">
        <PhoneScreenLogoScene
          src={staticFile("lifestyle_splash_cfr30.mp4")}
          srcStartFrame={0}
          sceneDuration={S4_END - S4_START}
          gameplaySrc={staticFile("gameplay_bored_cfr30.mp4")}
        />
      </Sequence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 5: AUTHENTIC GAMEPLAY (345 → 525 / 11.5s–17.5s = 6s)
          Source: gameplay_bored_cfr30.mp4 (from 55s–75s of recording_1)
          Using startFrom=0 (already trimmed during asset preparation)
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S5_START} durationInFrames={S5_END - S5_START} name="Scene 5: Gameplay">
        <GameplayScene
          src={staticFile("gameplay_bored_cfr30.mp4")}
          srcStartFrame={0}
          sceneDuration={S5_END - S5_START}
          pillText="Let's Play! 🧩"
          gameIconSrc={staticFile("icon_block_game.png")}
        />
      </Sequence>

      {/* ───────────────────────────────────────────────────────────────────
          SCENE 6: BRANDED OUTRO (525 → 600 / 17.5s–20.0s = 2.5s)
      ─────────────────────────────────────────────────────────────────── */}
      <Sequence from={S6_START} durationInFrames={S6_END - S6_START} name="Scene 6: Branded Outro">
        <BrandedOutroScene
          title="BLOCK PUZZLE BURST"
          subtitle="Turn boring moments into fun!"
          cta="Play Free Today 🧩"
          studioIconSrc={staticFile("pyapiras_games_icon.png")}
          gameIconSrc={staticFile("icon_block_game.png")}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SUB-COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lifestyle video scene with animated text overlay and watermark cover badge
 */
const LifestyleClipScene: React.FC<{
  src: string;
  srcStartFrame: number;
  sceneDuration: number;
  overlayText: string;
  textDelay?: number;
  wipeIn?: boolean;
  watermarkCover?: boolean;
  zoomPulse?: boolean;
  includeAudio?: boolean;
}> = ({
  src,
  srcStartFrame,
  sceneDuration,
  overlayText,
  textDelay = 8,
  wipeIn = false,
  watermarkCover = true,
  zoomPulse = false,
  includeAudio = false,
}) => {
  const frame = useCurrentFrame();
  useVideoConfig();

  // Ken Burns gentle zoom
  const scale = interpolate(frame, [0, sceneDuration], [1.0, zoomPulse ? 1.14 : 1.06], {
    extrapolateRight: "clamp",
  });

  // Text banner animation: slide up from below
  const bannerY = interpolate(frame, [textDelay, textDelay + 18], [60, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bannerOpacity = interpolate(frame, [textDelay, textDelay + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bannerExit = interpolate(
    frame,
    [sceneDuration - 12, sceneDuration - 2],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Cross-fade wipe between scenes
  const wipeOpacity = wipeIn
    ? interpolate(frame, [0, 8], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  return (
    <AbsoluteFill style={{ overflow: "hidden", opacity: wipeOpacity }}>
      {/* Video layer */}
      <OffthreadVideo
        src={src}
        startFrom={srcStartFrame}
        volume={includeAudio ? 0.3 : 0}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      />

      {/* Cinematic vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 40%, rgba(0,0,0,0.60) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Top gradient safe area */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 200,
          background: "linear-gradient(to bottom, rgba(0,0,0,0.5), transparent)",
          pointerEvents: "none",
        }}
      />

      {/* Floating text banner — upper safe area */}
      <div
        style={{
          position: "absolute",
          top: 240,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `translateY(${bannerY}px)`,
          opacity: bannerOpacity * bannerExit,
          padding: "0 44px",
          pointerEvents: "none",
          zIndex: 40,
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(10, 5, 30, 0.93), rgba(20, 5, 50, 0.93))",
            backdropFilter: "blur(14px)",
            padding: "18px 44px",
            borderRadius: 60,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 12px 40px rgba(0,0,0,0.85), 0 0 24px ${THEME_COLORS.goldGlowSoft}`,
            textAlign: "center",
            maxWidth: 980,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 50,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
              letterSpacing: 0.5,
              textShadow: "0 4px 14px rgba(0,0,0,0.9)",
            }}
          >
            {overlayText}
          </span>
        </div>
      </div>

      {/* Watermark cover: Pyapiras Games badge positioned directly over the Gemini sparkle (center at x:900, y:1740) */}
      {watermarkCover && (
        <div
          style={{
            position: "absolute",
            bottom: 120,
            right: 120,
            width: 120,
            height: 120,
            borderRadius: "50%",
            overflow: "hidden",
            border: "3px solid rgba(255, 215, 0, 0.75)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.85), 0 0 20px rgba(123,47,190,0.5)",
            zIndex: 50,
            opacity: interpolate(frame, [0, 6], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          <Img
            src={staticFile("pyapiras_games_icon.png")}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

/**
 * Scene 4: Phone Reveal & Splash Screen → Zoom into Authentic Gameplay
 * 1. Commuter holds phone forward naturally, revealing official Block Puzzle Burst splash screen.
 * 2. Splash screen displays subtle glowing pulse animation on the game logo squircle.
 * 3. Camera smoothly zooms in (scale 1.0 -> 2.48) centered directly on the phone display (535px, 980px).
 * 4. Resolves seamlessly into full-screen authentic gameplay without overlapping layers or duplicate bezels.
 */
const PhoneScreenLogoScene: React.FC<{
  src: string;
  srcStartFrame: number;
  sceneDuration: number;
  gameplaySrc: string;
}> = ({ src, srcStartFrame, sceneDuration, gameplaySrc }) => {
  const frame = useCurrentFrame();
  useVideoConfig();

  // Full solid video opacity from frame 0 - zero blank or dark frames
  const videoOpacity = 1;

  // Top banner "Let's Play! 🎮" animation
  const bannerY = interpolate(frame, [4, 18], [50, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bannerOpacity = interpolate(frame, [4, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bannerFadeOut = interpolate(frame, [36, 48], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Subtle splash screen animation: gentle aura pulse on the logo (frames 0 to 48)
  const logoPulseScale = interpolate(frame, [0, 22, 45], [0.94, 1.08, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const logoAuraOpacity = interpolate(frame, [0, 18, 36, 48], [0.2, 0.65, 0.4, 0.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Cinematic zoom directly into the phone screen display (frames 38 to 74)
  // Origin centered on the phone display (x: 535px, y: 980px)
  // Scales by 2.48x to cleanly fill the full 1080x1920 vertical canvas
  const transitionZoom = interpolate(frame, [38, 74], [1.0, 2.48], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Seamless dissolve from zooming splash screen into full-screen gameplay (frames 58 to 74)
  const gameplayCrossFade = interpolate(frame, [58, 74], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Watermark cover badge fades out as zoom progresses
  const badgeFade = interpolate(frame, [36, 48], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#070B14" }}>
      {/* Zooming container centered on the phone screen display */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${transitionZoom})`,
          transformOrigin: "535px 980px",
        }}
      >
        {/* Lifestyle video with splash screen perfectly composited into phone display */}
        <div style={{ position: "absolute", inset: 0, opacity: videoOpacity }}>
          <OffthreadVideo
            src={src}
            startFrom={srcStartFrame}
            volume={0}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </div>

        {/* Subtle splash screen logo aura pulse centered on phone logo (x: 535, y: 980) */}
        {frame < 45 && (
          <div
            style={{
              position: "absolute",
              left: 535 - 120,
              top: 980 - 120,
              width: 240,
              height: 240,
              borderRadius: "50%",
              background:
                "radial-gradient(circle, rgba(255, 215, 0, 0.45) 0%, rgba(123, 47, 190, 0.25) 50%, transparent 70%)",
              transform: `scale(${logoPulseScale})`,
              opacity: logoAuraOpacity,
              pointerEvents: "none",
              zIndex: 30,
            }}
          />
        )}

        {/* Cinematic vignette */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,0.5) 100%)",
            pointerEvents: "none",
          }}
        />

        {/* Seamless gameplay dissolve layer: appears at the peak of zoom to resolve cleanly into full screen */}
        {gameplayCrossFade > 0 && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: gameplayCrossFade,
              zIndex: 35,
            }}
          >
            <OffthreadVideo
              src={gameplaySrc}
              startFrom={0}
              volume={0}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          </div>
        )}
      </div>

      {/* Top Banner: "Let's Play! 🎮" (anchored to viewport, does not zoom with phone) */}
      <div
        style={{
          position: "absolute",
          top: 240,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          transform: `translateY(${bannerY}px)`,
          opacity: bannerOpacity * bannerFadeOut,
          pointerEvents: "none",
          zIndex: 50,
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(123, 47, 190, 0.96), rgba(74, 26, 122, 0.96))",
            padding: "16px 48px",
            borderRadius: 50,
            border: `2.5px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 10px 35px rgba(0,0,0,0.8), 0 0 25px ${THEME_COLORS.goldGlowSoft}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 46,
              fontWeight: 900,
              color: THEME_COLORS.textPrimary,
              textShadow: "0 4px 14px rgba(0,0,0,0.9)",
            }}
          >
            Let's Play! 🎮
          </span>
        </div>
      </div>

      {/* Watermark cover: Pyapiras Games badge pinned over the Gemini sparkle */}
      {badgeFade > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 120,
            right: 120,
            width: 120,
            height: 120,
            borderRadius: "50%",
            overflow: "hidden",
            border: "3px solid rgba(255, 215, 0, 0.75)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.85), 0 0 20px rgba(123,47,190,0.5)",
            opacity: badgeFade,
            zIndex: 60,
          }}
        >
          <Img
            src={staticFile("pyapiras_games_icon.png")}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

/**
 * Scene 5: Authentic gameplay with animated pill banner
 */
const GameplayScene: React.FC<{
  src: string;
  srcStartFrame: number;
  sceneDuration: number;
  pillText: string;
  gameIconSrc: string;
}> = ({ src, srcStartFrame, sceneDuration, pillText, gameIconSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  void sceneDuration;

  const pillSpring = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  // Top pill callout pops in at start of gameplay, stays for 1.5s, then gracefully fades out
  // so the genuine score, streak, and grid are 100% unobstructed!
  const pillFadeOut = interpolate(frame, [40, 55], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // "BLOCK PUZZLE BURST" label appears at frame 20 and remains cleanly anchored at bottom
  const titleOpacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade in video
  const videoFade = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#070B14", overflow: "hidden" }}>
      {/* Authentic gameplay video */}
      <div style={{ opacity: videoFade, position: "absolute", inset: 0 }}>
        <OffthreadVideo
          src={src}
          startFrom={srcStartFrame}
          volume={0.6}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />
      </div>

      {/* Top pill banner: "Let's Play!" - brief energetic splash */}
      {frame < 58 && (
        <div
          style={{
            position: "absolute",
            top: 230,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            transform: `scale(${pillSpring})`,
            opacity: pillFadeOut,
            zIndex: 50,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              background:
                "linear-gradient(135deg, rgba(123, 47, 190, 0.95), rgba(30, 10, 60, 0.95))",
              padding: "12px 40px",
              borderRadius: 50,
              border: `2.5px solid ${THEME_COLORS.goldHighlight}`,
              boxShadow: `0 10px 40px rgba(0,0,0,0.8), 0 0 30px ${THEME_COLORS.purpleGlow}`,
            }}
          >
            <span
              style={{
                fontFamily: THEME_FONTS.headings,
                fontSize: 38,
                fontWeight: 900,
                color: THEME_COLORS.textPrimary,
                letterSpacing: 0.5,
                textShadow: "0 4px 14px rgba(0,0,0,0.9)",
              }}
            >
              {pillText}
            </span>
          </div>
        </div>
      )}

      {/* Bottom: "BLOCK PUZZLE BURST" title */}
      <div
        style={{
          position: "absolute",
          bottom: 290,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 18,
          opacity: titleOpacity,
          zIndex: 50,
          pointerEvents: "none",
        }}
      >
        <Img
          src={gameIconSrc}
          style={{
            width: 64,
            height: 64,
            borderRadius: 14,
            boxShadow: "0 6px 20px rgba(0,0,0,0.8)",
            border: "2px solid rgba(255,215,0,0.6)",
          }}
        />
        <div
          style={{
            background: "rgba(10, 15, 30, 0.90)",
            backdropFilter: "blur(10px)",
            padding: "12px 32px",
            borderRadius: 30,
            border: "1.5px solid rgba(255,215,0,0.6)",
            boxShadow: "0 6px 20px rgba(0,0,0,0.6)",
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 30,
              fontWeight: 800,
              color: THEME_COLORS.goldHighlight,
              letterSpacing: 1.5,
              textTransform: "uppercase",
            }}
          >
            Block Puzzle Burst
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Scene 6: Official branded outro card
 */
const BrandedOutroScene: React.FC<{
  title: string;
  subtitle: string;
  cta: string;
  studioIconSrc: string;
  gameIconSrc: string;
}> = ({ title, subtitle, cta, studioIconSrc, gameIconSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: SPRING_PRESETS.smooth,
  });

  const ctaOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#070B14",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 50px",
        zIndex: 60,
      }}
    >
      {/* Subtle radial glow background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(123,47,190,0.18) 0%, rgba(7,11,20,0) 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          transform: `scale(${scale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          maxWidth: 980,
          zIndex: 10,
        }}
      >
        {/* Brand icons row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 28,
            marginBottom: 36,
          }}
        >
          <Img
            src={gameIconSrc}
            style={{
              width: 150,
              height: 150,
              borderRadius: 34,
              boxShadow: `0 14px 45px rgba(0,0,0,0.8), 0 0 35px ${THEME_COLORS.goldGlowSoft}`,
              border: `3px solid ${THEME_COLORS.goldHighlight}`,
            }}
          />
          <Img
            src={studioIconSrc}
            style={{
              width: 150,
              height: 150,
              borderRadius: "50%",
              boxShadow: `0 14px 45px rgba(0,0,0,0.8), 0 0 35px ${THEME_COLORS.purpleGlow}`,
              border: `3px solid ${THEME_COLORS.purpleBorder}`,
            }}
          />
        </div>

        {/* Title */}
        <h1
          style={{
            fontFamily: THEME_FONTS.headings,
            fontSize: 58,
            fontWeight: 900,
            color: THEME_COLORS.textPrimary,
            margin: "0 0 16px 0",
            letterSpacing: 1,
            textShadow: "0 4px 18px rgba(0,0,0,0.9)",
          }}
        >
          {title}
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 34,
            fontWeight: 600,
            color: THEME_COLORS.goldHighlight,
            margin: "0 0 40px 0",
            letterSpacing: 0.5,
          }}
        >
          {subtitle}
        </p>

        {/* CTA */}
        <div
          style={{
            opacity: ctaOpacity,
            background:
              "linear-gradient(135deg, rgba(123,47,190,0.98), rgba(74,26,122,0.98))",
            padding: "20px 56px",
            borderRadius: 60,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 10px 40px rgba(0,0,0,0.7), 0 0 35px ${THEME_COLORS.goldGlowSoft}`,
            marginBottom: 32,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 36,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
              letterSpacing: 0.5,
            }}
          >
            {cta}
          </span>
        </div>

        {/* Studio credit */}
        <div
          style={{
            fontSize: 26,
            fontFamily: THEME_FONTS.main,
            fontWeight: 700,
            color: "rgba(255,255,255,0.65)",
            letterSpacing: 2,
            textTransform: "uppercase",
          }}
        >
          Pyapiras Games
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// COMPOSITION REGISTRATION
// ─────────────────────────────────────────────────────────────────────────────

export const BoredLetsPlayReel: React.FC = () => {
  return (
    <Composition
      id="BoredLetsPlayReel"
      component={BoredLetsPlayReelContent}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={CANVAS_SPECS.width}   // 1080
      height={CANVAS_SPECS.height} // 1920
    />
  );
};
