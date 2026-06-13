# Joy-Con 遥操作 + 数据录制操作说明(单臂 SO-101)

用一只**右 Joy-Con** 控制 SO-101 follower 单臂,通过 `lerobot-record` 录制数据集。
机械臂采用**解耦轴控制**(摇杆/按键各管一个方向,互不干扰);录制流程(切换/重录/停止)用**键盘**。

> 说明:没有沿用 `7_xlerobot_2wheels_teleop_joycon.py` 的「枪口指向(俯仰投影)」映射——那种映射会在手腕俯仰到 ~90° 时让前后摇杆失效、推过头还回不来,不适合录制。这里把各轴解耦,并给末端位置加了边界,更直觉、可控。

---

## 0. 准备

1. 蓝牙配对右 Joy-Con,按一下任意键唤醒(闲置会休眠掉线)。
2. 确认手柄被识别:`ls /dev/input/js*` 有设备节点即可。
3. 机械臂已标定(标定文件对应 `--robot.id`)。

> Joy-Con 没连上时,启动会直接提示 `No right Joy-Con detected ...`——先唤醒手柄再重试。

---

## 1. 控制布局(右 Joy-Con → 机械臂)

| 输入 | 作用 |
|------|------|
| **摇杆 上/下** | 末端 X 方向(前后伸够),解耦,不受手腕俯仰影响 |
| **摇杆 左/右** | 末端 Y 方向 → 肩部旋转 `shoulder_pan` |
| **R 键** | 末端 Z 上升 |
| **按下摇杆**(摇杆按键) | 末端 Z 下降 |
| **倾斜手柄(roll)** | 手腕翻转 `wrist_roll` |
| **倾斜手柄(pitch)** | 手腕俯仰 `wrist_flex` |
| **ZR 键** | **夹爪**:按住持续开/合;**每按一次翻转方向**(开↔合) |
| **Home 键** | 末端复位到初始静止姿态 |
| **+ 键** | 重置 Joy-Con 姿态参考(漂移时用) |

> 末端位置有边界(见调参表 `pos_*`),推到工作空间边缘会停住,但**松杆/反推立即回来**,不会出现「推过头回不来」。

> A / B / X / Y 面键在单臂录制里**不参与控制**(它们在原 2wheels 脚本里是驱动轮式底盘的,本场景没有底盘)。录制切换请用键盘。

启动瞬间:机械臂会平缓移动到 Joy-Con 对应的初始姿态。已用 `--robot.max_relative_target=15` 限速,但**第一次务必把手放在急停/电源旁**。

---

## 2. 录制流程控制(键盘)

> 需在**有桌面环境**的机器上(pynput 全局监听,焦点不必在终端;纯 SSH 无显示则键盘无效)。

| 按键 | 作用 |
|------|------|
| `→` 右箭头 | 当前 episode 录够了 → 保存,进入下一条 |
| `←` 左箭头 | 当前 episode 录砸了 → 丢弃并重录 |
| `Esc` | 提前结束整个录制 |

录满 `--dataset.num_episodes` 或按 `Esc` 后自动保存,并(默认)上传 HF Hub。

---

## 3. 命令

### 3.1 先纯遥操测试(不带相机/数据集)

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=right_arm \
  --robot.max_relative_target=15 \
  --teleop.type=joycon_so101 \
  --teleop.side=right \
  --teleop.id=my_joycon_right
```

确认:摇杆控臂方向正常、ZR 能开合夹爪、无漂移。`Ctrl+C` 退出。

### 3.2 加相机再测

在上面命令基础上加:

```bash
  --robot.cameras="{ head: {type: intelrealsense, serial_number_or_name: 935422072196, width: 640, height: 480, fps: 30, use_depth: True}, right: {type: opencv, index_or_path: '/dev/video6', width: 640, height: 480, fps: 30}}" \
  --display_data=true
```

确认 rerun 窗口里两路相机画面正常。

### 3.3 正式录制

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=robot_right_arm \
  --robot.max_relative_target=15 \
  --robot.cameras="{ head: {type: intelrealsense, serial_number_or_name: 935422072196, width: 640, height: 480, fps: 30, use_depth: True}, right: {type: opencv, index_or_path: '/dev/video6', width: 640, height: 480, fps: 30}}" \
  --teleop.type=joycon_so101 \
  --teleop.side=right \
  --teleop.id=my_joycon_right \
  --display_data=true \
  --dataset.repo_id=你的HF_ID/clear_table_single_arm \
  --dataset.num_episodes=50 \
  --dataset.single_task="Clear the table"
```

