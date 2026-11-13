import React from "react";
import { AbsoluteFill, Composition, OffthreadVideo, staticFile } from "remotion";

const FrameFinderView: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#0D0D0D" }}>
      <OffthreadVideo
        src={staticFile("gameplay.mp4")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          objectPosition: "center",
        }}
      />
    </AbsoluteFill>
  );
};

export const FrameFinder: React.FC = () => {
  return (
    <Composition
      id="FrameFinder"
      component={FrameFinderView}
      durationInFrames={5200}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
