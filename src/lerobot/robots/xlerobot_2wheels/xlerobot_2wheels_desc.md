# `4_xlerobot_2wheels_teleop_keyboard.py` 代码说明

`examples/4_xlerobot_2wheels_teleop_keyboard.py` 是一个用键盘遥控 XLeRobot 两轮版机器人的示例脚本。

它控制的不是单一底盘，而是整台机器人：

- 两轮差速底盘：前进、后退、原地旋转
- 左机械臂
- 右机械臂
- 头部两个电机
- Rerun 可视化中的观测和动作记录

## 运行方式

文件开头给了两段运行说明。

启动机器人硬件端 host：

```bash
PYTHONPATH=src python -m lerobot.robots.xlerobot_2wheels.xlerobot_2wheels_host --robot.id=my_xlerobot_2wheels
```

启动键盘遥控端：

```bash
PYTHONPATH=src python -m examples.xlerobot_2wheels.teleoperate_Keyboard
```

注意：当前打开的示例文件路径是：

```text
examples/4_xlerobot_2wheels_teleop_keyboard.py
```

而运行说明里的模块名是：

```text
examples.xlerobot_2wheels.teleoperate_Keyboard
```

这两者不完全一致，实际运行前需要确认仓库里是否存在对应模块。

## 按键映射

`LEFT_KEYMAP` 和 `RIGHT_KEYMAP` 定义键盘按键到语义动作的映射。

左臂主要按键：

```text
Q/E: shoulder_pan +/-
R/F: wrist_roll +/-
T/G: gripper +/-
W/S: x 方向移动
A/D: y 方向移动
Z/X: pitch +/-
C: 左臂回零
Y: 执行矩形轨迹
</>, ,/.: 头部电机控制
```

右臂主要按键：

```text
7/9: shoulder_pan +/-
/ 和 *: wrist_roll +/-
+/-: gripper +/-
8/2: x 方向移动
4/6: y 方向移动
1/3: pitch +/-
0: 右臂回零
Y: 执行矩形轨迹
```

底盘按键来自机器人配置里的 `robot.teleop_keys`，用于控制：

```text
x.vel: 前进/后退线速度
theta.vel: 左转/右转角速度
```

## 核心类

### `RectangularTrajectory`

`RectangularTrajectory` 是一个矩形轨迹生成器。

它会在 x-y 平面生成一个矩形轨迹，让机械臂末端沿矩形四条边运动。每条边使用余弦平滑函数做加减速，所以目标点变化不是突变的。

主要参数：

- `width`: 矩形宽度
- `height`: 矩形高度
- `segment_duration`: 每条边的运动时间

核心方法：

```python
get_trajectory_point(current_x, current_y, t)
```

它根据当前时间 `t` 返回此刻目标末端位置：

```python
(target_x, target_y)
```

### `SimpleTeleopArm`

`SimpleTeleopArm` 是机械臂键盘控制类。

它负责：

- 保存当前机械臂目标关节角度
- 根据键盘增减 `shoulder_pan`、`wrist_roll`、`gripper`、`pitch`
- 根据 `x/y` 方向移动更新末端目标位置
- 调用 `SO101Kinematics.inverse_kinematics()` 做逆运动学
- 把末端位置转换为 `shoulder_lift` 和 `elbow_flex`
- 使用简单 P 控制生成动作

P 控制的核心形式是：

```python
error = target - current
control = kp * error
action = current + control
```

也就是说，它不是一次性把电机强行设置到目标角度，而是根据当前观测逐步靠近目标。

### `SimpleHeadControl`

`SimpleHeadControl` 控制头部两个电机：

```text
head_motor_1
head_motor_2
```

它同样使用 P 控制，让头部电机逐步靠近目标位置。

支持的功能包括：

- 增减头部电机目标角度
- 头部回零
- 根据当前观测生成头部动作

### `SmoothBaseController`

`SmoothBaseController` 是底盘平滑控制器。

它让底盘控制不是一按键就满速、一松键就立刻停止，而是：

- 按住方向键时线性加速
- 松开方向键时线性减速
- 根据机器人当前速度档位生成底盘速度命令

生成的底盘 action 主要包括：

```python
{
    "x.vel": ...,
    "theta.vel": ...,
}
```

其中：

- `x.vel` 控制前进和后退
- `theta.vel` 控制左转和右转

## `main()` 主流程

`main()` 是整个遥控程序的入口。

主要流程如下：

1. 设置控制频率：

   ```python
   FPS = 50
   ```

2. 设置连接方式。

   代码里目前启用的是本地有线连接：

   ```python
   robot_config = XLerobot2WheelsConfig(id=robot_name)
   robot = XLerobot2Wheels(robot_config)
   ```

   ZMQ 远程连接方式被注释掉了：

   ```python
   # robot_config = XLerobot2WheelsClientConfig(remote_ip=ip, id=robot_name)
   # robot = XLerobot2WheelsClient(robot_config)
   ```

3. 连接机器人：

   ```python
   robot.connect()
   ```

4. 初始化 Rerun 可视化：

   ```python
   init_rerun(session_name="xlerobot_2wheels_teleop")
   ```

5. 初始化键盘监听：

   ```python
   keyboard = KeyboardTeleop(keyboard_config)
   keyboard.connect()
   ```

6. 获取初始观测，并创建左右臂和头部控制器：

   ```python
   obs = robot.get_observation()
   left_arm = SimpleTeleopArm(...)
   right_arm = SimpleTeleopArm(...)
   head_control = SimpleHeadControl(obs)
   ```

7. 启动时让左右臂回零：

   ```python
   left_arm.move_to_zero_position(robot)
   right_arm.move_to_zero_position(robot)
   ```

8. 进入无限循环，持续读取键盘输入并发送动作：

   ```python
   pressed_keys = set(keyboard.get_action().keys())
   ```

   循环里会依次处理：

   - 左臂矩形轨迹
   - 右臂矩形轨迹
   - 左臂回零
   - 右臂回零
   - 头部回零
   - 左右臂普通按键控制
   - 头部按键控制
   - 底盘平滑速度控制

9. 合并所有动作：

   ```python
   action = {**left_action, **right_action, **head_action, **base_action}
   ```

10. 发送动作给机器人：

    ```python
    robot.send_action(action)
    ```

11. 获取观测并记录到 Rerun：

    ```python
    obs = robot.get_observation()
    log_rerun_data(obs, action)
    ```

12. 程序退出时断开连接：

    ```python
    robot.disconnect()
    keyboard.disconnect()
    ```

## 总结

这个文件是一个键盘实时遥控程序。

它把键盘输入转换成：

- 底盘速度命令
- 左机械臂目标动作
- 右机械臂目标动作
- 头部电机目标动作

然后不断发送给 `XLerobot2Wheels` 机器人，并同步记录观测和动作到 Rerun 里用于可视化。
