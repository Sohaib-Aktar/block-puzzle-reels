import React from "react";
import { FrameFinder } from "./FrameFinder";
import { MyDayThreeReel } from "./MyDayThreeReel";
import { MyDayTwoReel } from "./MyDayTwoReel";
import { SolveItReel } from "./SolveItReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <FrameFinder />
      <MyDayTwoReel />
      <MyDayThreeReel />
      <SolveItReel />
    </>
  );
};
