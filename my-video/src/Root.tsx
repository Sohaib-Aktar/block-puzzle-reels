import React from "react";
import { FrameFinder } from "./FrameFinder";
import { MyDayThreeReel } from "./MyDayThreeReel";
import { MyDayTwoReel } from "./MyDayTwoReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <FrameFinder />
      <MyDayThreeReel />
      <MyDayTwoReel />
    </>
  );
};
