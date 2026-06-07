# 树莓派部署指南 - ACT 策略推理

本指南用于在树莓派上部署和运行 ACT 机器人策略的实时推理。

## 系统要求

| 组件 | 要求 | 备注 |
|------|------|------|
| **树莓派** | Pi 4B+ 或更新 | 推荐 4GB+ RAM |
| **操作系统** | Raspberry Pi OS 64-bit | 32-bit 版本可能内存不足 |
| **Python** | 3.9+ | 推荐 3.11+ |
| **摄像头** | USB 或 Raspberry Pi Camera | 支持 V4L2 |
| **网络** | 以太网或 Wi-Fi | 用于模型下载 |

## 1. 树莓派环境配置

### 1.1 基础系统更新
```bash
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
sudo apt install -y python3-dev python3-pip git libopenblas-dev libomp-dev
sudo apt install -y libatlas-base-dev libjasper-dev libtiff-dev libjasper1
sudo apt install -y libharfbuzz0b libwebp6 libtiff5 libjasper1 libatlas3-base
sudo apt install -y libharfbuzz0b libwebp6 libatlas-base-dev libjasper-dev libtiff-dev
sudo apt install -y ffmpeg
```

### 1.2 启用摄像头
```bash
# 编辑配置
sudo raspi-config

# 选择 Interface Options → Camera → Enable
# 重启树莓派
sudo reboot
```

### 1.3 创建虚拟环境
```bash
cd ~
python3 -m venv lerobot_env
source lerobot_env/bin/activate
```

## 2. PyTorch for ARM 安装

### 2.1 安装 PyTorch (CPU 优化版本)

```bash
# 激活虚拟环境
source ~/lerobot_env/bin/activate

# 安装 PyTorch for ARM64
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 或使用预编译的 ARM 优化版本 (更快)
pip install https://github.com/neon-ai-dev/pytorch-arm/releases/download/v2.1.0/torch-2.1.0-cp311-cp311-linux_aarch64.whl
```

### 2.2 安装 LeRobot 依赖

```bash
# 从源码安装 (推荐在树莓派上)
git clone https://github.com/huggingface/lerobot.git
cd lerobot

# 安装基础依赖
pip install -e .

# 或安装特定依赖 (不需要所有可选包)
pip install -e ".[dev]"
```

## 3. 模型转换和优化

### 3.1 导出为 ONNX (可选 - 更快)

ONNX Runtime 在 ARM 上比 PyTorch 快 2-3 倍。

```bash
# 在 Mac/Linux 上转换模型
python -c "
import torch
from lerobot.policies.factory import make_policy

policy = make_policy(pretrained_model_name_or_path='path/to/model', device='cpu')
policy.eval()

# 创建示例输入
batch_size = 1
image = torch.randn(batch_size, 3, 480, 640)
state = torch.randn(batch_size, 6)

# 导出为 ONNX
torch.onnx.export(
    policy,
    (image, state),
    'model.onnx',
    input_names=['image', 'state'],
    output_names=['action'],
    opset_version=13,
)
"

# 在树莓派上使用 ONNX Runtime
pip install onnxruntime
# 注意: 确保 onnxruntime 是为 ARM 编译的
```

### 3.2 模型量化

```python
# 在 Mac/Linux 上量化模型为 INT8
import torch
from lerobot.policies.factory import make_policy

policy = make_policy(pretrained_model_name_or_path='path/to/model', device='cpu')
policy = torch.quantization.quantize_dynamic(
    policy,
    {torch.nn.Linear},
    dtype=torch.qint8,
)
torch.save(policy.state_dict(), 'model_quantized.pt')
```

## 4. 运行推理

### 4.1 基础推理

```bash
# 激活虚拟环境
source ~/lerobot_env/bin/activate
cd lerobot

# 运行推理脚本
python examples/raspberry_pi_inference.py \
    --model-path /path/to/model \
    --camera-id 0 \
    --num-frames 10
```

### 4.2 优化推理 (推荐)

```bash
# 使用 FP16 半精度 (减少 50% 内存占用)
python examples/raspberry_pi_inference_optimized.py \
    --model-path /path/to/model \
    --camera-id 0 \
    --use-fp16 \
    --num-frames 10
```

### 4.3 性能监控

```bash
# 监控树莓派 CPU 和内存使用
watch -n 1 'free -h && echo "---" && ps aux | grep python'

# 在另一个终端运行推理
python examples/raspberry_pi_inference_optimized.py \
    --model-path /path/to/model \
    --use-fp16
```

## 5. 性能优化建议

### 5.1 内存优化

| 优化项 | 效果 | 成本 |
|-------|------|------|
| **FP16 半精度** | 减少 50% 内存 | 精度下降 <1% |
| **动态量化** | 减少 30% 内存 | 推理慢 10-20% |
| **模型蒸馏** | 减少 70% 模型大小 | 需要重新训练 |
| **ONNX Runtime** | 快 2-3 倍 | 需要转换模型 |

### 5.2 CPU 优化

```bash
# 1. 禁用 Turbo Boost (降低功耗和热量)
echo powersave | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# 2. 增加 Swap (用于大型模型)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 使用 OpenBLAS 或 Eigen 后端
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
```

### 5.3 图像处理优化

```python
# 使用 OpenCV 硬件加速 (如果支持)
import cv2

# 启用 OpenCV 优化
cv2.setUseOptimized(True)
cv2.setNumThreads(4)

# 使用更快的调整大小插值
img_resized = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)
```

## 6. 常见问题

### Q: 推理太慢了 (>1 秒/帧)

**A:** 树莓派 CPU 的限制。尝试:
1. 使用 `--use-fp16` 加速
2. 转换为 ONNX Runtime (快 2-3 倍)
3. 使用 Jetson Nano/Orin 代替

### Q: 内存不足错误

**A:** 
1. 增加 Swap 空间
2. 使用 `--use-fp16` 减少 50% 内存
3. 使用模型量化

### Q: 摄像头无法检测

**A:**
1. 检查连接: `ls /dev/video*`
2. 测试摄像头: `libcamera-hello`
3. 安装 picamera2: `sudo apt install -y python3-picamera2`

### Q: USB 摄像头延迟高

**A:**
1. 降低帧率: `cap.set(cv2.CAP_PROP_FPS, 15)`
2. 使用 CSI 摄像头代替 USB
3. 增加 USB 带宽配置

## 7. 性能基准 (参考)

### ACT 模型 (ResNet18 + Transformer) 在树莓派上的推理时间

| 设置 | 推理时间 | 内存占用 |
|------|---------|---------|
| FP32 CPU | 5-10s | ~400MB |
| FP16 CPU | 3-6s | ~200MB |
| ONNX Runtime | 1-2s | ~150MB |
| Jetson Nano (FP32) | 0.5-1s | ~500MB |
| Jetson Orin (FP16) | 50-100ms | ~300MB |

**注**: 实际时间取决于模型大小、输入分辨率和树莓派硬件版本。

## 8. 下一步

- [ ] 连接真实机器人硬件
- [ ] 实现控制循环
- [ ] 添加力反馈
- [ ] 性能分析和优化
- [ ] 部署到容器 (Docker)

## 参考资源

- [PyTorch ARM 编译指南](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mobile/pytorch_mobile_and_raspberry_pi.md)
- [树莓派 Camera 配置](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [ONNX Runtime ARM 优化](https://onnxruntime.ai/docs/execution-providers/ARM-NN-ExecutionProvider.html)
- [LeRobot GitHub](https://github.com/huggingface/lerobot)
