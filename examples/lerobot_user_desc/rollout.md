# lerobot-rollout 命令参数详解

`lerobot-rollout` 是 LeRobot 中用于在真实机器人上部署训练好的策略的统一 CLI 工具。它支持多种执行策略和推理后端，适用于快速评估、持续录制、高亮片段保存以及人机协作数据采集等场景。

## 基本用法

```bash
lerobot-rollout \
    --strategy.type=base \
    --policy.path=<模型路径或HF repo_id> \
    --robot.type=<机器人类型> \
    --robot.port=<串口路径> \
    --task="任务描述" \
    --duration=30
```

---

## 一、顶层参数（RolloutConfig）

### 1.1 硬件配置

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|------|------|--------|------|------|
| `--robot.type` | str | None | **是** | 机器人类型，通过 draccus ChoiceRegistry 注册。可选值见下方列表 |
| `--robot.port` | str | — | 视机器人而定 | 串口路径（如 `/dev/ttyACM0`），部分机器人需要 |
| `--robot.id` | str | None | 否 | 机器人实例 ID，用于区分同类型的多台机器人，加载校准文件时使用 |
| `--robot.calibration_dir` | Path | None | 否 | 校准文件存储目录 |
| `--robot.cameras` | dict | — | 视情况 | 摄像头配置字典，格式为 `"{ 名称: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"` |
| `--teleop.type` | str | None | DAgger 必填 | 遥操作器类型，DAgger 策略必须设置此参数 |
| `--teleop.id` | str | None | 否 | 遥操作器实例 ID |
| `--teleop.calibration_dir` | Path | None | 否 | 遥操作器校准文件目录 |

**支持的 `--robot.type` 值：**
`so100_follower`、`so101_follower`、`koch_follower`、`openarm_follower`、`bi_openarm_follower`、`bi_so_follower`、`omx_follower`、`reachy2`、`xlerobot`、`xlerobot_client`、`xlerobot_2wheels`、`xlerobot_2wheels_client`、`lekiwi`、`lekiwi_client`、`earthrover_mini_plus`、`hope_jr_hand`、`hope_jr_arm`、`unitree_g1`

**支持的 `--teleop.type` 值：**
`so100_leader`、`so101_leader`、`koch_leader`、`openarm_leader`、`openarm_mini`、`bi_openarm_leader`、`bi_so_leader`、`omx_leader`、`reachy2_teleoperator`、`homunculus_glove`、`homunculus_arm`、`unitree_g1`、`keyboard`、`keyboard_ee`、`keyboard_rover`、`gamepad`、`phone`

---

### 1.2 策略配置（--strategy.*）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy.type` | str | `base` | 选择执行策略。可选值：`base`、`sentry`、`highlight`、`dagger` |

各策略的详细参数见下文"策略详解"章节。

---

### 1.3 推理后端配置（--inference.*）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--inference.type` | str | `sync` | 推理后端类型。可选值：`sync`（同步推理，每个控制 tick 调用一次策略）、`rtc`（Real-Time Chunking，适用于慢速 VLA 模型） |

各推理后端的详细参数见下文"推理后端详解"章节。

---

### 1.4 策略模型配置（--policy.*）

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|------|------|--------|------|------|
| `--policy.path` | str | None | **是** | 预训练策略的路径。可以是 HuggingFace Hub 的 repo_id（如 `lerobot/act_koch_real`）或本地目录路径（如 `outputs/train/.../pretrained_model`） |
| `--policy.device` | str | None | 否 | 推理设备，如 `cuda`、`cuda:0`、`cpu`、`mps`。不设时自动从策略配置中读取或自动检测 |
| `--policy.use_amp` | bool | False | 否 | 是否使用自动混合精度（AMP）推理 |
| `--policy.n_obs_steps` | int | 1 | 否 | 传给策略的历史观测步数（包含当前步） |

> 注意：策略的其他参数（如网络结构超参）通常在训练时已保存到 `config.json`，加载时自动还原。一般不需要在 rollout 时覆盖。

---

