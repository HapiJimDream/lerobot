


# 机器人情况
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
    Special Functions:
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

