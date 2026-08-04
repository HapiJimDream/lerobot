"""Robot-side client for a LingbotVLA websocket policy server.

The server (`websocket_policy_server.py`) is a blocking request/response endpoint: send one
observation, get back one action chunk. To keep the robot moving at a steady control rate while
inference is in flight, this client runs two threads:

  * the **control loop** (main thread) owns *all* robot I/O — it reads observations, pops actions
    off a local queue and writes them to the motors at a fixed `fps`;
  * the **inference thread** owns the websocket — it takes an observation off a hand-off slot,
    blocks on `infer()`, and merges the returned chunk back into the action queue.

When the queue drains below `chunk_size_threshold` of a full chunk, the control loop hands a fresh
observation to the inference thread. Chunks that overlap actions already queued are blended with
`aggregate_fn_name`, so a late chunk never causes a jump. This mirrors the scheduling in
`lerobot.async_inference.robot_client` without the gRPC layer.

Example (bimanual SO-101, 3 cameras):

```shell
python -m examples.lingbotvla.robot_client \
    --host=127.0.0.1 \
    --port=8000 \
    --robot.type=bi_so_follower \
    --robot.left_arm_config.port=/dev/ttyLeftArm \
    --robot.right_arm_config.port=/dev/ttyRightArm \
    --robot.id=bimanual_follower \
    --robot.left_arm_config.cameras="{
      head: {type: opencv, index_or_path: '/dev/camHead', width: 640, height: 480, fps: 30},
      left: {type: opencv, index_or_path: '/dev/camLeft', width: 640, height: 480, fps: 30}
    }" \
    --robot.right_arm_config.cameras="{
      right: {type: opencv, index_or_path: '/dev/camRight', width: 640, height: 480, fps: 30}
    }" \
    --image_keys="{
      left_head: base_0_rgb,
      left_left: left_wrist_0_rgb,
      right_right: right_wrist_0_rgb
    }" \
    --task="Place the object in the tray" \
    --actions_per_chunk=50 \
    --chunk_size_threshold=0.5 \
    --aggregate_fn_name=weighted_average \
    --fps=30
```

Note that `bi_so_follower` prefixes each arm's camera names, so the camera `head` declared under
`left_arm_config` shows up in observations as `left_head` — that is the key `--image_keys` maps
from. The values are whatever image names the server's policy was trained on.
"""

import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pprint import pformat
from queue import Empty, Full, Queue

import draccus
import numpy as np

from lerobot.cameras.opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.cameras.realsense import RealSenseCameraConfig  # noqa: F401
from lerobot.robots import (  # noqa: F401
    Robot,
    RobotConfig,
    bi_so_follower,
    koch_follower,
    make_robot_from_config,
    omx_follower,
    so_follower,
)
from lerobot.utils.import_utils import register_third_party_plugins

from .websocket_client_policy import WebsocketClientPolicy

logger = logging.getLogger("lingbotvla_client")

IMAGE_LAYOUTS = ("bchw", "bhwc", "chw", "hwc")

# Same blending options as `lerobot.async_inference`, on numpy rather than torch. They are
# redefined here so this script does not pull in the gRPC stack that module requires.
AGGREGATE_FUNCTIONS = {
    "weighted_average": lambda old, new: 0.3 * old + 0.7 * new,
    "latest_only": lambda old, new: new,
    "average": lambda old, new: 0.5 * old + 0.5 * new,
    "conservative": lambda old, new: 0.7 * old + 0.3 * new,
}


def get_aggregate_function(name: str):
    if name not in AGGREGATE_FUNCTIONS:
        raise ValueError(f"Unknown aggregate function '{name}'. Available: {list(AGGREGATE_FUNCTIONS)}")
    return AGGREGATE_FUNCTIONS[name]


