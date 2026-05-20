# 4_xlerobot_2wheels_teleop_keyboard.py 说明

`4_xlerobot_2wheels_teleop_keyboard.py` 是一个键盘遥操作示例脚本。它不是机器人底层驱动，而是一个上层应用：读取键盘输入，把按键转换成左右机械臂、头部和 2 轮差速底盘的 action，然后调用机器人对象的 `send_action()` 发给机器人。

## 和 xlerobot_2wheels 目录的关系

```text
4_xlerobot_2wheels_teleop_keyboard.py
  |
  | 创建 robot 对象
  v
XLerobot2Wheels 或 XLerobot2WheelsClient
  |
  | send_action(action)
  | get_observation()
  v
真实机器人 / 远程 host
```

当前脚本里实际启用的是本地直连模式：

```python
robot_config = XLerobot2WheelsConfig(id=robot_name)
robot = XLerobot2Wheels(robot_config)
```

也就是直接使用 `xlerobot_2wheels.py` 里的真实机器人类，直接连接串口、电机和摄像头。

脚本里也预留了 ZMQ 远程模式，但默认被注释掉：

```python
# robot_config = XLerobot2WheelsClientConfig(remote_ip=ip, id=robot_name)
# robot = XLerobot2WheelsClient(robot_config)
```

如果改用这两行，它会通过 `xlerobot_2wheels_client.py` 连接机器人端的 `xlerobot_2wheels_host.py`。

## 脚本主要流程

1. 初始化键盘监听：

```python
keyboard = KeyboardTeleop(keyboard_config)
keyboard.connect()
```

2. 连接机器人：

```python
robot.connect()
```

3. 读取一次当前机器人状态：

```python
obs = robot.get_observation()
```

4. 创建左臂、右臂和头部控制器：

```python
left_arm = SimpleTeleopArm(...)
right_arm = SimpleTeleopArm(...)
head_control = SimpleHeadControl(obs)
```

5. 主循环里不断读取键盘：

```python
pressed_keys = set(keyboard.get_action().keys())
```

6. 把键盘状态转换成 action：

```python
left_action = left_arm.p_control_action(robot)
right_action = right_arm.p_control_action(robot)
head_action = head_control.p_control_action(robot)
base_action = smooth_controller.update(pressed_keys, robot)

action = {**left_action, **right_action, **head_action, **base_action}
robot.send_action(action)
```

7. 再读取观测并记录到 rerun 可视化：

```python
obs = robot.get_observation()
log_rerun_data(obs, action)
```

## 控制内容

### 左臂

左臂按键定义在 `LEFT_KEYMAP`：

- `q/e`: 左肩 yaw
- `r/f`: 左腕 roll
- `t/g`: 左夹爪
- `w/s/a/d`: 左臂末端在 x/y 平面移动，内部用 `SO101Kinematics.inverse_kinematics()`
- `z/x`: pitchc
- `c`: 左臂归零
- `y`: 左臂矩形轨迹

### 右臂

右臂按键定义在 `RIGHT_KEYMAP`：

- `7/9`: 右肩 yaw
- `/*`: 右腕 roll
- `+/-`: 右夹爪
- `8/2/4/6`: 右臂末端在 x/y 平面移动
- `1/3`: pitch
- `0`: 右臂归零
- `Y`: 右臂矩形轨迹

### 头部

头部控制复用左侧 keymap：

- `</>`: `head_motor_1` 加减
- `,/.`: `head_motor_2` 加减
- `?`: 头部归零

### 底盘

底盘按键来自机器人配置里的 `robot.teleop_keys`：

- `i`: 前进
- `k`: 后退
- `u`: 左转
- `o`: 右转
- `n/m`: 速度档位

底盘动作最终生成：

```python
{"x.vel": ..., "theta.vel": ...}
```

这些值进入 `XLerobot2Wheels.send_action()` 后，会由 `_body_to_wheel_raw()` 转换成左右轮速度，再写入底盘电机。

## 总结

`xlerobot_2wheels.py` 提供底层机器人能力，`config_xlerobot_2wheels.py` 提供配置，`xlerobot_2wheels_host.py` 和 `xlerobot_2wheels_client.py` 提供远程通信。

`4_xlerobot_2wheels_teleop_keyboard.py` 是上层键盘遥操作入口：它把键盘输入变成 action，再通过本地 `XLerobot2Wheels` 或远程 `XLerobot2WheelsClient` 控制机器人。
