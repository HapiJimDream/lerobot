# 机器人情况
- lead left arm : /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61033431-if00
- lead right arm: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61034984-if00
- follower left arm : /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14115608-if00
- follower right arm : /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00

摄像头地址: 
主摄像头:/dev/v4l/by-path/platform-xhci-hcd.0-usb-0:1:1.0-video-index0
左摄像头:/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.1:1.0-video-index0
右摄像头:/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0

摄像头测试情况: 
✅ 摄像头 0: 640x480 @ 30.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.0-usb-0:1:1.0-video-index0
   实际设备: /dev/video0
   frame shape: (480, 640, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam0.jpg
✅ 摄像头 1: 1920x1080 @ 5.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.0-usb-0:1:1.0-video-index1
   实际设备: /dev/video1
   frame shape: (1080, 1920, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam1.jpg
✅ 摄像头 2: 640x480 @ 30.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.1:1.0-video-index0
   实际设备: /dev/video2
   frame shape: (480, 640, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam2.jpg
✅ 摄像头 3: 640x480 @ 30.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.1-usbv2-0:1.1:1.0-video-index1
   实际设备: /dev/video3
   frame shape: (480, 640, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam3.jpg
 ✅ 摄像头 4: 640x480 @ 30.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0
   实际设备: /dev/video4
   frame shape: (480, 640, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam4.jpg  
✅ 摄像头 5: 640x480 @ 30.0fps
   设备路径: /dev/v4l/by-path/platform-xhci-hcd.1-usbv2-0:1.2:1.0-video-index1
   实际设备: /dev/video5
   frame shape: (480, 640, 3)
   已保存: /home/jim/AiSpace/lerobot/examples/test_cam5.jpg

* 端口0:左臂,/dev/ttyACM0,电机1-6和舵机7-8,和头部摄像头
    ``` 
    bus1
        "left_arm_shoulder_pan": Motor(1, "sts3215", norm_mode_body),
        "left_arm_shoulder_lift": Motor(2, "sts3215", norm_mode_body),
        "left_arm_elbow_flex": Motor(3, "sts3215", norm_mode_body),
        "left_arm_wrist_flex": Motor(4, "sts3215", norm_mode_body),
        "left_arm_wrist_roll": Motor(5, "sts3215", norm_mode_body),
        "left_arm_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
        # head
        "head_motor_1": Motor(7, "sts3215", norm_mode_body),
        "head_motor_2": Motor(8, "sts3215", norm_mode_body)
    ```
* 端口1: 右臂,/dev/ttyACM1,电机1-6和舵机9-10,和两个轮子
    ``` 
    bus2  
    "right_arm_shoulder_pan": Motor(1, "sts3215", norm_mode_body),
    "right_arm_shoulder_lift": Motor(2, "sts3215", norm_mode_body),
    "right_arm_elbow_flex": Motor(3, "sts3215", norm_mode_body),
    "right_arm_wrist_flex": Motor(4, "sts3215", norm_mode_body),
    "right_arm_wrist_roll": Motor(5, "sts3215", norm_mode_body),
    "right_arm_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
    # base - only 2 wheels for differential drive
    "base_left_wheel": Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
    "base_right_wheel": Motor(10, "sts3215", MotorNormMode.RANGE_M100_100)
    ```

# conda activate lerobot

# lerobot-find-port

# lsof -nP -iTCP:5555 -sTCP:LISTEN



#  运行单个手臂控制
1. 右手臂校准文件设置
    ```text
    cat /Users/jim/.cache/huggingface/lerobot/calibration/robots/so_follower/right_follower_arm.json > /Users/jim/.cache/huggingface/lerobot/calibration/robots/so_follower/None.json
    ```
2. 右手臂id: 
    ```text
    /dev/tty.usbmodem5B141120971
    ```
3. 运行右手臂
    ```text
    cd /Users/jim/lerobot/examples
    ./0_so100_keyboard_joint_control.py
    ```
# 联动控制单臂 
1. 右手臂校准文件设置
    ```text
    cat /Users/jim/.cache/huggingface/lerobot/calibration/robots/so_follower/right_follower_arm.json > /Users/jim/.cache/huggingface/lerobot/calibration/robots/so_follower/None.json
    ```
2. 右手臂id: 
    ```text
    /dev/tty.usbmodem5B141120971
    ```
3. 运行右手臂
    ```text
    cd /Users/jim/lerobot/examples
    ./1_so100_keyboard_ee_control.py 

# 运行键盘控制整个机器人
* 远程模式
  * host启动
    ```text
        PYTHONPATH=src python -m lerobot.robots.xlerobot_2wheels.xlerobot_2wheels_host --robot.id=my_xlerobot_2wheels_lab
    ```
  * client启动
    ```text
        PYTHONPATH=src python examples/4_xlerobot_2wheels_teleop_keyboard.py
    ```
    /dev/cu.usbmodem5B141120971
    /dev/cu.usbmodem5B141156081
    l /dev/tty.usbmodem5B141156081
    r /dev/tty.usbmodem5B141120971
* 本地模式 
  * 修改机器人配置
    ```text
        robot_config = XLerobot2WheelsConfig(id=robot_name)
        robot = XLerobot2Wheels(robot_config)
    ```
  *  启动
    ```text
        PYTHONPATH=src python examples/4_xlerobot_2wheels_teleop_keyboard.py
    ```

  

    Base Control (Differential Drive):
        u: Forward
        o: Backward
        i: Rotate Left
        k: Rotate Right
        n: Speed Up
        m: Speed Down
        b: Quit
        🚀 Smooth Control: Linear acceleration when holding, linear deceleration when released

    🦾 Left Arm Control:
    Joint Control:
        Q/E: Shoulder Pan +/- (shoulder_pan)
        R/F: Wrist Roll +/- (wrist_roll)
        T/G: Gripper +/- (gripper)
        Z/X: Pitch +/- (pitch)
    Position Control:
        W/S: X-axis +/- (x movement)
        A/D: Y-axis +/- (y movement)
    Special Functions:
        C: Reset to zero position
        Y: Execute rectangular trajectory

    🦾 Right Arm Control:
    Joint Control:
        7/9: Shoulder Pan +/- (shoulder_pan)
        /*: Wrist Roll +/- (wrist_roll)
        +/-: Gripper +/- (gripper)
        1/3: Pitch +/- (pitch)
    Position Control:46
        8/2: X-axis +/- (x movement)
        4/6: Y-axis +/- (y movement)
    Special Functions:222222222222466666d
        0: Reset to zero position
        Y: Execute rectangular trajectory

    👁️ Head Control:
        </>: Head Motor 1 +/- (head_motor_1)
        ,/.: Head Motor 2 +/- (head_motor_2)
        ?: Head reset to zero position

    ⚙️ Robot Configuration:
    Wheel Radius: 0.050m
    Wheelbase: 0.250m
    Speed Levels: 3 levels
        Level 1: Linear 0.1m/s, Angular 30°/s
        Level 2: Linear 0.2m/s, Angular 60°/s
        Level 3: Linear 0.3m/s, Angular 90°/s

    🚀 Smooth Control Parameters:
    Acceleration Rate: 10.0 speed/second
    Deceleration Rate: 10.0 speed/second
    Max Speed Multiplier: 6.0x
2. 运行joycon控制 
    PYTHONPATH=src python examples/7_xlerobot_2wheels_teleop_joycon_pygame.py

    # joycon 控制2轮机器人
    7_xlerobot_2wheels_teleop_joycon.py
    
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

3.  按键记录
R:
    X:2
    A:0
    B:1
    Y:3
    ZR:轴5
    R:10
    +:6
    右遥杠左右:轴2
    右遥杠上下:轴3
    主页:5
L:
    上:11
    下:12
    左:13
    右:14
    左摇杆上下移动:轴1
    左摇杆左右移动:轴0
    -:4
    ZL:轴4
    L:9
    ⭕️:15

# 采集前遥控测试
#lerobot-teleoperate
'''
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=right_arm \
  --robot.max_relative_target=15 \
  --teleop.type=joycon_so101 \
  --teleop.side=right \
  --teleop.id=my_joycon_right
'''

# 数据采集
```
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=right_arm \
  --robot.max_relative_target=15 \
  --robot.cameras="{ right: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 30, rotation: 90}}" \
  --teleop.type=joycon_so101 \
  --teleop.side=right \
  --teleop.id=my_joycon_right \
  --display_data=false \
  --play_sounds=false \
  --dataset.repo_id=jim1234321/pick_red_block \
  --dataset.single_task="Put the red block into your own basket" \
  --dataset.num_episodes=20 \
  --dataset.push_to_hub=false
```

```
python /your_dir/lerobot/src/lerobot/record.py \
  --robot.type=so101_follower \
  --robot.port=/dev/right_arm \
  --robot.id=robot_right_arm \
  --robot.cameras="{ head: {type: intelrealsense, serial_number_or_name: 935422072196, width: 640, height: 480, fps: 30, use_depth: True}, right: {type: opencv, index_or_path: '/dev/video6', width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=/dev/ttyACM0 \
  --teleop.id=my_leader_arm \
  --display_data=true \
  --dataset.repo_id=your_huggingface_id/clear_table_single_arm \
  --dataset.num_episodes=50 \
  --dataset.single_task="Clear the table"
```

20260507
```
xvfb-run lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=right_arm \
  --robot.cameras="{ head: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.0-usb-0:1:1.0-video-index0', width: 640, height: 480 , fps: 30},right: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 640, height: 480 , fps: 30}}" \
  --teleop.type=so101_leader \
  --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61034984-if00 \
  --teleop.id=leader_right_arm \
  --display_data=false \
  --play_sounds=false \
  --dataset.repo_id=jim1234321/pick_red_block \
  --dataset.single_task="Put the red block into your own basket" \
  --dataset.num_episodes=3 \
  --dataset.push_to_hub=false \ 
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2 \
  --dataset.vcodec=auto \
```

```
 xvfb-run lerobot-record   --robot.type=so101_follower   --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00   --robot.id=right_arm   --robot.cameras="{ head: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.0-usb-0:1:1.0-video-index0', width: 640, height: 480 , fps: 30},right: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 640, height: 480 , fps: 30}}"   --teleop.type=so101_leader   --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61034984-if00   --teleop.id=leader_right_arm   --display_data=false   --play_sounds=false   --dataset.repo_id=jim1234321/pick_red_block   --dataset.single_task="Put the red block into your own basket"   --dataset.num_episodes=5  --dataset.push_to_hub=false  --dataset.streaming_encoding=true  --dataset.encoder_threads=2  --dataset.vcodec=h264
 ```


# 模型训练
```
lerobot-train \
  --dataset.repo_id=jim1234321/pick_red_box \
  --dataset.root=/Users/jim/.cache/huggingface/lerobot/jim1234321/pick_red_box_20260606_162506 \
  --policy.type=act \
  --policy.repo_id=jim1234321/act_pick_red_box \
  --output_dir=outputs/train/act_pick_red_box \
  --job_name=act_pick_red_box \
  --policy.device=mps \
  --wandb.enable=false \
  --steps=2000
```
# 模型评估


# 模型加载测试

```python
import torch
from lerobot.configs import PreTrainedConfig
from lerobot.policies.factory import get_policy_class

model_path = "outputs/train/act_pick_red_box/checkpoints/last/pretrained_model"

print("=" * 60)
print("ACT 模型推理测试")
print("=" * 60)

config = PreTrainedConfig.from_pretrained(model_path)
print(f"\n📋 策略类型: {config.type}")
print(f"📋 设备: {config.device}")

print(f"\n📥 输入特征 (模型需要的观测数据):")
for name, feat in config.input_features.items():
    print(f"   - {name}: shape={feat.shape}, type={feat.type}")

print(f"\n📤 输出特征 (模型输出的动作):")
for name, feat in config.output_features.items():
    print(f"   - {name}: shape={feat.shape}, type={feat.type}")

print("\n⏳ 加载模型权重...")
policy_class = get_policy_class(config.type)
policy = policy_class.from_pretrained(model_path, config=config)
policy.eval()
policy.reset()

params = sum(p.numel() for p in policy.parameters())
print(f"✅ 模型加载成功！参数量: {params:,}")

batch = {}
for name, feat in config.input_features.items():
    batch[name] = torch.zeros(1, *feat.shape)

print(f"\n🔧 Dummy 输入 (batch):")
for k, v in batch.items():
    print(f"   {k}: tensor shape={list(v.shape)}, dtype={v.dtype}")

print("\n🧠 运行推理 (predict_action_chunk)...")
with torch.no_grad():
    action_chunk = policy.predict_action_chunk(batch)

print(f"\n📊 推理输出 (action chunk):")
print(f"   shape: {list(action_chunk.shape)}")
print(f"   dtype: {action_chunk.dtype}")
print(f"   值范围: [{action_chunk.min().item():.4f}, {action_chunk.max().item():.4f}]")
print(f"   均值: {action_chunk.mean().item():.6f}")
print(f"   标准差: {action_chunk.std().item():.6f}")

print(f"\n📊 前3个 action step 的具体数值:")
for i in range(min(3, action_chunk.shape[1])):
    step = action_chunk[0, i]
    print(f"   Step {i}: {step.tolist()}")

policy.reset()
print(f"\n🧠 运行 select_action (单步动作)...")
with torch.no_grad():
    action = policy.select_action(batch)

print(f"\n📊 单步动作输出:")
print(f"   shape: {list(action.shape)}")
print(f"   值: {action.tolist()}")

if hasattr(config, 'output_features'):
    for name, feat in config.output_features.items():
        if hasattr(feat, 'names') and feat.names:
            print(f"\n📋 动作维度名称 ({name}):")
            for idx, n in enumerate(feat.names):
                val = action[idx].item() if idx < action.shape[0] else "N/A"
                print(f"   [{idx}] {n}: {val:.4f}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
```

# 模型推理运行
  基础版本（推荐用于测试）：

lerobot-rollout \
  --strategy.type=base \
  --policy.path=/home/jim/AiSpace/models/pretrained_model/ \
  --robot.type=so101_follower \
  --robot.id=right_arm \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 30, rotation: 90}}" \
  --policy.device=cpu \
  --task="Pick the red box into the green tray" \
  --duration=60 \
  --fps=30


lerobot-rollout \
  --strategy.type=base \
  --policy.path=/home/jim/AiSpace/models/pretrained_model/ \
  --robot.type=so101_follower \
  --robot.id=right_arm \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 10, rotation: 90}}" \
  --policy.device=cpu \
  --task="Pick the red box into the green tray" \
  --duration=60 \
  --fps=10
  
---
性能优化版本（Pi5 推荐）

如果推理速度不足或内存不足，使用 FP16 + RTC（实时分块）推理：

lerobot-rollout \
  --strategy.type=base \
  --policy.path=/home/jim/AiSpace/models/pretrained_model/ \
  --inference.type=rtc \
  --inference.rtc.execution_horizon=10 \
  --robot.type=so101_follower \
  --robot.id=right_arm \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 30, rotation: 90}}" \
  --policy.device=cpu \
  --task="Pick the red box into the green tray" \
  --duration=60 \
  --use_torch_compile=true


lerobot-rollout \
  --strategy.type=base \
  --policy.path=/home/jim/AiSpace/models/pretrained_model/ \
  --inference.type=rtc \
  --inference.rtc.execution_horizon=5 \
  --inference.rtc.max_guidance_weight=5.0 \
  --robot.type=so101_follower \
  --robot.id=right_arm \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 15, rotation: 90}}" \
  --policy.device=cpu \
  --task="Pick the red box into the green tray" \
  --duration=60 \
  --fps=15 \
  --use_torch_compile=true

---
数据记录版本（推荐用于收集更多数据）

边推理边保存数据：

lerobot-rollout \
  --strategy.type=sentry \
  --strategy.upload_every_n_episodes=1 \
  --policy.path=/home/pi/lerobot_models/act_pick_red_box \
  --robot.type=so101_follower \
  --robot.id=right_arm \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 30, rotation: 90}}" \
  --policy.device=cpu \
  --dataset.repo_id=jim1234321/pick_red_box_rollout \
  --dataset.single_task="Pick the red box into the green tray" \
  --duration=600

---
常见调整

┌────────────────────┬───────────────────────────────────────────────────────┐
│        问题        │                       解决方案                        │
├────────────────────┼───────────────────────────────────────────────────────┤
│ 摄像头路径改变     │ 在 Pi5 上运行 ls /dev/v4l/by-path/ 确认路径           │
├────────────────────┼───────────────────────────────────────────────────────┤
│ 推理过慢（>1s/帧） │ 加 --inference.type=rtc 和 --use_torch_compile=true   │
├────────────────────┼───────────────────────────────────────────────────────┤
│ 内存不足           │ 减少 --fps 或使用 --inference.rtc.execution_horizon=5 │
├────────────────────┼───────────────────────────────────────────────────────┤
│ 串口找不到         │ 运行 ls /dev/serial/by-id/ 确认端口                   │
└────────────────────┴───────────────────────────────────────────────────────┘

---
验证步骤

在 Pi5 上先做快速测试：

# 1. 确认设备连接
ls /dev/serial/by-id/usb-1a86*  # 检查机器人端口
ls /dev/v4l/by-path/            # 检查摄像头

# 2. 测试摄像头
python -c "import cv2; cap = cv2.VideoCapture('/dev/v4l/by-path/platform-xhci-hc0'); print('OK' if cap.isOpened() else 'FAIL')"

# 3. 运行推理（开始时用 --duration=30 短时间测试）
lerobot-rollout ... --duration=30




#lerobot-calibrate 
## so101_follower
 lerobot-calibrate --robot.type=so101_follower --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14115608-if00 --robot.id=left_arm

## so101_leader
 lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61034984-if00 --teleop.id=leader_right_arm
 lerobot-calibrate --teleop.type=so101_leader --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61033431-if00 --teleop.id=leader_left_arm

## right
 lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
    --robot.id=right_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61034984-if00 \
    --teleop.id=leader_right_arm

## left
lerobot-teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14115608-if00 \
    --robot.id=left_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B61033431-if00 \
    --teleop.id=leader_left_arm