### 1.5 数据集配置（--dataset.*）

| 参数 | 类型 | 默认值 | 必填 | 说明 |
|------|------|--------|------|------|
| `--dataset.repo_id` | str | `""` | sentry/highlight/dagger 必填 | HuggingFace Hub 上的数据集仓库 ID，格式为 `{用户名}/{数据集名}` |
| `--dataset.single_task` | str | `""` | 否 | 录制任务的简短准确描述（如 `"Pick the Lego block and drop it in the box."`）。与 `--task` 互通，设一个即可 |
| `--dataset.root` | Path | None | 否 | 数据集本地存储根目录。不设时默认为 `$HF_LEROBOT_HOME/{repo_id}` |
| `--dataset.fps` | int | 30 | 否 | 录制帧率（每秒帧数） |
| `--dataset.episode_time_s` | int/float | 60 | 否 | 每个 episode 的录制时长（秒） |
| `--dataset.reset_time_s` | int/float | 60 | 否 | 每个 episode 结束后环境重置时间（秒） |
| `--dataset.num_episodes` | int | 50 | 否 | 录制的 episode 总数 |
| `--dataset.video` | bool | True | 否 | 是否将帧编码为视频文件 |
| `--dataset.push_to_hub` | bool | True | 否 | 是否在拆解（teardown）时将数据集上传到 HuggingFace Hub |
| `--dataset.private` | bool | False | 否 | 是否上传到私有仓库 |
| `--dataset.tags` | list[str] | None | 否 | 上传到 Hub 时附加的标签列表 |
| `--dataset.num_image_writer_processes` | int | 0 | 否 | 用于将帧保存为 PNG 的子进程数。0 表示仅使用线程；≥1 时使用子进程，每个子进程内部使用线程。推荐 0 进程、每摄像头 4 线程 |
| `--dataset.num_image_writer_threads_per_camera` | int | 4 | 否 | 每个摄像头写帧到磁盘的线程数。线程过多会阻塞主线程导致 fps 不稳定，过少会导致摄像头 fps 下降 |
| `--dataset.video_encoding_batch_size` | int | 1 | 否 | 批量编码视频的 episode 数。1 表示立即编码（默认），更大的值表示批量编码 |
| `--dataset.vcodec` | str | `libsvtav1` | 否 | 视频编码格式。可选：`h264`、`hevc`、`libsvtav1`、`auto`，或硬件编码器：`h264_videotoolbox`、`h264_nvenc`、`h264_vaapi`、`h264_qsv`。`auto` 自动检测最佳硬件编码器 |
| `--dataset.streaming_encoding` | bool | False | 否 | 是否启用流式视频编码：在采集时实时编码帧，而非先写 PNG 再编码。使 `save_episode()` 近乎即时完成。**sentry/highlight 模式下强制启用** |
| `--dataset.encoder_queue_maxsize` | int | 30 | 否 | 流式编码时每个摄像头的最大缓冲帧数（约 30fps 下 1 秒的缓冲）。当编码器跟不上时提供背压控制 |
| `--dataset.encoder_threads` | int | None | 否 | 每个编码器实例的线程数。None 表示自动（由编码器决定）。较低的值降低 CPU 占用 |

---

### 1.6 运行时参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--fps` | float | 30.0 | 控制循环的帧率（每秒执行次数） |
| `--duration` | float | 0.0 | 运行时长（秒）。**0 表示无限运行**（24/7 模式） |
| `--interpolation_multiplier` | int | 1 | 动作插值倍数，用于平滑动作过渡 |
| `--device` | str | None | PyTorch 推理设备（如 `cuda`、`cpu`、`mps`）。不设时自动从策略配置读取或自动检测 |
| `--task` | str | `""` | 传给策略的任务描述文本。与 `--dataset.single_task` 互通，设置任一即可 |
| `--display_data` | bool | False | 是否将观测/动作实时流式传输到 Rerun 进行可视化 |
| `--display_ip` | str | None | Rerun 可视化服务器的 IP 地址（用于远程可视化） |
| `--display_port` | int | None | Rerun 可视化服务器的端口 |
| `--display_compressed_images` | bool | False | 是否在 Rerun 中显示压缩后的图像 |
| `--play_sounds` | bool | True | 是否使用语音合成朗读事件（如 episode 开始/结束提示音） |
| `--resume` | bool | False | 是否恢复之前的录制会话（仅 sentry 模式有意义）。设为 `true` 时保留已有的 episode 数据继续录制 |
| `--rename_map` | dict | `{}` | 将机器人/数据集的观测键映射到策略键的重命名映射表。格式：`"{robot_key: policy_key, ...}"`。用于机器人硬件键名与训练时数据集键名不一致的情况 |
| `--return_to_initial_position` | bool | True | 程序关闭时是否平滑插值回到启动时的关节位置。设为 `False` 则机器人保持在最终姿态 |

