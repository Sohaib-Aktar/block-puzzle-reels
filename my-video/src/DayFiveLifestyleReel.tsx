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

export interface DayFiveLifestyleReelProps {
  gameplaySrc?: string;
  hookScene1Text?: string;
  hookScene2Text?: string;
  hookScene3Text?: string;
  hookScene4Text?: string;
  gameplayPillText?: string;
  outroTitle?: string;
  outroSubtitle?: string;
  outroCta?: string;
}

export const DayFiveLifestyleReelContent: React.FC<DayFiveLifestyleReelProps> = ({
  gameplaySrc = staticFile("recording_3_cfr30.mp4"),
  hookScene1Text = "Long day at work...",
  hookScene2Text = "Finally, heading home.",
  hookScene3Text = "Still feeling bored?",
  hookScene4Text = "Time for a little break.",
  gameplayPillText = "Play. Place. Enjoy. ✨",
  outroTitle = "Block Puzzle Burst",
  outroSubtitle = "Your Perfect Offline Escape",
  outroCta = "Play Free Today 🧩",
}) => {
  const frame = useCurrentFrame();

  // Master fade-in & fade-out
  const masterFadeIn = interpolate(frame, [0, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const masterFadeOut = interpolate(frame, [645, 660], [1, 0], {
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
      {/* 
        =============================================================
        AUDIO TRACKS (BGM + VOICEOVERS + GAME AUDIO)
        =============================================================
      */}
      {/* Background Music: Ambient Piano & Upbeat Lofi Rhythm (22s) */}
      <Audio
        src={staticFile("bgm_day05.wav")}
        volume={(f) =>
          interpolate(f, [0, 15, 360, 450, 600, 645, 660], [0, 0.45, 0.45, 0.30, 0.45, 0.45, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })
        }
      />

      {/* Voiceover 1: Scene 1 (Frames 10 - 80) */}
      <Sequence from={10} durationInFrames={75} name="VO: Scene 1">
        <Audio src={staticFile("vo_scene1.wav")} volume={0.95} />
      </Sequence>

      {/* Voiceover 2: Scene 2 (Frames 100 - 170) */}
      <Sequence from={100} durationInFrames={75} name="VO: Scene 2">
        <Audio src={staticFile("vo_scene2.wav")} volume={0.95} />
      </Sequence>

      {/* Voiceover 3: Scenes 3 & 4 (Frames 200 - 350) */}
      <Sequence from={200} durationInFrames={150} name="VO: Scene 3 & 4">
        <Audio src={staticFile("vo_scene3_4.wav")} volume={0.95} />
      </Sequence>

      {/* Voiceover 4: Outro (Frames 605 - 655) */}
      <Sequence from={605} durationInFrames={50} name="VO: Scene 7 Outro">
        <Audio src={staticFile("vo_scene7.wav")} volume={0.95} />
      </Sequence>

      {/* 
        =============================================================
        SCENE 1: OFFICE DESK (Frames 0 - 90 / 0.0s - 3.0s, 3s)
        Worker typing at laptop, tired evening lighting
        =============================================================
      */}
      <Sequence from={0} durationInFrames={90} name="Scene 1: Office Fatigue">
        <LifestyleImageScene
          imageSrc={staticFile("scene_01_office.jpg")}
          startScale={1.0}
          endScale={1.08}
          panX={0}
          panY={-15}
          overlayText={hookScene1Text}
          sceneDuration={90}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 2: EVENING COMMUTE (Frames 90 - 180 / 3.0s - 6.0s, 3s)
        Window view inside evening metro/transit, amber city lights
        =============================================================
      */}
      <Sequence from={90} durationInFrames={90} name="Scene 2: Transit Commute">
        <LifestyleImageScene
          imageSrc={staticFile("scene_02_commute.jpg")}
          startScale={1.05}
          endScale={1.11}
          panX={-35}
          panY={0}
          overlayText={hookScene2Text}
          sceneDuration={90}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 3: HOME SOFA (Frames 180 - 270 / 6.0s - 9.0s, 3s)
        Arriving home, relaxing on sofa under warm lamplight
        =============================================================
      */}
      <Sequence from={180} durationInFrames={90} name="Scene 3: Home Living Room">
        <LifestyleImageScene
          imageSrc={staticFile("scene_03_home_sofa.jpg")}
          startScale={1.0}
          endScale={1.07}
          panX={15}
          panY={-10}
          overlayText={hookScene3Text}
          sceneDuration={90}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 4: PHONE UNLOCK (Frames 270 - 360 / 9.0s - 12.0s, 3s)
        Hand with wristwatch picking up and unlocking smartphone
        =============================================================
      */}
      <Sequence from={270} durationInFrames={90} name="Scene 4: Phone Unlock">
        <LifestyleImageScene
          imageSrc={staticFile("scene_04_phone_unlock.jpg")}
          startScale={1.02}
          endScale={1.10}
          panX={0}
          panY={-20}
          overlayText={hookScene4Text}
          sceneDuration={90}
          glowEffect={true}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 5: APP LAUNCH & BOARD TRANSITION (Frames 360 - 450 / 12.0s - 15.0s, 3s)
        Icon bounce & opening gameplay sequence from recording
        =============================================================
      */}
      <Sequence from={360} durationInFrames={90} name="Scene 5: App Launch">
        <AppLaunchScene
          gameplaySrc={gameplaySrc}
          iconSrc={staticFile("icon_block_game.png")}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 6: AUTHENTIC GAMEPLAY (Frames 450 - 600 / 15.0s - 20.0s, 5s)
        100% authentic Block Puzzle Burst 10x10 gameplay recording
        Frames 330-480 in CFR30 (11.0s - 16.0s of physical play)
        =============================================================
      */}
      <Sequence from={450} durationInFrames={150} name="Scene 6: Genuine Gameplay">
        <GameplayScene
          gameplaySrc={gameplaySrc}
          pillText={gameplayPillText}
        />
      </Sequence>

      {/* 
        =============================================================
        SCENE 7: BRANDED STUDIO OUTRO (Frames 600 - 660 / 20.0s - 22.0s, 2s)
        Pyapiras Games studio icon + Block Puzzle Burst app icon
        =============================================================
      */}
      <Sequence from={600} durationInFrames={60} name="Scene 7: Branded Outro">
        <BrandedOutroScene
          title={outroTitle}
          subtitle={outroSubtitle}
          cta={outroCta}
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
 * Scene component for photorealistic lifestyle keyframes with Ken Burns effect
 */
