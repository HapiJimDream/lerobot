# Joy-Con 虚拟机遥操作脚本使用说明

## 概述

`7_xlerobot_2wheels_teleop_joycon_pygame.py` 是一个基于 **pygame** 的 Joy-Con 遥操作脚本，专为 **Parallels 虚拟机环境**设计。通过 Parallels 的 macOS 游戏控制器框架，Joy-Con 被映射为虚拟 Xbox 控制器，可在虚拟机中通过 pygame 读取输入。

## 核心特性

| 特性 | 说明 |
|------|------|
| **连接方式** | 通过 Parallels Xbox 映射使用 pygame 读取 |
| **适用环境** | 虚拟机（无需蓝牙直通） |
| **控制对象** | XLerobot 2Wheels（双臂+头部+差速底盘） |
| **平滑控制** | 底盘加减速平滑 |
| **IMU 支持** | ❌ 不可用（pygame 限制） |

## 环境准备

### 1. 虚拟机端（Ubuntu）

```bash
# 安装 pygame
pip install pygame

# 确认 Joy-Con 设备存在
ls /dev/input/js*
# 应显示 js0（原有设备）和 js1（Joy-Con 映射）
```

### 2. macOS 端

1. 打开 **系统设置** → **蓝牙**
2. 按住 Joy-Con 的 **配对按钮**（手柄内侧小圆按钮）
3. 连接 Joy-Con，确认显示为 **"已连接"**
4. Parallels 自动将其映射为虚拟 Xbox 控制器

## 运行方法

### 启动机器人主机（可选，如使用网络模式）

```bash
PYTHONPATH=src python -m lerobot.robots.xlerobot_2wheels.xlerobot_2wheels_host --robot.id=my_xlerobot_2wheels
```

### 启动遥操作脚本

```bash
PYTHONPATH=src python examples/7_xlerobot_2wheels_teleop_joycon_pygame.py
```

## Joy-Con 按键映射

### 底盘控制（方向键 - 左手柄 ⬆️⬇️⬅️➡️）

| 功能 | Joy-Con 按键 | 编号 | 手柄 |
|------|-------------|------|------|
| 前进 | 方向键上 | 11 | **左手柄** ⬆️ |
| 后退 | 方向键下 | 12 | **左手柄** ⬇️ |
| 左转 | 方向键左 | 13 | **左手柄** ⬅️ |
| 右转 | 方向键右 | 14 | **左手柄** ➡️ |

### 左臂控制（左手柄 🔵）

| 功能 | 输入方式 | 手柄 |
|------|---------|------|
| X/Y 移动 | 左摇杆（轴0/轴1） | **左手柄** 🕹️ |
| shoulder_pan | L键(9) + 左摇杆左右 | **左手柄** L+🕹️ |
| pitch/wrist_roll | ZL(轴4) + 左摇杆 | **左手柄** ZL+🕹️ |
| 夹爪 | ZL 扳机(轴4) | **左手柄** ZL |

### 右臂控制（右手柄 🔴）

| 功能 | 输入方式 | 手柄 |
|------|---------|------|
| X/Y 移动 | 右摇杆（轴2/轴3） | **右手柄** 🕹️ |
| shoulder_pan | R键(10) + 右摇杆左右 | **右手柄** R+🕹️ |
| pitch/wrist_roll | ZR(轴5) + 右摇杆 | **右手柄** ZR+🕹️ |
| 夹爪 | ZR 扳机(轴5) | **右手柄** ZR |

### 头部控制（右手柄 🔴）

| 功能 | 按键 | 手柄 |
|------|------|------|
| head_motor_1+ | X (2) | **右手柄** X |
| head_motor_1- | B (1) | **右手柄** B |
| head_motor_2+ | A (0) | **右手柄** A |
| head_motor_2- | Y (3) | **右手柄** Y |

### 全局控制（右手柄 🔴）

| 功能 | 按键 | 手柄 |
|------|------|------|
| 复位所有 | Capture (15) | **右手柄** ⭕️ |

## 按键编号参考

基于 `readme.md` 的映射记录：

```
右手柄 🔴:
  X:2, A:0, B:1, Y:3, ZR:轴5, R:10, +:6, 主页:5
  右摇杆X:轴2, 右摇杆Y:轴3

左手柄 🔵:
  上:11, 下:12, 左:13, 右:14
  左摇杆X:轴0, 左摇杆Y:轴1
  -:4, ZL:轴4, L:9, ⭕️:15
```

## 技术限制

### ❌ 无法获取的功能

| 功能 | 原因 |
|------|------|
| IMU 姿态数据 | pygame 只能读取映射后的 Xbox 数据，无法访问 Joy-Con 原始陀螺仪/加速度计 |
| 倾斜控制 | 依赖 IMU 数据，不可用 |
| 高精度摇杆值 | pygame 只提供 -1.0~1.0 浮点值，非原始 0-4095 |

### ✅ 可用的功能

- 摇杆位置（左/右）
- 按键状态（A/B/X/Y/L/R/ZL/ZR/方向键/Capture）
- 扳机值（ZL/ZR 作为轴）

## 与原生 Joy-Con 脚本对比

| 特性 | pygame 版本（本脚本） | joyconrobotics 版本 |
|------|---------------------|---------------------|
| **运行环境** | 虚拟机 ✅ | 需蓝牙直连 |
| **IMU 数据** | ❌ 不可用 | ✅ 完整支持 |
| **倾斜控制** | ❌ 不可用 | ✅ 支持 |
| **摇杆精度** | 浮点 -1~1 | 原始 0-4095 |
| **连接复杂度** | 低（自动映射） | 高（需蓝牙配对） |

## 故障排除

### 问题：未检测到控制器

```bash
# 检查设备
ls /dev/input/js*

# 应显示 /dev/input/js0 和 /dev/input/js1
# 如只有 js0，检查 macOS 端 Joy-Con 是否已连接
```

### 问题：按键无响应

1. 确认 macOS 端 Joy-Con 显示为 **"已连接"**
2. 运行调试脚本确认映射：
   ```bash
   python joycon_debug_CN.py
   ```

### 问题：方向键无法控制底盘

- 方向键在 Joy-Con 映射中作为 **按钮**（11-14），非 Xbox 的 hat
- 确认 `get_base_action_from_joycon()` 函数使用按钮读取

## 文件位置

```
/Users/jim/lerobot/examples/
├── 7_xlerobot_2wheels_teleop_joycon_pygame.py  # 本脚本
├── joycon_debug_CN.py                            # 调试脚本
└── readme.md                                     # 按键映射记录
```

## 相关脚本

| 脚本 | 用途 |
|------|------|
| `7_xlerobot_2wheels_teleop_joycon.py` | 原生 Joy-Con（需蓝牙） |
| `7_xlerobot_2wheels_teleop_joycon_smooth.py` | 原生 Joy-Con + 平滑控制 |
| `5_xlerobot_teleop_xbox.py` | Xbox 控制器版本 |
| `4_xlerobot_2wheels_teleop_keyboard.py` | 键盘控制版本 |

## 更新记录

- **2025-05-20**: 初始版本，基于 `5_xlerobot_teleop_xbox.py` 和 `4_xlerobot_2wheels_teleop_keyboard.py` 创建，适配 Joy-Con Parallels 映射
