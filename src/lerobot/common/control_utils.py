# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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

from __future__ import annotations

########################################################################################
# Utilities
########################################################################################
import logging
import os
import select
import sys
import threading
from contextlib import nullcontext
from copy import copy
from functools import cache
from typing import TYPE_CHECKING, Any

try:
    import termios
    import tty
except ImportError:  # Non-Unix platforms (e.g. Windows) — stdin key control unavailable.
    termios = None
    tty = None

import numpy as np
import torch

from lerobot.policies import PreTrainedPolicy, prepare_observation_for_inference
from lerobot.utils.import_utils import _deepdiff_available, require_package

if TYPE_CHECKING or _deepdiff_available:
    from deepdiff import DeepDiff
else:
    DeepDiff = None

if TYPE_CHECKING:
    from lerobot.datasets import LeRobotDataset
from lerobot.processor import PolicyProcessorPipeline
from lerobot.robots import Robot
from lerobot.types import PolicyAction


@cache
def is_headless():
    """
    Detects if the Python script is running in a headless environment (e.g., without a display).

    This function attempts to import `pynput`, a library that requires a graphical environment.
    If the import fails, it assumes the environment is headless. The result is cached to avoid
    re-running the check.

    Returns:
        True if the environment is determined to be headless, False otherwise.
    """
    try:
        import pynput  # noqa

        return False
    except Exception as e:
        # Expected on a bare TTY or SSH session (no X server). The caller falls back
        # to the terminal-based key listener, so this is a normal degradation, not an
        # error — keep it to a single debug line instead of a scary traceback.
        logging.debug(f"pynput unavailable, switching to headless mode: {e}")
        return True


def predict_action(
    observation: dict[str, np.ndarray],
    policy: PreTrainedPolicy,
    device: torch.device,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]],
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction],
    use_amp: bool,
    task: str | None = None,
    robot_type: str | None = None,
):
    """
    Performs a single-step inference to predict a robot action from an observation.

    This function encapsulates the full inference pipeline:
    1. Prepares the observation by converting it to PyTorch tensors and adding a batch dimension.
    2. Runs the preprocessor pipeline on the observation.
    3. Feeds the processed observation to the policy to get a raw action.
    4. Runs the postprocessor pipeline on the raw action.
    5. Formats the final action by removing the batch dimension and moving it to the CPU.

    Args:
        observation: A dictionary of NumPy arrays representing the robot's current observation.
        policy: The `PreTrainedPolicy` model to use for action prediction.
        device: The `torch.device` (e.g., 'cuda' or 'cpu') to run inference on.
        preprocessor: The `PolicyProcessorPipeline` for preprocessing observations.
        postprocessor: The `PolicyProcessorPipeline` for postprocessing actions.
        use_amp: A boolean to enable/disable Automatic Mixed Precision for CUDA inference.
        task: An optional string identifier for the task.
        robot_type: An optional string identifier for the robot type.

    Returns:
        A `torch.Tensor` containing the predicted action, ready for the robot.
    """
    observation = copy(observation)
    with (
        torch.inference_mode(),
        torch.autocast(device_type=device.type) if device.type == "cuda" and use_amp else nullcontext(),
    ):
        # Convert to pytorch format: channel first and float32 in [0,1] with batch dimension
        observation = prepare_observation_for_inference(observation, device, task, robot_type)
        observation = preprocessor(observation)

        # Compute the next action with the policy
        # based on the current observation
        action = policy.select_action(observation)

        action = postprocessor(action)

    return action


class _StdinKeyboardListener:
    """Reads arrow keys / Esc directly from an interactive terminal (TTY).

    Fallback for headless setups (Raspberry Pi text console, SSH session) where
    ``pynput`` cannot run because there is no X server. Mirrors the key bindings of
    the pynput-based listener so the recording loop behaves identically:

        Right arrow -> exit early (save current episode, go to next)
        Left arrow  -> re-record the current episode
        Esc         -> stop recording

    The terminal is switched to cbreak mode (echo + canonical input off) so the raw
    escape sequences are not printed and keys are delivered without pressing Enter.
    ``ISIG`` is left enabled, so Ctrl-C still aborts. The original terminal settings
    are always restored in :meth:`stop`.
    """

    def __init__(self, events):
        self.events = events
        self._fd = sys.stdin.fileno()
        self._old_term = termios.tcgetattr(self._fd)
        self._stop_event = threading.Event()
        tty.setcbreak(self._fd)
        self._thread = threading.Thread(
            target=self._read_loop, daemon=True, name="stdin_keyboard_listener"
        )
        self._thread.start()

    def _read_loop(self):
        while not self._stop_event.is_set():
            # Poll with a timeout so the loop can notice stop_event promptly.
            ready, _, _ = select.select([self._fd], [], [], 0.1)
            if not ready:
                continue
            ch = os.read(self._fd, 1)
            if ch != b"\x1b":  # We only act on escape sequences and bare Esc.
                continue

            # ESC may be a bare Escape or the prefix of an arrow-key sequence
            # (ESC [ C / ESC [ D). Briefly wait to disambiguate.
            ready, _, _ = select.select([self._fd], [], [], 0.05)
            if not ready:
                print("Escape key pressed. Stopping data recording...")
                self.events["stop_recording"] = True
                self.events["exit_early"] = True
                continue

            seq = os.read(self._fd, 2)
            if seq == b"[C":  # Right arrow
                print("Right arrow key pressed. Exiting loop...")
                self.events["exit_early"] = True
            elif seq == b"[D":  # Left arrow
                print("Left arrow key pressed. Exiting loop and rerecord the last episode...")
                self.events["rerecord_episode"] = True
                self.events["exit_early"] = True

    def stop(self):
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        # Restore the terminal to its original (canonical, echoing) state.
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_term)