const LifestyleImageScene: React.FC<{
  imageSrc: string;
  startScale: number;
  endScale: number;
  panX: number;
  panY: number;
  overlayText: string;
  sceneDuration: number;
  glowEffect?: boolean;
}> = ({
  imageSrc,
  startScale,
  endScale,
  panX,
  panY,
  overlayText,
  sceneDuration,
  glowEffect = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = interpolate(frame, [0, sceneDuration], [startScale, endScale], {
    extrapolateRight: "clamp",
  });
  const currentPanX = interpolate(frame, [0, sceneDuration], [0, panX], {
    extrapolateRight: "clamp",
  });
  const currentPanY = interpolate(frame, [0, sceneDuration], [0, panY], {
    extrapolateRight: "clamp",
  });

  // Entrance banner spring
  const bannerSpring = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  const bannerExit = interpolate(frame, [sceneDuration - 12, sceneDuration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={imageSrc}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${currentPanX}px, ${currentPanY}px)`,
          filter: glowEffect ? "brightness(1.06) contrast(1.04)" : "none",
        }}
      />

      {/* Subtle vignette for cinematic depth */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.65) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Floating Story Banner */}
      <div
        style={{
          position: "absolute",
          top: 230, // Strict safe area (>= 220px)
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${bannerSpring})`,
          opacity: bannerExit,
          padding: "0 40px",
          pointerEvents: "none",
          zIndex: 40,
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(20, 10, 40, 0.92), rgba(10, 15, 30, 0.92))",
            backdropFilter: "blur(12px)",
            padding: "18px 46px",
            borderRadius: 60,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 12px 40px rgba(0,0,0,0.8), 0 0 25px ${THEME_COLORS.goldGlowSoft}`,
            textAlign: "center",
            maxWidth: 960,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 48,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
              letterSpacing: 0.5,
              textShadow: "0 4px 12px rgba(0,0,0,0.9)",
            }}
          >
            {overlayText}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Scene 5: App Launch with Icon animation transitioning to game board
 */
const AppLaunchScene: React.FC<{
  gameplaySrc: string;
  iconSrc: string;
}> = ({ gameplaySrc, iconSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Icon pop in frames 0 - 30
  const iconScale = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  const iconFadeOut = interpolate(frame, [25, 40], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const videoFadeIn = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#070B14", overflow: "hidden" }}>
      {/* Background authentic recording opening (Frames 0-90) */}
      <div style={{ position: "absolute", inset: 0, opacity: videoFadeIn }}>
        <OffthreadVideo
          src={gameplaySrc}
          startFrom={0}
          volume={0.7}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />
      </div>

      {/* App Icon Launch Splash Overlay */}
      {frame < 45 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: iconFadeOut,
            transform: `scale(${iconScale})`,
            zIndex: 30,
            pointerEvents: "none",
          }}
        >
          <Img
            src={iconSrc}
            style={{
              width: 190,
              height: 190,
              borderRadius: 44,
              boxShadow: `0 16px 50px rgba(0,0,0,0.8), 0 0 45px ${THEME_COLORS.goldGlow}`,
              border: `4px solid ${THEME_COLORS.goldHighlight}`,
              marginBottom: 24,
            }}
          />
          <div
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 42,
              fontWeight: 900,
              color: THEME_COLORS.textPrimary,
              textShadow: "0 4px 16px rgba(0,0,0,0.9)",
              background: "rgba(10, 15, 30, 0.8)",
              padding: "10px 32px",
              borderRadius: 30,
              border: "1px solid rgba(255, 215, 0, 0.5)",
            }}
          >
            Block Puzzle Burst
          </div>
        </div>
      )}

      {/* Floating Pill Banner */}
      <div
        style={{
          position: "absolute",
          top: 230,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          zIndex: 40,
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(123, 47, 190, 0.95), rgba(74, 26, 122, 0.95))",
            padding: "14px 40px",
            borderRadius: 50,
            border: `2px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 8px 30px rgba(0,0,0,0.7), 0 0 20px ${THEME_COLORS.goldGlowSoft}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 36,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
            }}
          >
            Let's play! 🧩
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Scene 6: 100% Authentic Gameplay recording view with crisp callout
 */