---

### 1.7 Torch Compile 编译优化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--use_torch_compile` | bool | False | 是否使用 `torch.compile` 编译策略模型以加速推理（首次运行需要编译预热） |
| `--torch_compile_backend` | str | `inductor` | torch.compile 的后端编译器，可选 `inductor`、`cudagraphs` 等 |
| `--torch_compile_mode` | str | `default` | 编译模式，可选 `default`、`reduce-overhead`、`max-autotune` 等 |
| `--compile_warmup_inferences` | int | 2 | 编译预热推理次数。在正式计时前运行指定次数的推理以完成 JIT 编译 |

---

## 二、策略详解

### 2.1 Base 策略（`--strategy.type=base`）

自主策略执行，**不进行数据录制**。适用于快速评估、演示或仅需观察机器人行为的场景。

**无额外参数。**

示例：
```bash
lerobot-rollout \
    --strategy.type=base \
    --policy.path=lerobot/act_koch_real \
    --robot.type=koch_follower \
    --robot.port=/dev/ttyACM0 \
    --task="pick up cube" \
    --duration=30
```

---

### 2.2 Sentry 策略（`--strategy.type=sentry`）

持续自主录制，带周期性上传到 HuggingFace Hub。Episode 边界根据摄像头分辨率、FPS 和目标视频文件大小自动计算，确保每次上传时视频文件已完整。

策略状态（隐藏状态、RTC 队列）**跨 episode 持续保留**：机器人不会在 episode 之间重置。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy.upload_every_n_episodes` | int | 5 | 每录制 N 个 episode 后推送至 Hub |
| `--strategy.target_video_file_size_mb` | int | None | 目标视频文件大小（MB），用于 episode 轮转。达到此大小时触发 episode 切换。None 时使用系统默认值 |

**强制行为：** Sentry 模式下 `--dataset.streaming_encoding` 被强制设为 `True`。

示例：
```bash
lerobot-rollout \
    --strategy.type=sentry \
    --strategy.upload_every_n_episodes=5 \
    --policy.path=lerobot/pi0_base \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
    --dataset.repo_id=user/rollout_sentry_data \
    --dataset.single_task="patrol" \
    --duration=3600
```

---

### 2.3 Highlight 策略（`--strategy.type=highlight`）

自主运行，带按需录制。使用内存有界的环形缓冲区持续捕获最近的遥测数据。按下保存键时刷出缓冲区并开始实时录制，再按一次保存该 episode。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy.ring_buffer_seconds` | float | 10.0 | 环形缓冲区保留的历史时长（秒）。缓冲区满后自动丢弃最旧数据 |
| `--strategy.ring_buffer_max_memory_mb` | int | 1024 | 环形缓冲区最大内存占用（MB），防止内存溢出 |
| `--strategy.save_key` | str | `s` | 保存按键。第一次按下刷出缓冲区并开始录制，第二次按下结束并保存 episode |
| `--strategy.push_key` | str | `h` | 推送按键。按下时将数据集推送到 HuggingFace Hub |

**强制行为：** Highlight 模式下 `--dataset.streaming_encoding` 被强制设为 `True`。

**键盘控制：**

