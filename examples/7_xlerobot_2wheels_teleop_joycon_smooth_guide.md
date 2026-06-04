# XLeRobot 2Wheels — Joy-Con 丝滑遥操作 操作说明

对应脚本:[`7_xlerobot_2wheels_teleop_joycon_smooth.py`](./7_xlerobot_2wheels_teleop_joycon_smooth.py)

整机由两条 Feetech 总线组成,通过两个串口连接:

| 端口 | 总线上的设备 | 默认路径(`config_xlerobot_2wheels.py`) |
| --- | --- | --- |
| `port1` | so101 头部臂 + 头部相机 | `usb-1a86_USB_Single_Serial_5B14115608-if00` |
| `port2` | 左右机械臂 + 两个驱动轮 | `usb-1a86_USB_Single_Serial_5B14112097-if00` |

脚本里 `robot.id` 硬编码为 `my_xlerobot_2wheels_lab`,校准文件按这个 id 存取。

---

## 1. 上电前检查(最重要)

> 之前 `lerobot-calibrate` 报 `Full found motor list: {}`(一个电机都没扫到),99% 是下面前两条没满足。

1. **舵机外部电源已接通, 确认舵机灯已亮**。Feetech STS3215 必须接独立电源(7.4V/12V),USB 线只给控制板逻辑供电,**不给舵机供电**。电源没开 → 串口能打开但扫不到任何电机。
2. **两个串口都已连接**,且对应关系正确(见上表)。串口权限:当前用户需在 `dialout` 组(已确认满足)。
3. **两个 Joy-Con 已通过蓝牙连接**到主机。
4. 机器人放在**安全空旷**位置,首次运行手臂会自动回到 zero position。

确认串口设备:

```bash
ls -l /dev/serial/by-id/        # 推荐:by-id 路径不会随插拔顺序变化
ls -l /dev/ttyACM*              # 备用:ACM 编号会变,不要写死在脚本里
```

---

## 2. 校准(首次或更换电机后)

整机校准,注意端口要用 `by-id` 路径(按实际替换):

```bash
lerobot-calibrate \
  --robot.type=xlerobot_2wheels \
  --robot.id=my_xlerobot_2wheels_lab \
  --robot.port1=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14115608-if00 \
  --robot.port2=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00
```

> 如果只想单独校准某条 so101 单臂,可用 `--robot.type=so101_follower --robot.port=<对应端口>`;此时 **port 必须对应那条臂所在的总线**,否则就会出现 `found {}`。

校准数据会按 `robot.id` 缓存,之后再次启动无需重复校准。

---

## 3. 启动遥操作

脚本默认是**本地直连**模式(直接驱动两个串口),所以**不需要**先跑 host:

```bash
cd /home/jim/AiSpace/lerobot
PYTHONPATH=src python examples/7_xlerobot_2wheels_teleop_joycon_smooth.py
```

启动后会:
1. 连接机器人并打印是否已校准;
2. 初始化左右 Joy-Con;
3. 左右臂 + 头部自动回到 zero position;
4. 打印控制说明,进入遥操作循环。

> 远程/分体运行(可选):若要主机与机器人分离,可改用脚本顶部注释的 host + zmq client 方式 —— 在机器人端跑
> `PYTHONPATH=src python -m lerobot.robots.xlerobot_2wheels.xlerobot_2wheels_host --robot.id=my_xlerobot_2wheels_lab`,
> 并在脚本 `main()` 里改用被注释掉的 `XLerobot2WheelsClient`。默认就用本地直连即可。

退出:`Ctrl+C`。脚本会在 `finally` 中断开 Joy-Con 和机器人(`disable_torque_on_disconnect=True`,断开时会松力)。

---

## 4. Joy-Con 控制映射

### 🚗 底盘(差速驱动)— 右 Joy-Con
| 按键 | 动作 |
| --- | --- |
| `Y` | 前进 Forward |
| `A` | 后退 Backward |
| `X` | 左转 Rotate Left |
| `B` | 右转 Rotate Right |

按住线性加速到上限,松开线性减速到 0(平滑控制)。

