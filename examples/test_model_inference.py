#!/usr/bin/env python3
"""
模型推理测试脚本 - 不需要摄像头
用于验证模型是否能正确加载和运行推理

用法:
    python examples/test_model_inference.py \\
        --model-path outputs/train/act_pick_red_box/checkpoints/last/pretrained_model
"""

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.configs import PreTrainedConfig
from lerobot.policies.factory import get_policy_class


def test_model_inference(
    model_path: str,
    device: str = "cpu",
    num_iterations: int = 5,
    use_fp16: bool = False,
):
    """测试模型推理"""
    model_path = Path(model_path)

    if not model_path.exists():
        print(f"[ERROR] 模型路径不存在: {model_path}")
        return False

    print(f"[INFO] 加载模型: {model_path}")
    print(f"[INFO] 设备: {device}, 精度: {'FP16' if use_fp16 else 'FP32'}")

    try:
        # 加载配置
        config = PreTrainedConfig.from_pretrained(str(model_path))
        policy_class = get_policy_class(config.type)

        # 加载模型
        policy = policy_class.from_pretrained(
            str(model_path),
            device=device,
        )
        policy.eval()

        # 转换为 FP16 (如果指定)
        if use_fp16:
            policy = policy.half()

        config = policy.config
        print(f"[OK] 模型加载成功")
        print(f"  - 配置类型: {config.type}")
        print(f"  - 观察步数: {config.n_obs_steps}")
        print(f"  - 动作步数: {config.n_action_steps}")
        print(f"  - 输入特征: {list(config.input_features.keys())}")
        print(f"  - 输出特征: {list(config.output_features.keys())}")

        # 获取输入尺寸
        image_shape = config.input_features["observation.images.wrist"].shape
        state_shape = config.input_features["observation.state"].shape
        action_shape = config.output_features["action"].shape

        print(f"\n[INFO] 输入/输出尺寸:")
        print(f"  - 图像: {image_shape}")
        print(f"  - 状态: {state_shape}")
        print(f"  - 动作: {action_shape}")

        # 创建虚拟输入
        batch_size = 1
        channels, height, width = image_shape
        state_dim = state_shape[0]

        print(f"\n[INFO] 运行 {num_iterations} 次推理测试...")

        times = []
        for i in range(num_iterations):
            # 创建随机输入
            image = torch.randn(batch_size, channels, height, width).to(device)
            state = torch.randn(batch_size, state_dim).to(device)

            # 如果使用 FP16，转换输入
            if use_fp16:
                image = image.half()
                state = state.half()

            input_data = {
                "observation.images.wrist": image,
                "observation.state": state,
            }

            # 推理
            start_time = time.time()
            with torch.no_grad():
                action = policy.select_action(input_data)
            inference_time = time.time() - start_time
            times.append(inference_time)

            # 动作是一个 1D 张量
            action_shape_actual = action.shape

            print(
                f"  [{i+1}/{num_iterations}] "
                f"时间: {inference_time*1000:.1f}ms | "
                f"输出形状: {action_shape_actual} | "
                f"值范围: [{action.min():.3f}, {action.max():.3f}]"
            )

            # 释放内存
            del image, state, input_data, action
            if device == "cuda":
                torch.cuda.empty_cache()

        # 统计
        print(f"\n[INFO] 推理统计:")
        print(f"  - 平均推理时间: {np.mean(times)*1000:.1f}ms")
        print(f"  - 最小推理时间: {np.min(times)*1000:.1f}ms")
        print(f"  - 最大推理时间: {np.max(times)*1000:.1f}ms")
        print(f"  - 标准差: {np.std(times)*1000:.1f}ms")
        print(f"  - 平均 FPS: {1.0 / np.mean(times):.2f}")

        # 内存使用
        if device == "cuda":
            memory_used = torch.cuda.memory_allocated() / 1024 / 1024
            memory_reserved = torch.cuda.memory_reserved() / 1024 / 1024
            print(f"\n[INFO] 显存使用:")
            print(f"  - 已分配: {memory_used:.1f} MB")
            print(f"  - 已预留: {memory_reserved:.1f} MB")
        else:
            # CPU 内存估计
            model_size = sum(p.numel() * p.element_size() for p in policy.parameters()) / 1024 / 1024
            print(f"\n[INFO] 模型大小: {model_size:.1f} MB")

        print(f"\n[OK] 所有测试通过! ✓")
        return True

    except Exception as e:
        print(f"[ERROR] 推理失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="模型推理测试"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="预训练模型路径",
    )
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
        help="使用 FP16 半精度",
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=5,
        help="推理迭代次数",
    )

    args = parser.parse_args()

    success = test_model_inference(
        model_path=args.model_path,
        device=args.device,
        num_iterations=args.num_iterations,
        use_fp16=args.use_fp16,
    )

    exit(0 if success else 1)


if __name__ == "__main__":
    main()
