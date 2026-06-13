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

from dataclasses import dataclass, field

from ..config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("joycon_so101")
@dataclass
class JoyConSO101Config(TeleoperatorConfig):
    """Nintendo Joy-Con end-effector teleoperator for a single SO-100/SO-101 follower arm.

    The Joy-Con pose is mapped to Cartesian end-effector coordinates and solved with the
    SO101 2-link inverse kinematics into absolute joint goal positions. The mapping mirrors
    the standalone ``examples/6_so100_joycon_ee_control.py`` script.
    """

    # Which Joy-Con to use: "right" or "left".
    side: str = "right"

    # End-effector base offsets (meters) added to the Joy-Con relative position.
    x_offset: float = 0.1629
    y_offset: float = 0.1131

    # Scaling from Joy-Con lateral position to the shoulder_pan joint (degrees).
    pan_scale: float = 250.0
    # Scaling from Joy-Con roll to the wrist_roll joint (degrees).
    roll_scale: float = 45.0
    # Pitch mapping: wrist pitch (degrees) = -pitch_rad * pitch_scale + pitch_bias.
    pitch_scale: float = 60.0
    pitch_bias: float = 10.0

    # --- Stick / button motion tuning ---
    # Per-frame Cartesian step gain applied from stick deflection / button hold.
    # The vertical stick is projected by wrist pitch into X (reach) and Z (height),
    # matching examples/7_xlerobot_2wheels_teleop_joycon.py (no workspace clamp).
    speed_scale: float = 0.001

    # --- Gripper: hold ZR for linear open/close (press toggles direction) ---
    gripper_speed: float = 0.4
    gripper_min: float = 0.0
    gripper_max: float = 90.0

    # Per-DOF speed multipliers passed to JoyconRobotics: [x, y, z, roll, pitch, yaw].
    dof_speed: list[float] = field(default_factory=lambda: [2, 2, 2, 1, 1, 1])
