import asyncio
import sys
import os
import time

import numpy as np  # type: ignore[import]
from ipc import core, messages, pubsub, registry
from node import base_node

# Min and max positions we can show the robot in
MAP_BOUNDS = (-10, 10)


class PotreroView(base_node.BaseNode):
    def __init__(self) -> None:
        super().__init__(registry.NodeIDs.POTRERO_VIEW)
        self._viz_welcome()
        self.add_subscribers({registry.TopicSpecs.ODOMETRY: self.rcv_odometry})

    @staticmethod
    def _viz_welcome() -> None:
        print("# Welcome to the next-gen Built Robotics UI.")
        print("# Here is a 2D map of your robot in the world.")

    async def rcv_odometry(self, msg: messages.Odometry) -> None:
        self._viz_map(msg.position, msg.heading, msg.obsticles)

    def _viz_map(self, position: list, heading: float, obsticles: list) -> None:
        os.system("clear")
        self._viz_welcome()

        for j in range(MAP_BOUNDS[0], MAP_BOUNDS[1] + 1, 1):
            line_str = "   |"

            for i in range(MAP_BOUNDS[0], MAP_BOUNDS[1] + 1, 1):
                if i == int(np.floor(position[0])) and j == int(np.floor(position[1])):
                    line_str += self._viz_heading_char(heading)
                elif [i, j] in obsticles:
                    line_str += "X"
                else:
                    line_str += "-"
            line_str += "|   "

            print(line_str)
        print("[(position)  ,  Heading ]")
        print(f"[({position[0]},{position[1]}) , {heading}]    ")

    @staticmethod
    def _viz_heading_char(heading: float):
        # assumes heading is sanatized between 0 - 359 degrees in 90 degree incriments

        heading_char = "^"
        if heading == 90:
            heading_char = ">"
        elif heading == 180:
            heading_char = "v"
        elif heading == 270:
            heading_char = "<"

        return heading_char


if __name__ == "__main__":
    node = PotreroView()
    node.run()
