import asyncio
import sys

import numpy as np  # type: ignore[import]
from ipc import core, messages, pubsub, registry
from node import base_node

# Min and max positions the robot can be in
WORLD_EDGES = (-10, 10)


class Simulator(base_node.BaseNode):
    def __init__(self) -> None:
        super().__init__(registry.NodeIDs.SIMULATOR)
        self._set_initial_values()
        self._heading_increment = 90

        self.add_publishers(registry.TopicSpecs.ODOMETRY)
        self.add_subscribers({registry.TopicSpecs.RC_JS_DEF: self.rcv_js})
        self.add_tasks(self._pub_odometry_loop)

    def _set_initial_values(self) -> None:
        self._position = [0, 0]
        self._heading = 90.0

        self._obsticles = self._load_obsticles()

    def _reset_simulation(self) -> None:
        print("INFO :: Simulation is resetting to initial state")
        self._set_initial_values()

    async def rcv_js(self, msg: messages.JoystickDeflection) -> None:
        if (
            msg.joystick == messages.JoystickType.TRACK_LEFT
            or msg.joystick == messages.JoystickType.TRACK_RIGHT
        ):
            self._heading = self._normalize_heading(
                self._heading + msg.deflection * self._heading_increment
            )

        elif (
            msg.joystick == messages.JoystickType.TRACK_FORWARD
            or msg.joystick == messages.JoystickType.TRACK_BACKWARD
        ):
            new_position = self._position.copy()
            new_position[0] = round(
                self._position[0] + np.sin(np.radians(self._heading)) * msg.deflection,
                1,
            )
            new_position[1] = round(
                self._position[1] - np.cos(np.radians(self._heading)) * msg.deflection,
                1,
            )

            if self._is_valid_location(new_position):
                # check obsticles
                if new_position in self._obsticles:
                    print("Warning :: Robot collided with an obstricle")
                else:
                    self._position = new_position

            else:
                # restart the simulation
                self._reset_simulation()

    async def _pub_odometry_loop(self) -> None:
        while True:
            msg = messages.Odometry(
                position=self._position,
                heading=self._heading,
                obsticles=self._obsticles,
            )
            self.publish(registry.TopicSpecs.ODOMETRY, msg)
            await asyncio.sleep(0.05)

    @staticmethod
    def _normalize_heading(heading: float) -> float:
        sign = -1 if heading >= 0 else 1
        # while loop is currrently not required but future development could have a spin exceeding 360 degrees rotation
        while heading < 0 or heading > 359:
            heading = heading + (sign * 360)
        return heading

    @staticmethod
    def _load_obsticles() -> list:
        obsticles = [[1, 2], [4, 3], [-6, 7]]
        return obsticles

    def _is_valid_location(self, position: list) -> bool:
        valid_location = True

        # check boundries
        if not (position[0] >= WORLD_EDGES[0] and position[0] <= WORLD_EDGES[1]):
            valid_location = False
            print("ERROR :: Robot attempted to travel outside boundries")

        if not (position[1] >= WORLD_EDGES[0] and position[1] <= WORLD_EDGES[1]):
            valid_location = False
            print("ERROR :: Robot attempted to travel outside boundries")

        return valid_location


if __name__ == "__main__":
    node = Simulator()
    node.run()