| 按键 | 操作 |
|------|------|
| `s`（默认） | 第一次：刷出缓冲区 + 开始录制；第二次：保存 episode |
| `h`（默认） | 推送数据集到 Hub |

示例：
```bash
lerobot-rollout \
    --strategy.type=highlight \
    --strategy.ring_buffer_seconds=30 \
    --policy.path=lerobot/act_koch_real \
    --robot.type=koch_follower \
    --robot.port=/dev/ttyACM0 \
    --dataset.repo_id=user/rollout_highlight_data \
    --dataset.single_task="pick up cube"
```

---

### 2.4 DAgger 策略（`--strategy.type=dagger`）

人机协作数据采集（DAgger / RaC）。在自主策略执行和人工干预之间交替进行。干预帧标记为 `intervention=True`。

**必须设置 `--teleop.type`**（遥操作器），否则启动时报错。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--strategy.num_episodes` | int | None | 要采集的校正 episode 数（仅 corrections-only 模式）。None 时从 `--dataset.num_episodes` 读取 |
| `--strategy.record_autonomous` | bool | False | 是否同时录制自主阶段帧。`False`（默认）= 仅录制人工校正窗口，每次校正成为一个 episode；`True` = 录制自主+校正帧，使用基于文件大小的 episode 轮转（同 Sentry） |
| `--strategy.upload_every_n_episodes` | int | 5 | 每 N 个 episode 推送至 Hub（仅 `record_autonomous=True` 时有效） |
| `--strategy.target_video_file_size_mb` | int | None | 目标视频文件大小（MB），用于 `record_autonomous=True` 时的 episode 轮转 |
| `--strategy.input_device` | str | `keyboard` | 输入设备类型，可选 `keyboard`（键盘）或 `pedal`（脚踏板） |
| `--strategy.keyboard.pause_resume` | str | `space` | 键盘暂停/恢复按键 |
| `--strategy.keyboard.correction` | str | `tab` | 键盘开始/停止校正按键 |
| `--strategy.keyboard.upload` | str | `enter` | 键盘推送数据集按键 |
| `--strategy.pedal.device_path` | str | `/dev/input/by-id/usb-PCsensor_FootSwitch-event-kbd` | 脚踏板设备路径 |
| `--strategy.pedal.pause_resume` | str | `KEY_A` | 脚踏板暂停/恢复键码（evdev 格式，如 `KEY_A`） |
| `--strategy.pedal.correction` | str | `KEY_B` | 脚踏板校正键码 |
| `--strategy.pedal.upload` | str | `KEY_C` | 脚踏板推送键码 |

**键盘控制（默认）：**

| 按键 | 操作 |
|------|------|
| `Space` | 暂停 / 恢复策略执行 |
| `Tab` | 开始 / 停止人工校正 |
| `Enter` | 推送数据集到 Hub（corrections-only 模式） |
| `ESC` | 停止会话 |

**streaming_encoding 规则：**
- `record_autonomous=True` 时强制启用 `streaming_encoding`
- `record_autonomous=False`（corrections-only）时不强制，但建议手动启用以加速 episode 保存

示例（corrections-only）：
```bash
lerobot-rollout \
    --strategy.type=dagger \
    --strategy.num_episodes=20 \
    --policy.path=outputs/pretrain/checkpoints/last/pretrained_model \
    --robot.type=bi_openarm_follower \
    --teleop.type=openarm_mini \
    --dataset.repo_id=user/rollout_hil_data \
    --dataset.single_task="Fold the T-shirt"
```

示例（continuous recording + RTC）：
```bash
lerobot-rollout \
    --strategy.type=dagger \
    --strategy.record_autonomous=true \
    --strategy.num_episodes=50 \
    --inference.type=rtc \
    --inference.rtc.execution_horizon=10 \
    --policy.path=user/my_pi0_policy \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM0 \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --dataset.repo_id=user/rollout_dagger_rtc_data \
    --dataset.single_task="Grasp the block"