def _init_stdin_listener(events):
    """Create a terminal-based key listener for headless/TTY setups.

    Returns a listener exposing ``.stop()``, or ``None`` if a terminal listener cannot
    be used (no termios support, or stdin is not an interactive TTY — e.g. piped input).
    """
    if termios is None or tty is None or not sys.stdin.isatty():
        return None
    try:
        return _StdinKeyboardListener(events)
    except (termios.error, OSError) as e:
        logging.warning(f"Could not initialize stdin keyboard listener: {e}")
        return None


def init_keyboard_listener():
    """
    Initializes a non-blocking keyboard listener for real-time user interaction.

    This function sets up a listener for specific keys (right arrow, left arrow, escape) to control
    the program flow during execution, such as stopping recording or exiting loops. It gracefully
    handles headless environments where keyboard listening is not possible.

    Returns:
        A tuple containing:
        - The `pynput.keyboard.Listener` instance, or `None` if in a headless environment.
        - A dictionary of event flags (e.g., `exit_early`) that are set by key presses.
    """
    # Allow to exit early while recording an episode or resetting the environment,
    # by tapping the right arrow key '->'. This might require a sudo permission
    # to allow your terminal to monitor keyboard events.
    events = {}
    events["exit_early"] = False
    events["rerecord_episode"] = False
    events["stop_recording"] = False

    if is_headless():
        # No X server (e.g. Pi text console or SSH), so pynput can't run. Fall back to
        # reading the controlling terminal directly, which works on a bare TTY and over SSH.
        listener = _init_stdin_listener(events)
        if listener is not None:
            logging.info(
                "Headless environment detected. Using terminal key control: "
                "Right arrow = next episode, Left arrow = re-record, Esc = stop."
            )
        else:
            logging.warning(
                "Headless environment detected and no interactive terminal available. "
                "On-screen cameras display and keyboard inputs will not be available."
            )
        return listener, events

    # Only import pynput if not in a headless environment
    from pynput import keyboard

    def on_press(key):
        try:
            if key == keyboard.Key.right:
                print("Right arrow key pressed. Exiting loop...")
                events["exit_early"] = True
            elif key == keyboard.Key.left:
                print("Left arrow key pressed. Exiting loop and rerecord the last episode...")
                events["rerecord_episode"] = True
                events["exit_early"] = True
            elif key == keyboard.Key.esc:
                print("Escape key pressed. Stopping data recording...")
                events["stop_recording"] = True
                events["exit_early"] = True
        except Exception as e:
            print(f"Error handling key press: {e}")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    return listener, events


def sanity_check_dataset_name(repo_id, policy_cfg):
    """
    Validates the dataset repository name against the presence of a policy configuration.

    This function enforces a naming convention: a dataset repository ID should start with "eval_"
    if and only if a policy configuration is provided for evaluation purposes.

    Args:
        repo_id: The Hugging Face Hub repository ID of the dataset.
        policy_cfg: The configuration object for the policy, or `None`.

    Raises:
        ValueError: If the naming convention is violated.
    """
    _, dataset_name = repo_id.split("/")
    # either repo_id doesnt start with "eval_" and there is no policy
    # or repo_id starts with "eval_" and there is a policy

    # Check if dataset_name starts with "eval_" but policy is missing
    if dataset_name.startswith("eval_") and policy_cfg is None:
        raise ValueError(
            f"Your dataset name begins with 'eval_' ({dataset_name}), but no policy is provided."
        )

    # Check if dataset_name does not start with "eval_" but policy is provided
    if not dataset_name.startswith("eval_") and policy_cfg is not None:
        raise ValueError(
            f"Your dataset name does not begin with 'eval_' ({dataset_name}), but a policy is provided ({policy_cfg.type})."
        )


def sanity_check_dataset_robot_compatibility(
    dataset: LeRobotDataset, robot: Robot, fps: int, features: dict
) -> None:
    """
    Checks if a dataset's metadata is compatible with the current robot and recording setup.

    This function compares key metadata fields (`robot_type`, `fps`, and `features`) from the
    dataset against the current configuration to ensure that appended data will be consistent.

    Args:
        dataset: The `LeRobotDataset` instance to check.
        robot: The `Robot` instance representing the current hardware setup.
        fps: The current recording frequency (frames per second).
        features: The dictionary of features for the current recording session.

    Raises:
        ValueError: If any of the checked metadata fields do not match.
    """
    require_package("deepdiff", extra="deepdiff-dep")

    from lerobot.utils.constants import DEFAULT_FEATURES

    fields = [
        ("robot_type", dataset.meta.robot_type, robot.robot_type),
        ("fps", dataset.fps, fps),
        ("features", dataset.features, {**features, **DEFAULT_FEATURES}),
    ]

    mismatches = []
    for field, dataset_value, present_value in fields:
        diff = DeepDiff(dataset_value, present_value, exclude_regex_paths=[r".*\['info'\]$"])
        if diff:
            mismatches.append(f"{field}: expected {present_value}, got {dataset_value}")

    if mismatches:
        raise ValueError(
            "Dataset metadata compatibility check failed with mismatches:\n" + "\n".join(mismatches)
        )
