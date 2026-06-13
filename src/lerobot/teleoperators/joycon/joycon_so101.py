#!/usr/bin/env python

# Copyright 2026 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from lerobot.model.SO101Robot import SO101Kinematics
from lerobot.types import RobotAction
from lerobot.utils.decorators import check_if_not_connected

from ..teleoperator import Teleoperator
from .configuration_joycon import JoyConSO101Config

logger = logging.getLogger(__name__)

# Motor order of an SO-100/SO-101 follower arm.
SO101_MOTORS = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)


def _make_fixed_axes_joycon(config: JoyConSO101Config):
    """Build a JoyconRobotics instance with a decoupled, full-speed control layout.

    Imported lazily because ``joyconrobotics`` is an optional, hardware-only dependency.
    ``common_update`` is overridden so that:
      * the vertical stick drives X (reach) directly at full speed, decoupled from wrist
        pitch (the example-7 ``cos(pitch)*0.6`` projection throttled forward reach and made
        the arm "only reach halfway" / crawl back, so it is intentionally dropped),
      * the horizontal stick drives Y (pan),
      * R / stick-button drive Z up/down,
      * the accumulated position is NOT clamped, so reaching far forward is unrestricted
        (the SO101 IK naturally saturates at full arm extension),
      * Home resets to the rest pose,
      * ZR is hold-to-open/close, a fresh press toggling direction (direction starts at -1 so
        the first press opens from the closed rest state).
    Wrist pitch/roll are still applied independently in ``get_action`` by tilting the Joy-Con.

    The thread started in the base ``__init__`` may call ``common_update`` before our own
    ``__init__`` body runs, so all tuning attributes are also defined at class scope.
    """
    from joyconrobotics import JoyconRobotics
    from joyconrobotics.device import get_L_ids, get_R_ids

    side = config.side

    # Fail fast with a clear message: the underlying library crashes with an opaque
    # `'NoneType' object is not subscriptable` when no matching Joy-Con is on the HID bus.
    found = get_R_ids() if side == "right" else get_L_ids()
    if not found:
        raise ConnectionError(
            f"No {side} Joy-Con detected over Bluetooth/HID. "
            "Pair it in your system Bluetooth settings and press a button to wake it, "
            "then retry. (Tip: the Joy-Con sleeps after a while and drops off the HID bus.)"
        )

    class FixedAxesJoyconRobotics(JoyconRobotics):
        # Class-scope defaults guard against the background thread calling common_update
        # before __init__ finishes setting these up.
        joycon_stick_v_0 = 1900
        joycon_stick_h_0 = 2100
        gripper_speed = config.gripper_speed
        gripper_min = config.gripper_min
        gripper_max = config.gripper_max
        # +1 opening, -1 closing. Start at -1 so the FIRST ZR press flips to +1 and opens from
        # the closed rest state (gripper_state == gripper_min); otherwise the first press tries
        # to close past the lower bound and appears to do nothing.
        gripper_direction = -1
        last_gripper_button_state = 0
        speed_scale = config.speed_scale

        def __init__(self, device, **kwargs):
            super().__init__(device, **kwargs)
            # Per-side stick rest centers (left/right read differently at rest).
            if self.joycon.is_right():
                self.joycon_stick_v_0 = 1900
                self.joycon_stick_h_0 = 2100
            else:
                self.joycon_stick_v_0 = 2300
                self.joycon_stick_h_0 = 2000

        def common_update(self):
            speed_scale = self.speed_scale
            is_right = self.joycon.is_right()

            # Vertical stick -> X (reach), decoupled from wrist pitch. We deliberately do NOT
            # project by pitch (the example-7 ``cos(pitch)*0.6`` mapping throttled forward reach
            # to ~60% and bled it into Z, so the arm "only reached halfway" and crawled back).
            # Full, symmetric speed straight into X; pitch/roll still drive the wrist via get_action.
            stick_v = (
                self.joycon.get_stick_right_vertical()
                if is_right
                else self.joycon.get_stick_left_vertical()
            )
            v_threshold, v_range = 300, 1000
            if abs(stick_v - self.joycon_stick_v_0) > v_threshold:
                self.position[0] += (
                    speed_scale
                    * (stick_v - self.joycon_stick_v_0)
                    / v_range
                    * self.dof_speed[0]
                    * self.direction_reverse[0]
                )

            # Horizontal stick -> Y (drives shoulder_pan downstream).
            stick_h = (
                self.joycon.get_stick_right_horizontal()
                if is_right
                else self.joycon.get_stick_left_horizontal()
            )
            h_threshold, h_range = 300, 1000
            if abs(stick_h - self.joycon_stick_h_0) > h_threshold:
                self.position[1] += (
                    speed_scale
                    * (stick_h - self.joycon_stick_h_0)
                    / h_range
                    * self.dof_speed[1]
                    * self.direction_reverse[1]
                )

            # R (or L) -> Z up; stick button -> Z down.
            button_up = self.joycon.get_button_r() if is_right else self.joycon.get_button_l()
            if button_up == 1:
                self.position[2] += speed_scale * self.dof_speed[2] * self.direction_reverse[2]
            button_down = (
                self.joycon.get_button_r_stick() if is_right else self.joycon.get_button_l_stick()
            )
            if button_down == 1:
                self.position[2] -= speed_scale * self.dof_speed[2] * self.direction_reverse[2]

            # Home (or Capture) -> reset to rest pose.
            button_home = self.joycon.get_button_home() if is_right else self.joycon.get_button_capture()
            if button_home == 1:
                self.position = self.offset_position_m.copy()

            # Episode buttons (read for completeness; recording flow is driven by the keyboard).
            for event_type, status in self.button.events():
                if (is_right and event_type == "plus" and status == 1) or (
                    not is_right and event_type == "minus" and status == 1
                ):
                    self.reset_button = 1
                    self.reset_joycon()
                elif is_right and event_type == "a":
                    self.next_episode_button = status
                elif is_right and event_type == "y":
                    self.restart_episode_button = status
                else:
                    self.reset_button = 0

            # Gripper: hold ZR/ZL to move; a fresh press flips the direction.
            gripper_pressed = (
                self.joycon.get_button_zr() == 1 if is_right else self.joycon.get_button_zl() == 1
            )
            if gripper_pressed and self.last_gripper_button_state == 0:
                self.gripper_direction *= -1
            self.last_gripper_button_state = 1 if gripper_pressed else 0
            if gripper_pressed:
                new_state = self.gripper_state + self.gripper_direction * self.gripper_speed
                if self.gripper_min <= new_state <= self.gripper_max:
                    self.gripper_state = new_state

            if is_right:
                if self.next_episode_button == 1:
                    self.button_control = 1
                elif self.restart_episode_button == 1:
                    self.button_control = -1
                elif self.reset_button == 1:
                    self.button_control = 8
                else:
                    self.button_control = 0

            return self.position, self.gripper_state, self.button_control

    return FixedAxesJoyconRobotics(
        side,
        dof_speed=list(config.dof_speed),
        gripper_state=config.gripper_min,
        gripper_open=config.gripper_max,
        gripper_close=config.gripper_min,
    )