```

---

## 三、推理后端详解

### 3.1 Sync 推理（`--inference.type=sync`，默认）

同步推理，每个控制 tick 调用一次策略。适用于推理速度快于控制频率的模型（如 ACT、Diffusion 等）。

**无额外参数。**

---

### 3.2 RTC 推理（`--inference.type=rtc`）

Real-Time Chunking：在后台线程异步执行策略推理，适用于推理速度慢于控制频率的 VLA 模型（如 Pi0、Pi0.5、SmolVLA 等）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--inference.rtc.enabled` | bool | True | 是否启用 RTC |
| `--inference.rtc.prefix_attention_schedule` | str | `LINEAR` | 前缀注意力调度策略。可选值：`ZEROS`、`ONES`、`LINEAR`、`EXP`。控制重叠时间步的 attention 权重分配方式 |
| `--inference.rtc.max_guidance_weight` | float | 10.0 | 最大引导权重，必须为正数。控制历史动作对当前预测的影响强度 |
| `--inference.rtc.execution_horizon` | int | 10 | 执行视野，即每次推理后实际执行的 action chunk 长度。较小的值使控制更频繁但每次预测的动作更少 |
| `--inference.rtc.debug` | bool | False | 是否启用 RTC 调试模式 |
| `--inference.rtc.debug_maxlen` | int | 100 | 调试模式下的最大记录长度 |
| `--inference.queue_threshold` | int | 30 | RTC 队列阈值。当动作队列长度低于此值时触发警告或采取补救措施 |

示例（Pi0 模型 + RTC）：
```bash
lerobot-rollout \
    --strategy.type=base \
    --policy.path=lerobot/pi0_base \
    --inference.type=rtc \
    --inference.rtc.execution_horizon=10 \
    --inference.rtc.max_guidance_weight=10.0 \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
    --task="pick up cube" \
    --duration=60
```

---

