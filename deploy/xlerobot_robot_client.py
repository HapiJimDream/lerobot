"""xlerobot(双臂 bi_so_follower)真机客户端:连接 LingBot-VLA 推理服务并控制机器人。

工作流程(同步整块执行,简单易懂):
    1. 连接机器人(lerobot BiSOFollower)和推理服务(websocket)
    2. 先向服务端发送 reset,让其加载 configs/robot_configs/{robo_name}.yaml
    3. 循环:读观测(3 路相机 + 12 维关节角)-> 发服务端推理 -> 得到动作块
       (use_length, 12) -> 按 fps 逐步执行整个动作块 -> 再次推理

服务端启动示例(需在 lingbot-vla 仓库根目录):
    export QWEN25_PATH=/path/to/Qwen2.5-VL-3B-Instruct
    python -m deploy.lingbot_vla_policy \
        --model_path /path/to/checkpoints/global_step_700/hf_ckpt \
        --use_compile --use_length 25 --num_denoising_step 5

客户端运行示例(机器人所在机器):
    python -m deploy.xlerobot_robot_client \
        --host 127.0.0.1 --port 8006 \
        --left_arm_port /dev/ttyLeftArm --right_arm_port /dev/ttyRightArm \
        --cam_head /dev/camHead --cam_left /dev/camLeft --cam_right /dev/camRight \
        --task "Place the object in the tray" \
        --max_steps 50

依赖说明:
    - 机器人端环境只需 lerobot(pip install -e /path/to/lerobot)+ websockets + msgpack + numpy,不需要 torch
    - use_degrees 等标定/单位设置必须与采集训练数据时一致(bi_so_follower 默认 use_degrees=True)
    - 首次推理前请让机器人处于合理的初始位姿
    - 先用 --dry_run 可在无硬件情况下验证与服务端的通信协议
"""

import argparse
import time

import numpy as np

from deploy.websocket_client_policy import WebsocketClientPolicy

# 12 维状态/动作的关节顺序,必须与训练数据(LeRobotDataset observation.state)一致:
# 左臂 5 关节 + 左夹爪 + 右臂 5 关节 + 右夹爪,
# 对应 configs/robot_configs/xlerobot_v1.yaml 中的切片 [0:5]+[6:11]=arm, [5]+[11]=effector
JOINT_KEYS = [
    "left_shoulder_pan.pos",
    "left_shoulder_lift.pos",
    "left_elbow_flex.pos",
    "left_wrist_flex.pos",
    "left_wrist_roll.pos",
    "left_gripper.pos",
    "right_shoulder_pan.pos",
    "right_shoulder_lift.pos",
    "right_elbow_flex.pos",
    "right_wrist_flex.pos",
    "right_wrist_roll.pos",
    "right_gripper.pos",
]

# lerobot 观测中的相机键 -> 训练数据集中的图像键(见 xlerobot_v1.yaml 的 origin_keys)
CAMERA_KEY_MAPPING = {
    "left_head": "observation.images.left_head",
    "left_left": "observation.images.left_left",
    "right_right": "observation.images.right_right",
}


def build_observation(robot_obs: dict, task: str) -> dict:
    """把 lerobot 的观测 dict 转成服务端期望的原始数据集键格式。

    服务端(FeatureTransform)负责所有键映射、resize 和归一化,
    客户端只需发送原始 12 维关节角、原始尺寸的 RGB 图像(HWC uint8)和任务文本。
    """
    obs = {
        "observation.state": np.array(
            [robot_obs[k] for k in JOINT_KEYS], dtype=np.float32
        ),
        "task": task,
    }
    for cam_key, image_key in CAMERA_KEY_MAPPING.items():
        image = robot_obs[cam_key]
        assert image.ndim == 3 and image.shape[-1] == 3, (
            f"相机 {cam_key} 图像应为 HWC 3 通道, 实际 shape={image.shape}"
        )
        obs[image_key] = np.ascontiguousarray(image, dtype=np.uint8)
    return obs


def make_robot(args):
    """按参考命令的相机布局构造 BiSOFollower:左臂挂 head/left 两个相机,右臂挂 right 相机。"""
    from lerobot.cameras.opencv import OpenCVCameraConfig
    from lerobot.robots.bi_so_follower import BiSOFollower, BiSOFollowerConfig
    from lerobot.robots.so_follower import SOFollowerConfig

    def camera(index_or_path):
        # 支持 /dev/camHead 这类设备路径, 也支持数字索引
        if isinstance(index_or_path, str) and index_or_path.isdigit():
            index_or_path = int(index_or_path)
        return OpenCVCameraConfig(
            index_or_path=index_or_path,
            width=args.cam_width,
            height=args.cam_height,
            fps=args.cam_fps,
        )

    config = BiSOFollowerConfig(
        id=args.robot_id,
        left_arm_config=SOFollowerConfig(
            port=args.left_arm_port,
            max_relative_target=args.max_relative_target,
            cameras={"head": camera(args.cam_head), "left": camera(args.cam_left)},
        ),
        right_arm_config=SOFollowerConfig(
            port=args.right_arm_port,
            max_relative_target=args.max_relative_target,
            cameras={"right": camera(args.cam_right)},
        ),
    )
    return BiSOFollower(config)