class JoyConSO101(Teleoperator):
    """Joy-Con end-effector teleoperator producing absolute SO-101 joint goal positions.

    ``get_action`` returns a ``{motor}.pos`` dict in the same convention as the SO leader
    arm, so it is a drop-in teleop for ``lerobot-record`` with an SO-100/SO-101 follower.
    """

    config_class = JoyConSO101Config
    name = "joycon_so101"

    def __init__(self, config: JoyConSO101Config):
        super().__init__(config)
        self.config = config
        self._joycon = None
        self._kinematics = SO101Kinematics()

    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in SO101_MOTORS}

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self._joycon is not None

    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            raise RuntimeError(f"{self} already connected")
        self._joycon = _make_fixed_axes_joycon(self.config)
        logger.info(f"{self} connected ({self.config.side} Joy-Con).")

    @property
    def is_calibrated(self) -> bool:
        return True

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    @check_if_not_connected
    def get_action(self) -> RobotAction:
        pose, gripper_state, _button = self._joycon.get_control()
        x, y, z, roll_rad, pitch_rad, _yaw = pose

        # End-effector target in the arm's vertical plane.
        current_x = self.config.x_offset + x
        current_y = self.config.y_offset + z

        pitch = -pitch_rad * self.config.pitch_scale + self.config.pitch_bias
        roll = roll_rad * self.config.roll_scale
        shoulder_pan = y * self.config.pan_scale

        shoulder_lift, elbow_flex = self._kinematics.inverse_kinematics(current_x, current_y)
        wrist_flex = -shoulder_lift - elbow_flex + pitch

        return {
            "shoulder_pan.pos": shoulder_pan,
            "shoulder_lift.pos": shoulder_lift,
            "elbow_flex.pos": elbow_flex,
            "wrist_flex.pos": wrist_flex,
            "wrist_roll.pos": roll,
            "gripper.pos": float(gripper_state),
        }

    def send_feedback(self, feedback: dict[str, float]) -> None:
        raise NotImplementedError

    def disconnect(self) -> None:
        if self._joycon is not None:
            try:
                self._joycon.disconnect()
            except Exception:  # nosec B110
                pass
            self._joycon = None
        logger.info(f"{self} disconnected.")
