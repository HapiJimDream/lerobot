#!/usr/bin/env python3
"""
SO100/SO101 YOLO end-effector following with a control-first realtime loop.

The original example runs camera capture, YOLO inference, display drawing, and
robot control in one loop. This version keeps robot control on the main thread
and moves YOLO detection into a background thread that only publishes the latest
target offset. Old detections are overwritten instead of replayed.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Any

try:
    import cv2
except ModuleNotFoundError:
    cv2 = None


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


JOINT_CALIBRATION = [
    ["shoulder_pan", 6.0, 1.0],
    ["shoulder_lift", 2.0, 0.97],
    ["elbow_flex", 0.0, 1.05],
    ["wrist_flex", 0.0, 0.94],
    ["wrist_roll", 0.0, 0.5],
    ["gripper", 0.0, 1.0],
]

ZERO_POSITIONS = {
    "shoulder_pan": 0.0,
    "shoulder_lift": 0.0,
    "elbow_flex": 0.0,
    "wrist_flex": 0.0,
    "wrist_roll": 0.0,
    "gripper": 0.0,
}

K_PAN = -0.006
K_Y = 0.00004

JOINT_LIMITS = {
    "shoulder_pan": (-95.0, 95.0),
    "shoulder_lift": (-95.0, 95.0),
    "elbow_flex": (-95.0, 95.0),
    "wrist_flex": (-120.0, 120.0),
    "wrist_roll": (-180.0, 180.0),
    "gripper": (0.0, 100.0),
}


@dataclass(frozen=True)
class DetectionSnapshot:
    found: bool
    timestamp: float
    frame_timestamp: float
    dx: float = 0.0
    dy: float = 0.0
    label: str = ""
    bbox: tuple[int, int, int, int] | None = None
    frame: Any | None = None
    inference_ms: float = 0.0
    vision_fps: float = 0.0


class LatestVisionState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot = DetectionSnapshot(found=False, timestamp=0.0, frame_timestamp=0.0)

    def update(self, snapshot: DetectionSnapshot) -> None:
        with self._lock:
            self._snapshot = snapshot

    def read(self) -> DetectionSnapshot:
        with self._lock:
            return self._snapshot


class DryRunRobot:
    def __init__(self) -> None:
        self.positions = dict(ZERO_POSITIONS)
        self.is_connected = False

    def connect(self) -> None:
        self.is_connected = True
        print("Dry-run robot connected")

    def disconnect(self) -> None:
        self.is_connected = False
        print("Dry-run robot disconnected")

    def calibrate(self) -> None:
        print("Dry-run calibration skipped")

    def get_observation(self) -> dict[str, float]:
        return {f"{joint}.pos": pos for joint, pos in self.positions.items()}

    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        for key, value in action.items():
            if key.endswith(".pos"):
                self.positions[key.removesuffix(".pos")] = value
        return action


class DryRunKeyboard:
    def connect(self) -> None:
        print("Dry-run keyboard connected")

    def disconnect(self) -> None:
        print("Dry-run keyboard disconnected")

    def get_action(self) -> dict[str, Any]:
        return {}


def apply_joint_calibration(joint_name: str, raw_position: float) -> float:
    for joint_name_cal, offset, scale in JOINT_CALIBRATION:
        if joint_name_cal == joint_name:
            return (raw_position - offset) * scale
    return raw_position


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clamp_joint(joint_name: str, value: float) -> float:
    low, high = JOINT_LIMITS.get(joint_name, (-180.0, 180.0))
    return clamp(value, low, high)


def inverse_kinematics(x: float, y: float, l1: float = 0.1159, l2: float = 0.1350) -> tuple[float, float]:
    theta1_offset = math.atan2(0.028, 0.11257)
    theta2_offset = math.atan2(0.0052, 0.1349) + theta1_offset

    r = math.sqrt(x**2 + y**2)
    r_max = l1 + l2
    if r > r_max:
        scale_factor = r_max / r
        x *= scale_factor
        y *= scale_factor
        r = r_max

    r_min = abs(l1 - l2)
    if 0 < r < r_min:
        scale_factor = r_min / r
        x *= scale_factor
        y *= scale_factor
        r = r_min

    cos_theta2 = -(r**2 - l1**2 - l2**2) / (2 * l1 * l2)
    cos_theta2 = clamp(cos_theta2, -1.0, 1.0)
    theta2 = math.pi - math.acos(cos_theta2)

    beta = math.atan2(y, x)
    gamma = math.atan2(l2 * math.sin(theta2), l1 + l2 * math.cos(theta2))
    theta1 = beta + gamma

    joint2 = clamp(theta1 + theta1_offset, -0.1, 3.45)
    joint3 = clamp(theta2 + theta2_offset, -0.2, math.pi)

    joint2_deg = 90 - math.degrees(joint2)
    joint3_deg = math.degrees(joint3) - 90
    return joint2_deg, joint3_deg


def extract_positions(obs: dict[str, Any], calibrated: bool) -> dict[str, float]:
    positions = {}
    for key, value in obs.items():
        if key.endswith(".pos"):
            motor_name = key.removesuffix(".pos")
            value = float(value)
            positions[motor_name] = apply_joint_calibration(motor_name, value) if calibrated else value
    return positions


def move_to_zero_position(robot: Any, duration: float = 3.0, kp: float = 0.5, control_freq: float = 50.0) -> None:
    print("Using P control to slowly move robot to zero position...")
    total_steps = int(duration * control_freq)
    control_period = 1.0 / control_freq

    for step in range(total_steps):
        current_positions = extract_positions(robot.get_observation(), calibrated=True)
        robot_action = {}
        for joint_name, target_pos in ZERO_POSITIONS.items():
            if joint_name in current_positions:
                current_pos = current_positions[joint_name]
                new_position = current_pos + kp * (target_pos - current_pos)
                robot_action[f"{joint_name}.pos"] = clamp_joint(joint_name, new_position)

        if robot_action:
            robot.send_action(robot_action)

        if step % max(1, int(control_freq // 2)) == 0:
            print(f"Moving to zero position progress: {(step / total_steps) * 100:.1f}%")
        time.sleep(control_period)

    print("Robot has moved to zero position")


def return_to_start_position(
    robot: Any, start_positions: dict[str, float], kp: float = 0.5, control_freq: float = 50.0
) -> None:
    print("Returning to start position...")
    control_period = 1.0 / control_freq
    max_steps = int(5.0 * control_freq)

    for _ in range(max_steps):
        current_positions = extract_positions(robot.get_observation(), calibrated=False)
        robot_action = {}
        total_error = 0.0

        for joint_name, target_pos in start_positions.items():
            if joint_name in current_positions:
                current_pos = current_positions[joint_name]
                error = target_pos - current_pos
                total_error += abs(error)
                new_position = current_pos + kp * error
                robot_action[f"{joint_name}.pos"] = clamp_joint(joint_name, new_position)

        if robot_action:
            robot.send_action(robot_action)

        if total_error < 2.0:
            print("Returned to start position")
            break

        time.sleep(control_period)

    print("Return to start position completed")


def list_cameras(max_index: int = 5) -> list[int]:
    require_cv2()
    available = []
    for idx in range(max_index):
        cap_test = cv2.VideoCapture(idx)
        if cap_test.isOpened():
            available.append(idx)
            cap_test.release()
    return available


def parse_targets(targets: str) -> list[str]:
    parsed = [target.strip() for target in targets.split(",") if target.strip()]
    return parsed or ["mouse"]


def resolve_target_objects(targets_arg: str) -> set[str]:
    print("\n" + "=" * 60)
    print("YOLO Detection Target Setup")
    print("=" * 60)

    if targets_arg:
        target_objects = parse_targets(targets_arg)
        print(f"Detection targets: {target_objects}")
        return set(target_objects)

    target_input = input("Enter objects to detect (separate multiple objects with commas, e.g., bottle,cup,mouse): ").strip()
    target_objects = parse_targets(target_input)
    if target_input:
        print(f"Detection targets: {target_objects}")
    else:
        print(f"Using default targets: {target_objects}")
    return set(target_objects)


def configure_camera(cap: cv2.VideoCapture, width: int, height: int, buffer_size: int) -> None:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)


def run_yolo_detection_thread(
    model: Any,
    cap: cv2.VideoCapture,
    target_objects: set[str],
    state: LatestVisionState,
    stop_event: threading.Event,
    imgsz: int,
    conf: float,
    max_vision_fps: float,
    keep_frame: bool,
) -> None:
    print(f"Vision thread started, targets: {sorted(target_objects)}")
    min_period = 1.0 / max_vision_fps if max_vision_fps > 0 else 0.0
    last_start = 0.0
    fps_ema = 0.0

    while not stop_event.is_set():
        loop_start = time.monotonic()
        elapsed = loop_start - last_start
        if elapsed < min_period:
            stop_event.wait(min_period - elapsed)
            continue
        last_start = time.monotonic()

        ret, frame = cap.read()
        frame_timestamp = time.monotonic()
        if not ret:
            stop_event.wait(0.01)
            continue

        inference_start = time.perf_counter()
        try:
            results = model.predict(frame, imgsz=imgsz, conf=conf, verbose=False)
        except Exception as exc:
            logger.warning("YOLO inference failed: %s", exc)
            stop_event.wait(0.1)
            continue
        inference_ms = (time.perf_counter() - inference_start) * 1e3

        now = time.monotonic()
        sample_dt = now - loop_start
        if sample_dt > 0:
            sample_fps = 1.0 / sample_dt
            fps_ema = sample_fps if fps_ema == 0 else 0.9 * fps_ema + 0.1 * sample_fps

        snapshot = build_detection_snapshot(
            results=results,
            frame=frame,
            target_objects=target_objects,
            timestamp=now,
            frame_timestamp=frame_timestamp,
            inference_ms=inference_ms,
            vision_fps=fps_ema,
            keep_frame=keep_frame,
        )
        state.update(snapshot)

    print("Vision thread stopped")


def build_detection_snapshot(
    results: Any,
    frame: Any,
    target_objects: set[str],
    timestamp: float,
    frame_timestamp: float,
    inference_ms: float,
    vision_fps: float,
    keep_frame: bool,
) -> DetectionSnapshot:
    h, w = frame.shape[:2]
    frame_for_display = frame.copy() if keep_frame else None

    if results and hasattr(results[0], "boxes") and results[0].boxes:
        for box in results[0].boxes:
            cls = int(box.cls[0])
            label = results[0].names[cls]
            if label not in target_objects:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            return DetectionSnapshot(
                found=True,
                timestamp=timestamp,
                frame_timestamp=frame_timestamp,
                dx=float(cx - w // 2),
                dy=float(cy - h // 2),
                label=label,
                bbox=(x1, y1, x2, y2),
                frame=frame_for_display,
                inference_ms=inference_ms,
                vision_fps=vision_fps,
            )

    return DetectionSnapshot(
        found=False,
        timestamp=timestamp,
        frame_timestamp=frame_timestamp,
        frame=frame_for_display,
        inference_ms=inference_ms,
        vision_fps=vision_fps,
    )


def apply_detection_to_targets(
    detection: DetectionSnapshot,
    target_positions: dict[str, float],
    current_x: float,
    current_y: float,
    args: argparse.Namespace,
    filtered_dx: float | None,
    filtered_dy: float | None,
) -> tuple[float, float, float | None, float | None, bool]:
    if not detection.found:
        return current_x, current_y, filtered_dx, filtered_dy, False

    now = time.monotonic()
    if now - detection.timestamp > args.vision_timeout:
        return current_x, current_y, filtered_dx, filtered_dy, False

    dx = detection.dx
    dy = detection.dy
    alpha = args.vision_filter_alpha
    filtered_dx = dx if filtered_dx is None else alpha * dx + (1.0 - alpha) * filtered_dx
    filtered_dy = dy if filtered_dy is None else alpha * dy + (1.0 - alpha) * filtered_dy

    pan_delta = -K_PAN * filtered_dx
    if abs(filtered_dx) < args.deadband_px:
        pan_delta = 0.0
    pan_delta = clamp(pan_delta, -args.max_pan_step_deg, args.max_pan_step_deg)

    y_delta = -K_Y * filtered_dy
    if abs(filtered_dy) < args.deadband_px:
        y_delta = 0.0
    y_delta = clamp(y_delta, -args.max_y_step_m, args.max_y_step_m)

    target_positions["shoulder_pan"] = clamp_joint("shoulder_pan", target_positions["shoulder_pan"] + pan_delta)
    current_y = clamp(current_y + y_delta, args.min_ee_y, args.max_ee_y)
    joint2_target, joint3_target = inverse_kinematics(current_x, current_y)
    target_positions["shoulder_lift"] = clamp_joint("shoulder_lift", joint2_target)
    target_positions["elbow_flex"] = clamp_joint("elbow_flex", joint3_target)

    return current_x, current_y, filtered_dx, filtered_dy, True


def process_keyboard_action(
    keyboard_action: dict[str, Any],
    robot: Any,
    target_positions: dict[str, float],
    start_positions: dict[str, float],
    current_x: float,
    current_y: float,
    pitch: float,
    control_freq: float,
) -> tuple[float, float, float, bool]:
    joint_controls = {
        "q": ("shoulder_pan", -1.0),
        "a": ("shoulder_pan", 1.0),
        "t": ("wrist_roll", -1.0),
        "g": ("wrist_roll", 1.0),
        "y": ("gripper", -1.0),
        "h": ("gripper", 1.0),
    }
    xy_controls = {
        "w": ("x", -0.004),
        "s": ("x", 0.004),
        "e": ("y", -0.004),
        "d": ("y", 0.004),
    }

    for key in keyboard_action:
        if key == "x":
            print("Exit command detected, returning to start position...")
            return_to_start_position(robot, start_positions, 0.2, control_freq)
            return current_x, current_y, pitch, True

        if key == "r":
            pitch += 1.0
            print(f"Increase pitch adjustment: {pitch:.3f}")
        elif key == "f":
            pitch -= 1.0
            print(f"Decrease pitch adjustment: {pitch:.3f}")

        if key in joint_controls:
            joint_name, delta = joint_controls[key]
            current_target = target_positions[joint_name]
            target_positions[joint_name] = clamp_joint(joint_name, current_target + delta)
            print(f"Update target position {joint_name}: {current_target:.3f} -> {target_positions[joint_name]:.3f}")
        elif key in xy_controls:
            coord, delta = xy_controls[key]
            if coord == "x":
                current_x += delta
            else:
                current_y += delta
            joint2_target, joint3_target = inverse_kinematics(current_x, current_y)
            target_positions["shoulder_lift"] = clamp_joint("shoulder_lift", joint2_target)
            target_positions["elbow_flex"] = clamp_joint("elbow_flex", joint3_target)
            print(
                f"Update {coord} coordinate: x={current_x:.4f}, y={current_y:.4f}, "
                f"joint2={joint2_target:.3f}, joint3={joint3_target:.3f}"
            )

    return current_x, current_y, pitch, False


def draw_detection_window(detection: DetectionSnapshot, window_name: str = "YOLO realtime tracking") -> bool:
    if cv2 is None:
        return False

    frame = detection.frame
    if frame is None:
        return False

    h, w = frame.shape[:2]
    cv2.drawMarker(frame, (w // 2, h // 2), (255, 255, 255), cv2.MARKER_CROSS, 20, 1)

    if detection.found and detection.bbox is not None:
        x1, y1, x2, y2 = detection.bbox
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
        cv2.putText(frame, detection.label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(
        frame,
        f"YOLO {detection.vision_fps:.1f} fps  infer {detection.inference_ms:.1f} ms",
        (10, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )
    cv2.imshow(window_name, frame)
    key = cv2.waitKey(1) & 0xFF
    return key in (ord("q"), 27)


def realtime_control_loop(
    robot: Any,
    keyboard: Any,
    start_positions: dict[str, float],
    vision_state: LatestVisionState,
    stop_event: threading.Event,
    args: argparse.Namespace,
) -> None:
    control_period = 1.0 / args.control_freq
    target_positions = dict(ZERO_POSITIONS)
    current_x, current_y = args.initial_x, args.initial_y
    pitch = 0.0
    filtered_dx: float | None = None
    filtered_dy: float | None = None
    last_stats_time = time.monotonic()
    start_time = time.monotonic()
    loop_count = 0
    max_loop_ms = 0.0

    print(f"Starting realtime control loop at {args.control_freq:.1f}Hz")
    print(f"Initial end effector position: x={current_x:.4f}, y={current_y:.4f}")

    next_tick = time.monotonic()
    while not stop_event.is_set():
        loop_start = time.monotonic()
        if args.max_runtime is not None and loop_start - start_time >= args.max_runtime:
            print(f"Max runtime reached: {args.max_runtime:.1f}s")
            stop_event.set()
            break

        detection = vision_state.read()
        current_x, current_y, filtered_dx, filtered_dy, used_detection = apply_detection_to_targets(
            detection, target_positions, current_x, current_y, args, filtered_dx, filtered_dy
        )

        if args.show and detection.frame is not None:
            if draw_detection_window(detection):
                print("Video window exit requested")
                stop_event.set()
                break

        keyboard_action = keyboard.get_action()
        if keyboard_action:
            current_x, current_y, pitch, should_exit = process_keyboard_action(
                keyboard_action, robot, target_positions, start_positions, current_x, current_y, pitch, args.control_freq
            )
            if should_exit:
                stop_event.set()
                break

        target_positions["wrist_flex"] = clamp_joint(
            "wrist_flex", -target_positions["shoulder_lift"] - target_positions["elbow_flex"] + pitch
        )

        current_positions = extract_positions(robot.get_observation(), calibrated=True)
        robot_action = {}
        for joint_name, target_pos in target_positions.items():
            if joint_name in current_positions:
                current_pos = current_positions[joint_name]
                new_position = current_pos + args.kp * (target_pos - current_pos)
                robot_action[f"{joint_name}.pos"] = clamp_joint(joint_name, new_position)

        if robot_action:
            robot.send_action(robot_action)

        loop_count += 1
        loop_ms = (time.monotonic() - loop_start) * 1e3
        max_loop_ms = max(max_loop_ms, loop_ms)
        now = time.monotonic()
        if now - last_stats_time >= args.stats_interval:
            control_fps = loop_count / (now - last_stats_time)
            vision_age = now - detection.timestamp if detection.timestamp else float("inf")
            tracking = "tracking" if used_detection else "holding"
            print(
                f"control={control_fps:.1f}Hz max_loop={max_loop_ms:.1f}ms "
                f"vision={detection.vision_fps:.1f}Hz age={vision_age:.2f}s {tracking}"
            )
            loop_count = 0
            max_loop_ms = 0.0
            last_stats_time = now

        next_tick += control_period
        sleep_for = next_tick - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)
        else:
            next_tick = time.monotonic()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SO100 YOLO realtime end-effector following")
    parser.add_argument("--port", default="", help="SO100 USB port. If omitted, prompts; empty prompt uses /dev/ttyACM0.")
    parser.add_argument("--camera", type=int, default=None, help="Camera index. If omitted, prompts from detected cameras.")
    parser.add_argument(
        "--targets",
        default="",
        help="Comma-separated YOLO labels to track. If omitted, prompts interactively like the original example.",
    )
    parser.add_argument("--model", default="yolo11s.pt", help="YOLO model path/name, e.g. yolo11n.pt, yolo11s.pt, yolo11x.pt.")
    parser.add_argument("--imgsz", type=int, default=320, help="YOLO inference image size.")
    parser.add_argument("--conf", type=float, default=0.35, help="YOLO confidence threshold.")
    parser.add_argument("--vision-fps", type=float, default=15.0, help="Maximum YOLO detection FPS.")
    parser.add_argument("--control-freq", type=float, default=50.0, help="Robot control frequency.")
    parser.add_argument("--kp", type=float, default=0.5, help="P control gain.")
    parser.add_argument("--camera-width", type=int, default=640)
    parser.add_argument("--camera-height", type=int, default=480)
    parser.add_argument("--camera-buffer", type=int, default=1)
    parser.add_argument("--deadband-px", type=float, default=12.0)
    parser.add_argument("--max-pan-step-deg", type=float, default=2.0)
    parser.add_argument("--max-y-step-m", type=float, default=0.005)
    parser.add_argument("--vision-timeout", type=float, default=0.3)
    parser.add_argument("--vision-filter-alpha", type=float, default=0.35)
    parser.add_argument("--initial-x", type=float, default=0.1629)
    parser.add_argument("--initial-y", type=float, default=0.1131)
    parser.add_argument("--min-ee-y", type=float, default=0.02)
    parser.add_argument("--max-ee-y", type=float, default=0.22)
    parser.add_argument("--stats-interval", type=float, default=1.0)
    parser.add_argument("--show", action=argparse.BooleanOptionalAction, default=True, help="Show camera tracking window.")
    parser.add_argument("--dry-run", action="store_true", help="Use mock robot and keyboard; still uses camera/YOLO unless --no-vision.")
    parser.add_argument("--no-vision", action="store_true", help="Disable camera and YOLO thread.")
    parser.add_argument("--camera-only", action="store_true", help="Open the camera and exit; useful for macOS permission prompts.")
    parser.add_argument("--skip-zero", action="store_true", help="Do not move to zero position before starting.")
    parser.add_argument("--max-runtime", type=float, default=None, help="Exit automatically after N seconds; useful for smoke tests.")
    return parser


def make_robot_and_keyboard(args: argparse.Namespace) -> tuple[Any, Any]:
    if args.dry_run:
        return DryRunRobot(), DryRunKeyboard()

    from lerobot.robots.so_follower.config_so_follower import SO100FollowerConfig
    from lerobot.robots.so_follower.so_follower import SO100Follower
    from lerobot.teleoperators.keyboard.configuration_keyboard import KeyboardTeleopConfig
    from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop

    port = args.port
    if not port:
        port = input("Please enter SO100 robot USB port (e.g.: /dev/ttyACM0): ").strip() or "/dev/ttyACM0"
    print(f"Connecting to port: {port}")

    robot_config = SO100FollowerConfig(port=port, max_relative_target=None)
    robot = SO100Follower(robot_config)
    keyboard = KeyboardTeleop(KeyboardTeleopConfig())
    return robot, keyboard


def make_camera(args: argparse.Namespace) -> cv2.VideoCapture:
    require_cv2()
    camera_index = args.camera
    if camera_index is None:
        cameras = list_cameras()
        if not cameras:
            raise RuntimeError("No cameras found")
        print(f"Available cameras: {cameras}")
        camera_index = int(input(f"Select camera index from {cameras}: "))

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Camera {camera_index} could not be opened")
    configure_camera(cap, args.camera_width, args.camera_height, args.camera_buffer)
    return cap


def require_cv2() -> None:
    if cv2 is None:
        raise RuntimeError("OpenCV is required for camera/vision mode. Install cv2 or run with --no-vision --no-show.")


def main() -> None:
    args = build_arg_parser().parse_args()
    target_objects = resolve_target_objects(args.targets)
    stop_event = threading.Event()
    vision_state = LatestVisionState()
    robot = None
    keyboard = None
    cap = None
    vision_thread = None

    try:
        robot, keyboard = make_robot_and_keyboard(args)
        robot.connect()
        keyboard.connect()
        print("Devices connected successfully")

        if not args.dry_run:
            calibrate_choice = input("Do you want to recalibrate the robot? (y/n): ").strip().lower()
            if calibrate_choice in ["y", "yes"]:
                robot.calibrate()

        start_positions = extract_positions(robot.get_observation(), calibrated=False)
        print("Starting joint angles:")
        for joint_name, position in start_positions.items():
            print(f"  {joint_name}: {position:.1f} deg")

        if not args.skip_zero:
            move_to_zero_position(robot, duration=3.0, kp=args.kp, control_freq=args.control_freq)

        if not args.no_vision:
            cap = make_camera(args)
            if args.camera_only:
                ret, _ = cap.read()
                print(f"Camera probe {'succeeded' if ret else 'failed'}")
                stop_event.set()
                return

            from ultralytics import YOLO

            model = YOLO(args.model)
            vision_thread = threading.Thread(
                target=run_yolo_detection_thread,
                args=(
                    model,
                    cap,
                    target_objects,
                    vision_state,
                    stop_event,
                    args.imgsz,
                    args.conf,
                    args.vision_fps,
                    args.show,
                ),
                daemon=True,
            )
            vision_thread.start()
        else:
            print("Vision disabled; keyboard/manual control only")

        print("Control instructions:")
        print("- Q/A: shoulder_pan decrease/increase")
        print("- W/S: end effector x decrease/increase")
        print("- E/D: end effector y decrease/increase")
        print("- R/F: pitch adjustment increase/decrease")
        print("- T/G: wrist_roll decrease/increase")
        print("- Y/H: gripper close/open")
        print("- X: return to start position and exit")
        print("- Q or ESC in video window: exit")

        realtime_control_loop(robot, keyboard, start_positions, vision_state, stop_event, args)

    except KeyboardInterrupt:
        print("User interrupted program")
        stop_event.set()
    except Exception as exc:
        print(f"Program execution failed: {exc}")
        traceback.print_exc()
    finally:
        stop_event.set()
        if vision_thread is not None:
            vision_thread.join(timeout=1.0)
        if cap is not None:
            cap.release()
        if cv2 is not None:
            cv2.destroyAllWindows()
        if keyboard is not None:
            try:
                keyboard.disconnect()
            except Exception as exc:
                logger.warning("Keyboard disconnect failed: %s", exc)
        if robot is not None:
            try:
                robot.disconnect()
            except Exception as exc:
                logger.warning("Robot disconnect failed: %s", exc)
        print("Program ended")


if __name__ == "__main__":
    main()
