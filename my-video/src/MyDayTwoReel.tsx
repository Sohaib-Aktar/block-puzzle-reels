import React from "react";
import {
  AbsoluteFill,
  Composition,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import {
  CANVAS_SPECS,
  THEME_COLORS,
} from "./theme/tokens";
import {
  ComboPulse,
  HookBanner,
  OutroCard,
} from "./components";

export interface MyDayTwoReelProps {
  videoSrc?: string;
  startFromFrame?: number;
  hookText?: string;
  gameTitle?: string;
  callToAction?: string;
  showComboBadge?: boolean;
}

export const MyDayTwoReelContent: React.FC<MyDayTwoReelProps> = ({
  videoSrc = staticFile("gameplay.mp4"),
  startFromFrame = 0,
  hookText = "Wait for the last piece...",
  gameTitle = "Block Puzzle Burst",
  callToAction = "Play Free Today 🚀",
  showComboBadge = true,
}) => {
  const frame = useCurrentFrame();

  const initialFadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: THEME_COLORS.background,
        opacity: initialFadeIn,
        overflow: "hidden",
      }}
    >
      {/* 
        1. Segment 1: Frames 0 - 300 (0:00 - 0:10, 10s)
        Normal 1.0x playback speed
      */}
      <Sequence from={0} durationInFrames={300} name="Normal Speed Playback">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame}
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
        2. Segment 2: Frames 300 - 390 (0:10 - 0:13, 3s)
        Slow-Mo 0.3x speed playback
      */}
      <Sequence from={300} durationInFrames={90} name="Slow-Mo Dramatic Playback">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame + 300}
            playbackRate={0.3}
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
        3. Segment 3: Frames 390 - 450 (0:13 - 0:15, 2s)
        Gameplay underlay while outro card transitions in
      */}
      <Sequence from={390} durationInFrames={60} name="Gameplay Outro Underlay">
        <AbsoluteFill>
          <OffthreadVideo
            src={videoSrc}
            startFrom={startFromFrame + 327}
            playbackRate={1.0}
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

      {/* Hook Banner (0:00 - 0:02.5 / Frames 0 - 75) */}
      <Sequence from={0} durationInFrames={75} name="Hook Banner">
        <HookBanner title={hookText} />
      </Sequence>

      {/* Slow-mo Combo Pulse (0:10 - 0:13 / Frames 300 - 390) */}
      {showComboBadge && (
        <Sequence from={300} durationInFrames={90} name="Combo Pulse Overlay">
          <ComboPulse scoreText="COMBO +400" subText="INSANE CLEAR!" />
        </Sequence>
      )}

      {/* Outro CTA Card (0:13 - 0:15 / Frames 390 - 450) */}
      <Sequence from={390} durationInFrames={60} name="Outro Card Overlay">
        <OutroCard
          headline={gameTitle}
          subheadline="Can you beat this score?"
          callToAction={callToAction}
        />
      </Sequence>
    </AbsoluteFill>
  );
};

export const MyDayTwoReel: React.FC = () => {
  return (
    <Composition
      id="MyDayTwoReel"
      component={MyDayTwoReelContent}
      durationInFrames={CANVAS_SPECS.defaultDurationInFrames}
      fps={CANVAS_SPECS.fps}
      width={CANVAS_SPECS.width}
      height={CANVAS_SPECS.height}
      defaultProps={{
        videoSrc: staticFile("gameplay.mp4"),
        startFromFrame: 0,
        hookText: "Wait for the last piece...",
        gameTitle: "Block Puzzle Burst",
        callToAction: "Play Free Today 🚀",
        showComboBadge: true,
      }}
    />
  );
};