const GameplayScene: React.FC<{
  gameplaySrc: string;
  pillText: string;
}> = ({ gameplaySrc, pillText }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pillSpring = spring({
    frame,
    fps,
    config: SPRING_PRESETS.pop,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#070B14", overflow: "hidden" }}>
      {/* 5 Seconds of Genuine Active Gameplay (CFR30: 330 to 480) */}
      <OffthreadVideo
        src={gameplaySrc}
        startFrom={330}
        volume={1.0}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
        }}
      />

      {/* Safe Area Top Floating Banner */}
      <div
        style={{
          position: "absolute",
          top: 230, // >= 220px safe area
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          transform: `scale(${pillSpring})`,
          zIndex: 50,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(123, 47, 190, 0.95), rgba(30, 10, 60, 0.95))",
            padding: "16px 48px",
            borderRadius: 50,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 10px 40px rgba(0,0,0,0.8), 0 0 30px ${THEME_COLORS.purpleGlow}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 42,
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

      {/* Safe Area Bottom Feature Badge */}
      <div
        style={{
          position: "absolute",
          bottom: 290, // >= 280px safe area
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
            background: "rgba(10, 15, 30, 0.88)",
            backdropFilter: "blur(10px)",
            padding: "10px 32px",
            borderRadius: 30,
            border: "1.5px solid rgba(255, 215, 0, 0.6)",
            boxShadow: "0 6px 20px rgba(0,0,0,0.6)",
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
            100% Offline • Zero Stress • Relaxing Fun
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Scene 7: Official Branded Outro Card
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

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "rgba(7, 11, 20, 0.96)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 50px",
        zIndex: 60,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          maxWidth: 960,
        }}
      >
        {/* Brand Icons Row: Official Studio Badge + Game Squircle Icon */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 28,
            marginBottom: 32,
          }}
        >
          {/* Game Icon */}
          <Img
            src={gameIconSrc}
            style={{
              width: 140,
              height: 140,
              borderRadius: 32,
              boxShadow: `0 14px 45px rgba(0,0,0,0.8), 0 0 35px ${THEME_COLORS.goldGlowSoft}`,
              border: `3px solid ${THEME_COLORS.goldHighlight}`,
            }}
          />
          {/* Studio Badge */}
          <Img
            src={studioIconSrc}
            style={{
              width: 140,
              height: 140,
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
            fontSize: 60,
            fontWeight: 900,
            color: THEME_COLORS.textPrimary,
            margin: "0 0 12px 0",
            letterSpacing: 0.5,
            textShadow: "0 4px 18px rgba(0,0,0,0.9)",
          }}
        >
          {title}
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontFamily: THEME_FONTS.main,
            fontSize: 32,
            fontWeight: 600,
            color: THEME_COLORS.goldHighlight,
            margin: "0 0 36px 0",
            letterSpacing: 0.5,
          }}
        >
          {subtitle}
        </p>

        {/* CTA Button */}
        <div
          style={{
            background:
              "linear-gradient(135deg, rgba(123, 47, 190, 0.98), rgba(74, 26, 122, 0.98))",
            padding: "18px 52px",
            borderRadius: 60,
            border: `3px solid ${THEME_COLORS.goldHighlight}`,
            boxShadow: `0 10px 40px rgba(0,0,0,0.7), 0 0 35px ${THEME_COLORS.goldGlowSoft}`,
          }}
        >
          <span
            style={{
              fontFamily: THEME_FONTS.headings,
              fontSize: 34,
              fontWeight: 800,
              color: THEME_COLORS.textPrimary,
              letterSpacing: 0.5,
            }}
          >
            {cta}
          </span>
        </div>

        {/* Studio Credit */}
        <div
          style={{
            marginTop: 36,
            fontSize: 26,
            fontFamily: THEME_FONTS.main,
            fontWeight: 700,
            color: "rgba(255, 255, 255, 0.75)",
            letterSpacing: 1,
            textTransform: "uppercase",
          }}
        >
          Pyapiras Games
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const DayFiveLifestyleReel: React.FC = () => {
  return (
    <Composition
      id="DayFiveLifestyleReel"
      component={DayFiveLifestyleReelContent}
      durationInFrames={660} // Exactly 22.00 seconds at 30.0 fps
      fps={30}
      width={CANVAS_SPECS.width} // 1080
      height={CANVAS_SPECS.height} // 1920
    />
  );
};