### 🦾 右臂 — 右 Joy-Con
| 操作 | 动作 |
| --- | --- |
| 右摇杆 上/下 | 末端 X / Z 轴(前后伸缩) |
| 右摇杆 左/右 | 末端 Y 轴(左右,同时驱动 `shoulder_pan`) |
| `R` | Z 轴上升 |
| 右摇杆按下 | Z 轴下降 |
| `ZR` | 夹爪:按一下切换开/合方向,**按住**连续开合 |
| 倾斜手柄 | pitch → `wrist_flex`,roll → `wrist_roll` |
| `+`(Plus) | 重置 Joy-Con 原点,并触发**全部回 zero position** |

### 🦾 左臂 — 左 Joy-Con
| 操作 | 动作 |
| --- | --- |
| 左摇杆 上/下 | 末端 X / Z 轴 |
| 左摇杆 左/右 | 末端 Y 轴(同时驱动 `shoulder_pan`) |
| `L` | Z 轴上升 |
| 左摇杆按下 | Z 轴下降 |
| `ZL` | 夹爪:按一下切换方向,按住连续开合 |
| 倾斜手柄 | pitch / roll → 手腕 |
| `−`(Minus) | 重置 Joy-Con 原点 |

### 👁️ 头部 — 左 Joy-Con 方向键(D-pad)
| 按键 | 动作 |
| --- | --- |
| 上 / 下 | `head_motor_2` +/− |
| 左 / 右 | `head_motor_1` +/− |

---

## 5. 可调参数(脚本顶部 / 参数区)

### 动作幅度(走多远,range of motion)
```python
ARM_MOTION_SCALE  = 0.5   # shoulder_pan/lift/elbow_flex 幅度;1.0=原始,0.5=减半
HEAD_MOTION_SCALE = 0.8   # 头部每步幅度;1.0=原始,0.8=下降 20%
```
`shoulder_lift / elbow_flex` 是**相对 neutral pose 缩放偏移**,缩小幅度不会移动中性点。

### 手臂平滑(走多快/多顺,velocity-limited slew-rate)
```python
ARM_ACCELERATION_RATE = 300.0  # °/s^2,越大启动越猛
ARM_DECELERATION_RATE = 400.0  # °/s^2,越大越不容易过冲(overshoot)
ARM_MAX_SPEED         = 120.0  # °/s,这三个关节的最高速度
ARM_MAX_DT            = 0.1    # 限制单帧 dt,防止卡顿造成跳变
ENABLE_ARM_SMOOTH_CONTROL = True  # False 则退回原始 P-control
```

### 底盘平滑
```python
BASE_ACCELERATION_RATE = 10.0  # 加速斜率
BASE_DECELERATION_RATE = 10.0  # 减速斜率
BASE_MAX_SPEED         = 5.0   # 最大速度倍率
MIN_VELOCITY_THRESHOLD = 0.02  # 减速末段最小速度,防止电机过早截止
```

> 幅度参数(`*_MOTION_SCALE`)和速度参数(`ARM_MAX_SPEED` 等)**相互独立**:一个管"走多远",一个管"走多快/多顺"。

其它常见微调点:
- `y_scale = 250.0`(`handle_joycon_input` 内):`shoulder_pan` 对摇杆水平量的灵敏度。
- `joycon_stick_v_0 / joycon_stick_h_0`(`FixedAxesJoyconRobotics.__init__`):摇杆中心值,若静止时末端会漂移就调这里。
- `gripper_speed = 0.4`:夹爪开合速度。

---

## 6. 常见问题

| 现象 | 排查 |
| --- | --- |
| `Full found motor list: {}`(扫不到电机) | ① 舵机外部电源没开;② 端口选错(port1/port2 接反或写成了别的 ACM);③ 总线排线没插好 |
| 报错打不开端口 / Permission denied | 用户不在 `dialout` 组,或端口被其它进程占用 |
| Joy-Con 无反应 | 蓝牙未配对;先在系统蓝牙里连上两个手柄再启动脚本 |
| 静止时末端缓慢漂移 | 调整 `joycon_stick_v_0 / joycon_stick_h_0` 中心值,或加大摇杆 `threshold` |
| 三个关节动作太小/太大 | 改 `ARM_MOTION_SCALE` |
| 头部动作太小/太大 | 改 `HEAD_MOTION_SCALE` |
| 手臂动作发抖/过冲 | 降低 `ARM_MAX_SPEED` 或提高 `ARM_DECELERATION_RATE` |
| 不确定哪个端口对应哪条总线 | `lerobot-find-port`(按提示拔插一条线即可识别) |
```