@dataclass
class LingbotVLAClientConfig:
    # Robot configuration; the robot instance is built from this.
    robot: RobotConfig = field(metadata={"help": "Robot configuration"})

    # Maps robot observation camera keys to the image names the server's policy expects,
    # e.g. "{left_head: base_0_rgb, right_right: right_wrist_0_rgb}".
    image_keys: dict[str, str] = field(metadata={"help": "Robot camera key -> server image name"})

    # Natural-language instruction sent with every observation.
    task: str = field(metadata={"help": "Task instruction for the robot to execute"})

    # Websocket policy server.
    host: str = field(default="127.0.0.1", metadata={"help": "Policy server host"})
    port: int = field(default=8000, metadata={"help": "Policy server port"})
    api_key: str | None = field(default=None, metadata={"help": "Optional server API key"})

    # Observation encoding. `image_size` resizes every camera frame to a square of that side
    # (0 keeps the native resolution). `image_layout` selects the array layout the server expects;
    # layouts starting with "b" carry a leading batch dimension of 1, which also batches the
    # state vector and wraps the prompt in a list.
    image_size: int = field(default=224, metadata={"help": "Square resize for camera frames; 0 = native"})
    image_layout: str = field(default="bchw", metadata={"help": f"One of {IMAGE_LAYOUTS}"})

    # Action chunking / scheduling.
    actions_per_chunk: int = field(default=50, metadata={"help": "Max actions consumed per returned chunk"})
    chunk_size_threshold: float = field(
        default=0.5, metadata={"help": "Request a new chunk once the queue drops to this fraction"}
    )
    aggregate_fn_name: str = field(
        default="weighted_average",
        metadata={"help": f"How to blend overlapping actions. Options: {list(AGGREGATE_FUNCTIONS)}"},
    )
    fps: int = field(default=30, metadata={"help": "Control loop frequency"})

    # Ask the server to reset policy state before the first observation.
    reset_on_start: bool = field(default=False, metadata={"help": "Send a reset to the server on start"})
    robot_name: str = field(default="", metadata={"help": "Robot name passed along with the reset"})

    verbose: bool = field(default=False, metadata={"help": "Log per-chunk timing and queue state"})

    @property
    def environment_dt(self) -> float:
        return 1 / self.fps

    def __post_init__(self):
        if not self.image_keys:
            raise ValueError("image_keys cannot be empty")
        if self.image_layout not in IMAGE_LAYOUTS:
            raise ValueError(f"image_layout must be one of {IMAGE_LAYOUTS}, got {self.image_layout}")
        if not 0 <= self.chunk_size_threshold <= 1:
            raise ValueError(f"chunk_size_threshold must be in [0, 1], got {self.chunk_size_threshold}")
        if self.fps <= 0:
            raise ValueError(f"fps must be positive, got {self.fps}")
        if self.actions_per_chunk <= 0:
            raise ValueError(f"actions_per_chunk must be positive, got {self.actions_per_chunk}")

        self.aggregate_fn = get_aggregate_function(self.aggregate_fn_name)


def _sleep_until(deadline: float, spin: float = 0.001):
    """Sleep to an absolute deadline. `time.sleep` overshoots by a few ms, which at 30Hz costs
    ~10% of the control rate, so give back the last millisecond by spinning."""
    remaining = deadline - time.perf_counter()
    if remaining > spin:
        time.sleep(remaining - spin)
    while time.perf_counter() < deadline:
        pass


def _resize(frame: np.ndarray, size: int) -> np.ndarray:
    if size <= 0 or frame.shape[:2] == (size, size):
        return frame
    import cv2

    return cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)


def _encode_image(frame: np.ndarray, size: int, layout: str) -> np.ndarray:
    """Robot camera frame (H, W, C) uint8 -> the layout the server expects."""
    image = np.ascontiguousarray(_resize(frame, size), dtype=np.uint8)
    if layout.endswith("chw"):
        image = image.transpose(2, 0, 1)
    return image[None] if layout.startswith("b") else image


def _extract_actions(response: dict) -> np.ndarray:
    """Pull the action chunk out of a server response as a (horizon, action_dim) array."""
    for key in ("actions", "action"):
        if key in response:
            actions = np.asarray(response[key], dtype=np.float32)
            break
    else:
        raise KeyError(f"No 'actions' key in server response. Got keys: {sorted(response)}")

    if actions.ndim == 3 and actions.shape[0] == 1:  # drop the batch dimension
        actions = actions[0]
    if actions.ndim == 1:  # single action
        actions = actions[None]
    if actions.ndim != 2:
        raise ValueError(f"Expected an action chunk of shape (horizon, action_dim), got {actions.shape}")
    return actions


