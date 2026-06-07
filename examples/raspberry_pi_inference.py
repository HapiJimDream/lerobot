#!/usr/bin/env python3
"""
ACT 策略在树莓派上的推理脚本
适用于实时机器人控制

用法:
    python examples/raspberry_pi_inference.py \\
        --model-path outputs/train/act_pick_red_box/checkpoints/last/pretrained_model \\
        --camera-id 0  # 摄像头设备 ID
"""

import argparse
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
from PIL import Image

from lerobot.configs import PreTrainedConfig
from lerobot.policies.factory import get_policy_class


class RaspberryPiInference:
    def __init__(self, model_path: str, device: str = "cpu"):
        """初始化推理引擎"""
        self.model_path = Path(model_path)
        self.device = device

        print(f"[INFO] 从 {model_path} 加载模型...")
        # 加载配置并获取策略类
        config = PreTrainedConfig.from_pretrained(str(self.model_path))
        policy_class = get_policy_class(config.type)

        # 加载模型
        self.policy = policy_class.from_pretrained(
            str(self.model_path),
            device=device,
        )
        self.policy.eval()

        self.config = self.policy.config
        print(f"[INFO] 模型加载完成")
        print(f"  - 输入特征: {list(self.config.input_features.keys())}")
        print(f"  - 输出特征: {list(self.config.output_features.keys())}")
        print(f"  - 观察步数: {self.config.n_obs_steps}")
        print(f"  - 动作步数: {self.config.n_action_steps}")

    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """预处理图像"""
        # 获取目标尺寸（从配置中）
        expected_shape = self.config.input_features["observation.images.wrist"].shape
        channels, height, width = expected_shape

        # 调整大小
        image = cv2.resize(image, (width, height))

        # BGR -> RGB
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # HWC -> CHW
        image = image.transpose(2, 0, 1)

        # 转换为张量并归一化到 [0, 1]
        image_tensor = torch.FloatTensor(image) / 255.0

        return image_tensor

    def preprocess_state(self, state: np.ndarray) -> torch.Tensor:
        """预处理状态向量"""
        state_tensor = torch.FloatTensor(state)
        return state_tensor

    def run_inference(
        self,
        image: np.ndarray,
        state: np.ndarray,
    ) -> np.ndarray:
        """
        运行推理

        Args:
            image: 摄像头图像 (HxWx3) BGR 格式
            state: 状态向量 (6,) - 例如关节角度

        Returns:
            预测的动作 (n_action_steps, action_dim)
        """
        # 预处理输入
        image_tensor = self.preprocess_image(image)
        state_tensor = self.preprocess_state(state)

        # 准备输入字典
        image_tensor = image_tensor.unsqueeze(0).to(self.device)  # (1, 3, H, W)
        state_tensor = state_tensor.unsqueeze(0).to(self.device)  # (1, 6)

        input_data = {
            "observation.images.wrist": image_tensor,
            "observation.state": state_tensor,
        }

        # 运行推理
        with torch.no_grad():
            action = self.policy.select_action(input_data)

        # 动作是一个 1D 张量 (action_dim,)
        action = action.cpu().numpy()

        return action

    def capture_from_camera(self, camera_id: int = 0) -> Optional[np.ndarray]:
        """从摄像头捕获图像"""
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"[ERROR] 无法打开摄像头 {camera_id}")
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("[ERROR] 无法读取摄像头帧")
            return None

        return frame

    def run_realtime_inference(self, camera_id: int = 0, num_frames: int = 10):
        """实时推理循环（演示用）"""
        print(f"\n[INFO] 启动实时推理 (将处理 {num_frames} 帧)")
        print("[INFO] 按 'q' 停止\n")

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"[ERROR] 无法打开摄像头 {camera_id}")
            return

        frame_count = 0
        times = []

        try:
            while frame_count < num_frames:
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] 无法读取摄像头帧")
                    break

                # 示例状态 (关节角度)
                state = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

                # 推理
                start_time = time.time()
                action = self.run_inference(frame, state)
                inference_time = time.time() - start_time
                times.append(inference_time)

                # 显示结果
                print(f"[Frame {frame_count+1}]")
                print(f"  推理时间: {inference_time:.3f}s")
                print(f"  预测动作: {action}")

                # 显示图像 (可选)
                cv2.putText(
                    frame,
                    f"Inference: {inference_time:.1f}ms",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("Frame", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                frame_count += 1

        finally:
            cap.release()
            cv2.destroyAllWindows()

            # 统计信息
            print(f"\n[INFO] 统计:")
            print(f"  总帧数: {len(times)}")
            print(f"  平均推理时间: {np.mean(times):.3f}s")
            print(f"  最小推理时间: {np.min(times):.3f}s")
            print(f"  最大推理时间: {np.max(times):.3f}s")
            print(f"  平均 FPS: {1.0 / np.mean(times):.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="树莓派 ACT 策略推理"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="预训练模型路径",
    )
    parser.add_argument(
        "--camera-id",
        type=int,
        default=0,
        help="摄像头设备 ID (default: 0)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "mps", "cuda"],
        help="推理设备 (default: cpu)",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=10,
        help="推理帧数 (default: 10)",
    )

    args = parser.parse_args()

    # 初始化推理引擎
    inference_engine = RaspberryPiInference(
        model_path=args.model_path,
        device=args.device,
    )

    # 运行实时推理
    inference_engine.run_realtime_inference(
        camera_id=args.camera_id,
        num_frames=args.num_frames,
    )


if __name__ == "__main__":
    main()