## 四、完整参数速查表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--robot.type` | str | — | **必填**，机器人类型 |
| `--robot.port` | str | — | 串口路径 |
| `--robot.id` | str | None | 机器人实例 ID |
| `--robot.calibration_dir` | Path | None | 校准文件目录 |
| `--robot.cameras` | dict | — | 摄像头配置 |
| `--teleop.type` | str | None | 遥操作器类型（DAgger 必填） |
| `--teleop.id` | str | None | 遥操作器 ID |
| `--policy.path` | str | — | **必填**，预训练策略路径 |
| `--policy.device` | str | None | 推理设备 |
| `--policy.use_amp` | bool | False | 是否使用混合精度 |
| `--policy.n_obs_steps` | int | 1 | 历史观测步数 |
| `--strategy.type` | str | `base` | 策略类型 |
| `--strategy.upload_every_n_episodes` | int | 5 | sentry/dagger: 每 N 个 episode 上传 |
| `--strategy.target_video_file_size_mb` | int | None | sentry/dagger: 目标视频文件大小(MB) |
| `--strategy.ring_buffer_seconds` | float | 10.0 | highlight: 环形缓冲区时长(秒) |
| `--strategy.ring_buffer_max_memory_mb` | int | 1024 | highlight: 缓冲区最大内存(MB) |
| `--strategy.save_key` | str | `s` | highlight: 保存按键 |
| `--strategy.push_key` | str | `h` | highlight: 推送按键 |
| `--strategy.num_episodes` | int | None | dagger: 校正 episode 数 |
| `--strategy.record_autonomous` | bool | False | dagger: 是否录制自主阶段 |
| `--strategy.input_device` | str | `keyboard` | dagger: 输入设备 |
| `--strategy.keyboard.*` | str | 各不同 | dagger: 键盘按键绑定 |
| `--strategy.pedal.*` | str | 各不同 | dagger: 脚踏板配置 |
| `--inference.type` | str | `sync` | 推理后端 |
| `--inference.rtc.execution_horizon` | int | 10 | RTC: 执行视野 |
| `--inference.rtc.max_guidance_weight` | float | 10.0 | RTC: 最大引导权重 |
| `--inference.rtc.prefix_attention_schedule` | str | `LINEAR` | RTC: 注意力调度 |
| `--inference.rtc.debug` | bool | False | RTC: 调试模式 |
| `--inference.rtc.debug_maxlen` | int | 100 | RTC: 调试最大长度 |
| `--inference.queue_threshold` | int | 30 | RTC: 队列阈值 |
| `--dataset.repo_id` | str | `""` | Hub 数据集仓库 ID |
| `--dataset.single_task` | str | `""` | 任务描述 |
| `--dataset.root` | Path | None | 本地存储根目录 |
| `--dataset.fps` | int | 30 | 录制帧率 |
| `--dataset.episode_time_s` | int/float | 60 | episode 时长(秒) |
| `--dataset.reset_time_s` | int/float | 60 | 重置时间(秒) |
| `--dataset.num_episodes` | int | 50 | episode 总数 |
| `--dataset.video` | bool | True | 是否编码为视频 |
| `--dataset.push_to_hub` | bool | True | 是否上传到 Hub |
| `--dataset.private` | bool | False | 是否私有仓库 |
| `--dataset.tags` | list[str] | None | Hub 标签 |
| `--dataset.num_image_writer_processes` | int | 0 | 图像写进程数 |
| `--dataset.num_image_writer_threads_per_camera` | int | 4 | 每摄像头图像写线程数 |
| `--dataset.video_encoding_batch_size` | int | 1 | 视频编码批量大小 |
| `--dataset.vcodec` | str | `libsvtav1` | 视频编码格式 |
| `--dataset.streaming_encoding` | bool | False | 流式视频编码 |
| `--dataset.encoder_queue_maxsize` | int | 30 | 编码器队列缓冲大小 |
| `--dataset.encoder_threads` | int | None | 编码器线程数 |
| `--fps` | float | 30.0 | 控制循环帧率 |
| `--duration` | float | 0.0 | 运行时长(秒)，0=无限 |
| `--interpolation_multiplier` | int | 1 | 动作插值倍数 |
| `--device` | str | None | PyTorch 设备 |
| `--task` | str | `""` | 任务描述 |
| `--display_data` | bool | False | Rerun 可视化 |
| `--display_ip` | str | None | Rerun 服务器 IP |
| `--display_port` | int | None | Rerun 服务器端口 |
| `--display_compressed_images` | bool | False | 显示压缩图像 |
| `--play_sounds` | bool | True | 播放提示音 |
| `--resume` | bool | False | 恢复之前会话 |
| `--rename_map` | dict | `{}` | 观测键重命名映射 |
| `--return_to_initial_position` | bool | True | 关闭时回到初始位置 |
| `--use_torch_compile` | bool | False | 启用 torch.compile |
| `--torch_compile_backend` | str | `inductor` | 编译后端 |
| `--torch_compile_mode` | str | `default` | 编译模式 |
| `--compile_warmup_inferences` | int | 2 | 编译预热推理次数 |

---

## 五、注意事项

1. **Base 策略不支持数据集录制**：使用 base 策略时设置 `--dataset.*` 会报错。如需录制请使用 sentry、highlight 或 dagger。

2. **streaming_encoding 自动强制**：sentry 和 highlight 模式会自动将 `--dataset.streaming_encoding` 设为 `True`，无需手动设置。

3. **task 与 single_task 互通**：`--task` 和 `--dataset.single_task` 设置任一即可，系统会自动同步到另一侧。

4. **DAgger 必须设置 teleop**：使用 `--strategy.type=dagger` 时必须同时设置 `--teleop.type`。

5. **resume 仅用于 sentry**：`--resume=true` 用于恢复之前的 sentry 录制会话，保留已有 episode 数据继续录制。

6. **设备自动检测**：不设 `--device` 时，系统优先从策略配置中读取设备，若不可用则自动选择（优先 GPU → MPS → CPU）。

7. **rename_map 的使用场景**：当机器人硬件的观测键名（如 `observation.state`）与训练时数据集的键名不一致时，通过 `--rename_map` 建立映射关系，例如 `--rename_map="{observation.state: observation.states}"`。
