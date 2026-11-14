import React from "react";
import {
  AbsoluteFill,
  Composition,
  Freeze,
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
  CandidateBadge,
  CountdownBar,
  HookBanner,
  OutroCard,
  SolutionBox,
} from "./components";

/**
 * CONFIGURATION - Day 3 Puzzle Challenge
 * Frame 1780 features a 93.2% filled block board with all 3 candidate pieces waiting in the tray.
 */
export const CONFIG = {
  pauseAtVideoFrame: 1780,
  badgePositions: {
    A: { x: 284, y: 1540 },
    B: { x: 540, y: 1540 },
    C: { x: 820, y: 1540 },
  },
  solutionBox: {
    x: 390,
    y: 690,
    width: 260,
    height: 260,
  },
  correctAnswer: "B" as "A" | "B" | "C",
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
 * Container component for candidate badges A, B, C
 */
const CandidateBadgesGroup: React.FC<{
  positions: typeof CONFIG.badgePositions;
  correctAnswer: "A" | "B" | "C";
}> = ({ positions, correctAnswer }) => {
  const frame = useCurrentFrame();

  // Answer reveal begins at local frame 300 (which corresponds to composition frame 345)
  const isRevealed = frame >= 300;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <CandidateBadge
        label="A"
        x={positions.A.x}
        y={positions.A.y}
        isCorrect={correctAnswer === "A"}
        isRevealed={isRevealed}
        staggerDelay={0}
      />
      <CandidateBadge
        label="B"
        x={positions.B.x}
        y={positions.B.y}
        isCorrect={correctAnswer === "B"}
        isRevealed={isRevealed}
        staggerDelay={15}
      />
      <CandidateBadge
        label="C"
        x={positions.C.x}
        y={positions.C.y}
        isCorrect={correctAnswer === "C"}
        isRevealed={isRevealed}
        staggerDelay={30}
      />
    </AbsoluteFill>
  );
};

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
        backgroundColor: THEME_COLORS.background,
        opacity: initialFadeIn,
        overflow: "hidden",
      }}
    >
      {/* 
        1. Frames 0 - 45: Smooth entrance into pause point (frames 1735 -> 1780)
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
        Freeze board at pauseAtVideoFrame (93.2% full board, all 3 pieces clear in tray)
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
        Unfreeze gameplay so viewer sees Piece B placed and line-clear combo burst!
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
        Background underlay during outro card
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
        <HookBanner title={hookText} subtitle="Find the winning move!" />
      </Sequence>

      {/* 0:01.5 - 0:14.0 (Frames 45 - 420): Candidate Badges A, B, C */}
      <Sequence from={45} durationInFrames={375} name="Badges Overlay">
        <CandidateBadgesGroup
          positions={config.badgePositions}
          correctAnswer={config.correctAnswer}
        />
      </Sequence>

      {/* 0:06.5 - 0:11.5 (Frames 195 - 345): Thinking 5-Dot Countdown */}
      <Sequence from={195} durationInFrames={150} name="Countdown Timer">
        <CountdownBar totalDots={5} framesPerDot={30} />
      </Sequence>

      {/* 0:11.5 - 0:14.0 (Frames 345 - 420): Glowing Solution Box Highlight */}
      <Sequence from={345} durationInFrames={75} name="Solution Highlight">
        <SolutionBox
          x={config.solutionBox.x}
          y={config.solutionBox.y}
          width={config.solutionBox.width}
          height={config.solutionBox.height}
          label="WINNING MOVE!"
        />
      </Sequence>

      {/* 0:14.0 - 0:15.0 (Frames 420 - 450): Outro Call-To-Action Card */}
      <Sequence from={420} durationInFrames={30} name="Outro Card">
        <OutroCard
          headline="Block Puzzle Burst"
          subheadline="Did you spot it in time? 🧩"
          callToAction="Comment A, B or C below 👇"
        />
      </Sequence>
    </AbsoluteFill>
  );
};

export const MyDayThreeReel: React.FC = () => {
  return (
    <Composition
      id="MyDayThreeReel"
      component={MyDayThreeReelContent}
      durationInFrames={CANVAS_SPECS.defaultDurationInFrames}
      fps={CANVAS_SPECS.fps}
      width={CANVAS_SPECS.width}
      height={CANVAS_SPECS.height}
      defaultProps={{
        videoSrc: staticFile("gameplay.mp4"),
        config: CONFIG,
      }}
    />
  );
};