class FakeRobot:
    """--dry_run 模式使用的假机器人, 用于无硬件时验证与服务端的通信协议。"""

    def connect(self):
        print("[dry_run] 使用假机器人, 不连接真实硬件")

    def disconnect(self):
        pass

    def get_observation(self):
        obs = {k: 0.0 for k in JOINT_KEYS}
        for cam_key in CAMERA_KEY_MAPPING:
            obs[cam_key] = np.random.randint(0, 256, size=(480, 640, 3), dtype=np.uint8)
        return obs

    def send_action(self, action):
        return action


def main():
    parser = argparse.ArgumentParser(description="xlerobot 真机客户端: 接收 LingBot-VLA 服务端推理结果并控制双臂机器人")
    # 推理服务
    parser.add_argument("--host", type=str, default="127.0.0.1", help="推理服务地址")
    parser.add_argument("--port", type=int, default=8006, help="推理服务端口")
    parser.add_argument("--robo_name", type=str, default="xlerobot_v1",
                        help="服务端 configs/robot_configs/ 下的机器人配置名")
    # 机器人硬件
    parser.add_argument("--left_arm_port", type=str, default="/dev/ttyLeftArm", help="左臂串口")
    parser.add_argument("--right_arm_port", type=str, default="/dev/ttyRightArm", help="右臂串口")
    parser.add_argument("--robot_id", type=str, default="bimanual_follower", help="机器人 id(对应标定文件)")
    parser.add_argument("--cam_head", type=str, default="/dev/camHead", help="头部相机(挂在左臂配置下, 名为 head)")
    parser.add_argument("--cam_left", type=str, default="/dev/camLeft", help="左腕相机(挂在左臂配置下, 名为 left)")
    parser.add_argument("--cam_right", type=str, default="/dev/camRight", help="右腕相机(挂在右臂配置下, 名为 right)")
    parser.add_argument("--cam_width", type=int, default=640)
    parser.add_argument("--cam_height", type=int, default=480)
    parser.add_argument("--cam_fps", type=int, default=30)
    parser.add_argument("--max_relative_target", type=float, default=None,
                        help="单步最大关节位移限制(安全用, 默认不限制)")
    # 控制
    parser.add_argument("--task", type=str, required=True, help="任务描述文本")
    parser.add_argument("--fps", type=float, default=30, help="动作执行频率, 须与采集训练数据时一致")
    parser.add_argument("--max_steps", type=int, default=-1, help="最多执行的动作步数, -1 表示不限制")
    parser.add_argument("--dry_run", action="store_true", help="不连接真实机器人, 用假观测验证通信协议")
    args = parser.parse_args()

    if args.dry_run:
        robot = FakeRobot()
        precise_sleep = time.sleep
    else:
        from lerobot.utils.robot_utils import precise_sleep
        robot = make_robot(args)

    robot.connect()

    try:
        # 连接服务端并加载 robo_name 对应的 FeatureTransform(归一化统计等)
        client = WebsocketClientPolicy(host=args.host, port=args.port)
        print(f"服务端 metadata: {client.get_server_metadata()}")
        client.reset(robo_name=args.robo_name)
        print(f"服务端已 reset 为机器人配置: {args.robo_name}")

        dt = 1.0 / args.fps
        total_steps = 0
        while args.max_steps < 0 or total_steps < args.max_steps:
            # 1) 采集观测并请求推理
            observation = build_observation(robot.get_observation(), args.task)
            infer_start = time.perf_counter()
            result = client.infer(observation)
            action_chunk = result["action"]  # (use_length, 12), 反归一化后的绝对关节位置
            print(
                f"step {total_steps}: 推理耗时 {time.perf_counter() - infer_start:.3f}s, "
                f"动作块 shape={action_chunk.shape}, server_timing={result.get('server_timing')}"
            )

            # 2) 按 fps 逐步执行整个动作块
            for action_step in action_chunk:
                step_start = time.perf_counter()
                robot.send_action({k: float(v) for k, v in zip(JOINT_KEYS, action_step)})
                total_steps += 1
                if args.max_steps >= 0 and total_steps >= args.max_steps:
                    break
                precise_sleep(max(0.0, dt - (time.perf_counter() - step_start)))

        print(f"已完成 {total_steps} 步, 退出")
    except KeyboardInterrupt:
        print("\n收到 Ctrl-C, 停止控制")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()