### 3.4 暂存本地
```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port=/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B14112097-if00 \
  --robot.id=right_arm \
  --robot.max_relative_target=15 \
  --robot.cameras="{ wrist: {type: opencv, index_or_path: '/dev/v4l/by-path/platform-xhci-hcd.1-usb-0:1.2:1.0-video-index0', width: 480, height: 640, fps: 30, rotation: 90}}" \
  --teleop.type=joycon_so101 \
  --teleop.side=right \
  --teleop.id=my_joycon_right \
  --display_data=false \
  --play_sounds=false \
  --dataset.repo_id=jim1234321/pick_red_box \
  --dataset.single_task="Pick the red box into the green tray" \
  --dataset.num_episodes=1 \
  --dataset.push_to_hub=false
```

### 3.5 push to hub
```python
python - <<'PY'
from lerobot.datasets.lerobot_dataset import LeRobotDataset
root = "/home/jim/.cache/huggingface/lerobot/jim1234321/pick_red_box_20260605_225103"
ds = LeRobotDataset("jim1234321/pick_red_box", root=root)
ds.push_to_hub()   # 默认公开;要私有传 private=True
print("pushed:", ds.repo_id)
PY                       
```


---

## 4. 调参(`--teleop.*`)

| 参数 | 默认 | 说明 |
|------|------|------|
| `--teleop.side` | right | 用左/右 Joy-Con |
| `--teleop.speed_scale` | 0.0008 | 摇杆/按键位移步长;大=移动快 |
| `--teleop.pos_x_min` / `pos_x_max` | -0.09 / 0.07 | X(前后)行程边界 |
| `--teleop.pos_y_min` / `pos_y_max` | -0.30 / 0.30 | Y(肩转)行程边界 |
| `--teleop.pos_z_min` / `pos_z_max` | -0.10 / 0.10 | Z(高低)行程边界 |
| `--teleop.pan_scale` | 250.0 | 摇杆横向→肩转幅度 |
| `--teleop.roll_scale` | 45.0 | roll→腕翻 |
| `--teleop.pitch_scale` / `pitch_bias` | 60 / 10 | 俯仰→腕俯仰映射 |
| `--teleop.gripper_speed` | 0.4 | 夹爪开合速度 |
| `--teleop.gripper_min` / `gripper_max` | 0 / 90 | 夹爪行程 |
| `--robot.max_relative_target` | — | 每帧关节限速:大=更跟手但更冲,小=更稳 |

> 推到边界太早(够不到目标)就调大对应 `pos_*` 边界;移动太快/太慢调 `speed_scale`。

方向反了(左右/前后相反)或漂移,先调上面参数;若需整体反向,告知后我加方向开关。

---

## 5. 训练衔接

数据集格式由**机器人**决定(与 teleop 无关),所以 Joy-Con 录的数据集和 leader 臂录的完全一致,官方教程训练步骤原样适用:

```bash
lerobot-train \
  --dataset.repo_id=你的HF_ID/clear_table_single_arm \
  --policy.type=act \
  --output_dir=outputs/train/act_clear_table \
  --job_name=act_clear_table \
  --policy.device=cuda \
  --wandb.enable=true
```

评估/部署阶段**不需要 Joy-Con**——策略直接输出关节位置。Joy-Con 仅用于录制。


## 6. 本地训练数据训练
```bash
lerobot-train \
  --dataset.repo_id=jim1234321/pick_red_box \
  --dataset.root=/Users/jim/.cache/huggingface/lerobot/jim1234321/pick_red_box_20260606_162506 \
  --policy.type=act \
  --output_dir=outputs/train/act_pick_red_box \
  --job_name=act_pick_red_box \
  --policy.device=cpu \
  --wandb.enable=false
- --dataset.root=... 是关键,有它就不下载。repo_id 此时只当标识用。
- --wandb.enable=false 避免再联网。
```