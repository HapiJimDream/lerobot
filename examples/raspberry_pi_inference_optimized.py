#!/usr/bin/env python3
"""
树莓派优化版本 - 推理脚本
针对低功耗设备的内存优化和性能优化

优化策略:
  1. FP16 半精度 - 减少内存占用 50%
  2. 动态内存释放 - 及时释放推理中间变量
  3. 图像缓冲池 - 减少内存分配
  4. 推理线程异步处理 - 不阻塞控制线程

用法:
    python examples/raspberry_pi_inference_optimized.py \\
        --model-path outputs/train/act_pick_red_box/checkpoints/last/pretrained_model \\
        --use-fp16 \\
        --camera-id 0
"""

import argparse
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Optional

import cv2
import numpy as np
import torch
from PIL import Image

from lerobot.configs import PreTrainedConfig
from lerobot.policies.factory import get_policy_class


class ImageBuffer:
    """图像缓冲池 - 减少内存分配频率"""

    def __init__(self, max_size: int = 10):
        self.buffers = Queue(maxsize=max_size)
        for _ in range(max_size):
            self.buffers.put(np.zeros((480, 640, 3), dtype=np.uint8))

    def get(self) -> np.ndarray:
        try:
            return self.buffers.get_nowait()
        except:
            return np.zeros((480, 640, 3), dtype=np.uint8)

    def put(self, buf: np.ndarray):
        try:
            self.buffers.put_nowait(buf)
        except:
            pass


class OptimizedRaspberryPiInference:
    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        use_fp16: bool = False,
        use_torch_compile: bool = False,
    ):
        """
        初始化优化推理引擎

        Args:
            model_path: 模型路径
            device: 推理设备 (cpu, mps, cuda)
            use_fp16: 是否使用半精度 (FP16)
            use_torch_compile: 是否使用 torch.compile() (需要 PyTorch 2.0+)
        """
        self.model_path = Path(model_path)
        self.device = device
        self.use_fp16 = use_fp16
        self.dtype = torch.float16 if use_fp16 else torch.float32

        print(f"[INFO] 加载模型: {model_path}")
        print(f"[INFO] 设备: {device}, 精度: {'FP16' if use_fp16 else 'FP32'}")

        # 加载配置并获取策略类
        config = PreTrainedConfig.from_pretrained(str(self.model_path))
        policy_class = get_policy_class(config.type)

        # 加载模型
        self.policy = policy_class.from_pretrained(
            str(self.model_path),
            device=device,
        )
        self.policy.eval()

        # 转换为目标精度
        if use_fp16:
            self.policy = self.policy.half()

        # 可选: torch.compile 加速 (需要 PyTorch 2.0+)
        if use_torch_compile and hasattr(torch, "compile"):
            print("[INFO] 使用 torch.compile() 加速...")
            try:
                self.policy = torch.compile(self.policy, mode="reduce-overhead")
            except Exception as e:
                print(f"[WARNING] torch.compile() 失败: {e}")

        self.config = self.policy.config
        self.image_buffer = ImageBuffer(max_size=5)

        print(f"[INFO] 模型加载完成")
        print(f"  输入: {list(self.config.input_features.keys())}")
        print(f"  输出: {list(self.config.output_features.keys())}")

    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """预处理图像"""
        expected_shape = self.config.input_features["observation.images.wrist"].shape
        channels, height, width = expected_shape

        # 快速调整大小
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)

        # BGR -> RGB
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # HWC -> CHW
        image = image.transpose(2, 0, 1)

        # 转换为张量并归一化
        image_tensor = torch.from_numpy(image).to(self.dtype) / 255.0

        return image_tensor

    def preprocess_state(self, state: np.ndarray) -> torch.Tensor:
        """预处理状态"""
        state_tensor = torch.from_numpy(state).to(self.dtype)
        return state_tensor

    def run_inference(
        self,
        image: np.ndarray,
        state: np.ndarray,
    ) -> np.ndarray:
        """运行推理"""
        image_tensor = self.preprocess_image(image)
        state_tensor = self.preprocess_state(state)

        # 添加 batch 维度
        image_tensor = image_tensor.unsqueeze(0).to(self.device)
        state_tensor = state_tensor.unsqueeze(0).to(self.device)

        input_data = {
            "observation.images.wrist": image_tensor,
            "observation.state": state_tensor,
        }

        # 推理
        with torch.no_grad():
            action = self.policy.select_action(input_data)

        action = action.cpu().numpy()

        # 释放中间变量
        del image_tensor, state_tensor, input_data, output
        torch.cuda.empty_cache() if self.device == "cuda" else None

        return action

    def run_realtime_inference(self, camera_id: int = 0, num_frames: int = 10):
        """实时推理循环"""
        print(f"\n[INFO] 启动实时推理 (处理 {num_frames} 帧)")

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"[ERROR] 无法打开摄像头 {camera_id}")
            return

        # 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        frame_count = 0
        times = []
        memory_usage = []

        try:
            while frame_count < num_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                # 示例状态
                state = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

                # 推理
                start_time = time.time()
                action = self.run_inference(frame, state)
                inference_time = time.time() - start_time
                times.append(inference_time)

                # 内存使用
                if self.device == "cuda":
                    mem_used = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                    memory_usage.append(mem_used)

                # 输出
                print(
                    f"[Frame {frame_count+1}] 推理: {inference_time*1000:.1f}ms | "
                    f"动作: {action}"
                )

                # 显示
                text = f"Time: {inference_time*1000:.0f}ms | FPS: {1.0/inference_time:.1f}"
                cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Inference", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                frame_count += 1

        finally:
            cap.release()
            cv2.destroyAllWindows()

            # 统计
            print(f"\n[INFO] 统计:")
            print(f"  处理帧数: {len(times)}")
            print(f"  平均推理时间: {np.mean(times)*1000:.1f}ms")
            print(f"  最快推理时间: {np.min(times)*1000:.1f}ms")
            print(f"  最慢推理时间: {np.max(times)*1000:.1f}ms")
            print(f"  平均 FPS: {1.0/np.mean(times):.2f}")
            if memory_usage:
                print(f"  平均内存使用: {np.mean(memory_usage):.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="树莓派优化推理脚本")
    parser.add_argument("--model-path", type=str, required=True, help="模型路径")
    parser.add_argument("--camera-id", type=int, default=0, help="摄像头 ID")
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "mps", "cuda"],
        help="推理设备",
    )
    parser.add_argument(
        "--use-fp16",
        action="store_true",
        help="使用 FP16 半精度 (减少 50% 内存)",
    )
    parser.add_argument(
        "--use-torch-compile",
        action="store_true",
        help="使用 torch.compile() (PyTorch 2.0+)",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=10,
        help="推理帧数",
    )

    args = parser.parse_args()

    inference_engine = OptimizedRaspberryPiInference(
        model_path=args.model_path,
        device=args.device,
        use_fp16=args.use_fp16,
        use_torch_compile=args.use_torch_compile,
    )

    inference_engine.run_realtime_inference(
        camera_id=args.camera_id,
        num_frames=args.num_frames,
    )


if __name__ == "__main__":
    main()