class LingbotVLAClient:
    def __init__(self, cfg: LingbotVLAClientConfig):
        self.cfg = cfg
        self.robot = make_robot_from_config(cfg.robot)
        self.robot.connect()

        # The motor keys double as the state vector and the action vector, in this order.
        self.motor_keys = list(self.robot.action_features)
        missing = set(cfg.image_keys) - set(self.robot.observation_features)
        if missing:
            available = sorted(k for k in self.robot.observation_features if k not in self.motor_keys)
            raise ValueError(
                f"Cameras {sorted(missing)} are not in the robot observation. Available: {available}"
            )

        self.policy = WebsocketClientPolicy(host=cfg.host, port=cfg.port, api_key=cfg.api_key)
        logger.info(f"Server metadata: {self.policy.get_server_metadata()}")
        if cfg.reset_on_start:
            self.policy.reset(cfg.robot_name)

        self.shutdown_event = threading.Event()

        # Actions waiting to be executed, keyed by timestep so late chunks can be blended in.
        self.queue: deque[tuple[int, np.ndarray]] = deque()
        self.queue_lock = threading.Lock()
        self.latest_timestep = -1  # index of the last action written to the motors
        self.chunk_size = -1  # horizon actually returned by the server, learned on the first chunk

        # Single-slot hand-off from the control loop to the inference thread.
        self.obs_slot: Queue[tuple[dict, int]] = Queue(maxsize=1)
        self.inference_in_flight = threading.Event()
        self.start_barrier = threading.Barrier(2)

        logger.info(f"Robot connected | state/action dim: {len(self.motor_keys)}")

    @property
    def running(self) -> bool:
        return not self.shutdown_event.is_set()

    def stop(self):
        self.shutdown_event.set()
        self.robot.disconnect()
        logger.info("Robot disconnected")

    def _build_observation(self) -> dict:
        raw = self.robot.get_observation()
        state = np.array([raw[k] for k in self.motor_keys], dtype=np.float32)
        images = {
            server_key: _encode_image(raw[robot_key], self.cfg.image_size, self.cfg.image_layout)
            for robot_key, server_key in self.cfg.image_keys.items()
        }
        if self.cfg.image_layout.startswith("b"):
            return {"image": images, "state": state[None], "prompt": [self.cfg.task]}
        return {"image": images, "state": state, "prompt": self.cfg.task}

    def _merge_chunk(self, start_timestep: int, actions: np.ndarray):
        """Blend an incoming chunk into the queue, dropping actions the robot already passed."""
        aggregate_fn = self.cfg.aggregate_fn
        with self.queue_lock:
            queued = dict(self.queue)
            latest = self.latest_timestep
            merged = {}
            for i, action in enumerate(actions[: self.cfg.actions_per_chunk]):
                timestep = start_timestep + i
                if timestep <= latest:
                    continue
                merged[timestep] = aggregate_fn(queued[timestep], action) if timestep in queued else action
            self.queue = deque(sorted(merged.items()))

    def _needs_new_chunk(self) -> bool:
        if self.inference_in_flight.is_set():
            return False
        with self.queue_lock:
            if self.chunk_size <= 0:  # nothing received yet: bootstrap the first chunk
                return True
            return len(self.queue) / self.chunk_size <= self.cfg.chunk_size_threshold

    def inference_loop(self):
        """Owns the websocket: observation in, action chunk out."""
        self.start_barrier.wait()
        logger.info("Inference thread starting")

        while self.running:
            try:
                observation, obs_timestep = self.obs_slot.get(timeout=self.cfg.environment_dt)
            except Empty:
                continue

            try:
                start = time.perf_counter()
                response = self.policy.infer(observation)
                actions = _extract_actions(response)
                round_trip = time.perf_counter() - start

                if actions.shape[1] != len(self.motor_keys):
                    logger.error(
                        f"Server returns {actions.shape[1]}-dim actions but the robot has "
                        f"{len(self.motor_keys)} motors: {self.motor_keys}"
                    )
                    self.shutdown_event.set()
                    return

                # The observation reflects the state after action `obs_timestep`, so the chunk the
                # policy returns starts at the next timestep.
                self._merge_chunk(obs_timestep + 1, actions)
                self.chunk_size = max(self.chunk_size, min(len(actions), self.cfg.actions_per_chunk))

                if self.cfg.verbose:
                    timing = response.get("server_timing", {})
                    with self.queue_lock:
                        queue_size = len(self.queue)
                    logger.info(
                        f"Chunk for step #{obs_timestep + 1} | horizon: {len(actions)} | "
                        f"round trip: {round_trip * 1000:.1f}ms | "
                        f"server infer: {timing.get('infer_ms', float('nan')):.1f}ms | "
                        f"queue: {queue_size}"
                    )
            except Exception as e:
                logger.error(f"Inference failed: {e}")
            finally:
                # Cleared only after the chunk is queued, so the control loop cannot fire a
                # redundant observation for a chunk that is already on its way in.
                self.inference_in_flight.clear()

    def control_loop(self):
        """Owns the robot: pops actions to the motors, hands observations to the inference thread."""
        self.start_barrier.wait()
        logger.info("Control loop starting")

        deadline = time.perf_counter()
        while self.running:
            deadline += self.cfg.environment_dt

            # (1) Send a fresh observation whenever the queue is running low.
            if self._needs_new_chunk():
                obs_timestep = self.latest_timestep
                observation = self._build_observation()
                self.inference_in_flight.set()
                try:
                    self.obs_slot.put_nowait((observation, obs_timestep))
                except Full:  # slot still occupied, the inference thread will catch up
                    self.inference_in_flight.clear()

            # (2) Execute the next action, if one is available.
            with self.queue_lock:
                timed_action = self.queue.popleft() if self.queue else None
            if timed_action is not None:
                timestep, action = timed_action
                self.robot.send_action(dict(zip(self.motor_keys, action.tolist(), strict=True)))
                with self.queue_lock:
                    self.latest_timestep = timestep

            # Pace against an absolute deadline so per-iteration overshoot does not accumulate.
            # If capturing an observation or writing to the motors ran long, resync rather than
            # firing a burst of catch-up actions.
            if time.perf_counter() > deadline:
                deadline = time.perf_counter()
            else:
                _sleep_until(deadline)


@draccus.wrap()
def lingbotvla_client(cfg: LingbotVLAClientConfig):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logger.info(pformat(asdict(cfg)))

    client = LingbotVLAClient(cfg)
    inference_thread = threading.Thread(target=client.inference_loop, daemon=True)
    inference_thread.start()

    try:
        client.control_loop()
    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")
    finally:
        client.stop()
        inference_thread.join(timeout=2.0)
        logger.info("Client stopped")


if __name__ == "__main__":
    register_third_party_plugins()
    lingbotvla_client()
