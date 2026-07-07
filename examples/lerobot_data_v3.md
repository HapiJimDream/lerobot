# LeRobot v3.0 数据集结构说明 — cube_stacking_merged

> 数据集:双臂机器人叠方块任务(`bi_so_follower`,双臂 SO-ARM follower)
> 任务描述:*Place large cube on coaster. Then place small cube on large cube*(把大方块放到杯垫上,再把小方块叠到大方块上)
> 规模:60 个 episode / 44813 帧 / 30 FPS / 3 个相机视角

## 目录结构总览

```
cube_stacking_merged/
├── meta/                                  # 元信息
│   ├── info.json                          # 数据集"总说明书"(格式、规模、features 声明)
│   ├── stats.json                         # 全数据集统计量(归一化用)
│   ├── tasks.parquet                      # 任务文本表
│   └── episodes/chunk-000/file-000.parquet  # episode 索引表(60 行 × 121 列)
├── data/
│   └── chunk-000/file-000.parquet         # 逐帧数值数据(44813 行 × 7 列)
└── videos/                                # 三路相机的视觉观测
    ├── observation.images.left_head/chunk-000/file-000.mp4    # 头部相机(174 MB)
    ├── observation.images.left_left/chunk-000/file-000.mp4    # 左臂腕部相机(147 MB)
    └── observation.images.right_right/chunk-000/
        ├── file-000.mp4                   # 右臂腕部相机(172 MB)
        └── file-001.mp4                   # 超过 200 MB 上限后切分的第二个文件(32 MB)
```

---

## 1. `meta/` — 数据集元信息

### 1.1 `meta/info.json`(数据集"总说明书")
```
{
    "codebase_version": "v3.0",
    "robot_type": "bi_so_follower",
    "total_episodes": 60,
    "total_frames": 44813,
    "total_tasks": 1,
    "chunks_size": 1000,
    "data_files_size_in_mb": 100,
    "video_files_size_in_mb": 200,
    "fps": 30,
    "splits": {
        "train": "0:60"
    },
    "data_path": "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
    "video_path": "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4",
    "features": {
        "action": {
            "dtype": "float32",
            "names": [
                "left_shoulder_pan.pos",
                "left_shoulder_lift.pos",
                "left_elbow_flex.pos",
                "left_wrist_flex.pos",
                "left_wrist_roll.pos",
                "left_gripper.pos",
                "right_shoulder_pan.pos",
                "right_shoulder_lift.pos",
                "right_elbow_flex.pos",
                "right_wrist_flex.pos",
                "right_wrist_roll.pos",
                "right_gripper.pos"
            ],
            "shape": [
                12
            ]
        },
        "observation.state": {
            "dtype": "float32",
            "names": [
                "left_shoulder_pan.pos",
                "left_shoulder_lift.pos",
                "left_elbow_flex.pos",
                "left_wrist_flex.pos",
                "left_wrist_roll.pos",
                "left_gripper.pos",
                "right_shoulder_pan.pos",
                "right_shoulder_lift.pos",
                "right_elbow_flex.pos",
                "right_wrist_flex.pos",
                "right_wrist_roll.pos",
                "right_gripper.pos"
            ],
            "shape": [
                12
            ]
        },
        "observation.images.left_head": {
            "dtype": "video",
            "shape": [
                480,
                640,
                3
            ],
            "names": [
                "height",
                "width",
                "channels"
            ],
            "info": {
                "video.height": 480,
                "video.width": 640,
                "video.codec": "h264",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "video.fps": 30,
                "video.channels": 3,
                "has_audio": false
            }
        },
        "observation.images.left_left": {
            "dtype": "video",
            "shape": [
                480,
                640,
                3
            ],
            "names": [
                "height",
                "width",
                "channels"
            ],
            "info": {
                "video.height": 480,
                "video.width": 640,
                "video.codec": "h264",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "video.fps": 30,
                "video.channels": 3,
                "has_audio": false
            }
        },
        "observation.images.right_right": {
            "dtype": "video",
            "shape": [
                480,
                640,
                3
            ],
            "names": [
                "height",
                "width",
                "channels"
            ],
            "info": {
                "video.height": 480,
                "video.width": 640,
                "video.codec": "h264",
                "video.pix_fmt": "yuv420p",
                "video.is_depth_map": false,
                "video.fps": 30,
                "video.channels": 3,
                "has_audio": false
            }
        },
        "timestamp": {
            "dtype": "float32",
            "shape": [
                1
            ],
            "names": null
        },
        "frame_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "episode_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        },
        "task_index": {
            "dtype": "int64",
            "shape": [
                1
            ],
            "names": null
        }
    }
}
```


| 字段 | 内容 | 作用 |
|---|---|---|
| `codebase_version` | `v3.0` | LeRobot 格式版本,加载器据此选择解析方式 |
| `robot_type` | `bi_so_follower` | 采集数据的机器人型号(双臂) |
| `total_episodes` / `total_frames` | 60 / 44813 | 总回合数、总帧数 |
| `total_tasks` | 1 | 任务种类数(只有一个叠方块任务) |
| `chunks_size` | 1000 | 每个 chunk 目录最多放多少个文件 |
| `data_files_size_in_mb` | 100 | 单个 data parquet 文件的大小上限,超过就切分新文件 |
| `video_files_size_in_mb` | 200 | 单个 mp4 文件的大小上限(right_right 视频因此切出 file-001) |
| `fps` | 30 | 采样帧率,timestamp 按 1/30 秒递增 |
| `splits` | `train: 0:60` | 数据划分,60 个 episode 全部用于训练 |
| `data_path` | `data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet` | 帧数据文件的路径模板 |
| `video_path` | `videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4` | 视频文件的路径模板 |
| `features` | 见 1.2 | 声明每个数据字段的 dtype、shape、维度名称及视频编码信息 |

### 1.2 `info.json` 中 `features` 各字段详解

`features` 是整个数据集的 **schema(数据字典)**:声明数据集中每一个特征叫什么、什么类型、什么形状、每一维是什么含义。LeRobot 加载器(`LeRobotDataset`)完全依赖它来解析 parquet 列和视频流,训练框架也靠它自动构建模型的输入输出维度。

每个特征条目的通用结构:

| 键 | 含义 |
|---|---|
| `dtype` | 数据类型:`float32` / `int64` 表示数值(存在 parquet 里);`video` 表示该特征存为 mp4 视频,按需解码 |
| `shape` | 张量形状:如 `[12]` 表示 12 维向量,`[480, 640, 3]` 表示高×宽×通道的图像 |
| `names` | 每一维的名称(语义标签);标量特征为 `null` |
| `info` | 仅 `video` 类型有:编码参数(分辨率、编解码器、像素格式、帧率等) |

#### ① `action` — 动作(模型学习的目标输出)

- `dtype: float32`,`shape: [12]`
- 遥操作时**主臂(leader)发出的 12 个关节目标位置指令**,即模仿学习的监督标签(policy 要学会输出它)。
- `names` 共 12 项,顺序为**左臂 6 关节 + 右臂 6 关节**:

| 序号 | 名称 | 含义 |
|---|---|---|
| 0 | `left_shoulder_pan.pos` | 左臂肩部水平旋转 |
| 1 | `left_shoulder_lift.pos` | 左臂肩部抬升 |
| 2 | `left_elbow_flex.pos` | 左臂肘部弯曲 |
| 3 | `left_wrist_flex.pos` | 左臂腕部俯仰 |
| 4 | `left_wrist_roll.pos` | 左臂腕部旋转 |
| 5 | `left_gripper.pos` | 左夹爪开合 |
| 6–11 | `right_*` | 右臂同上 6 个关节 |

`.pos` 后缀表示位置控制(角度/归一化位置),而非速度或力矩。

#### ② `observation.state` — 本体感知状态(模型输入之一)

- `dtype: float32`,`shape: [12]`,`names` 与 `action` **完全相同**。
- 含义不同:这是 **follower 机械臂编码器实际测量到的当前关节位置**。
- 一句话区分:`action` 是"想让它去哪",`observation.state` 是"它现在在哪"。两者的差值反映跟踪误差/延迟。

#### ③④⑤ `observation.images.left_head` / `left_left` / `right_right` — 三路相机图像(视觉输入)

- `dtype: video`:图像不存在 parquet 里,而是编码成 mp4(节省大量空间),训练时按 timestamp 实时解码。
- `shape: [480, 640, 3]`,`names: ["height", "width", "channels"]`:每帧是 480 高 × 640 宽 × 3 通道(RGB)的图像。
- 三个视角:`left_head` = 头部/全局相机,`left_left` = 左臂腕部相机,`right_right` = 右臂腕部相机。
- `info` 子字段(三个相机取值相同):

| 键 | 值 | 含义 |
|---|---|---|
| `video.height` / `video.width` | 480 / 640 | 视频分辨率,与 `shape` 一致 |
| `video.codec` | `h264` | 视频编码器 |
| `video.pix_fmt` | `yuv420p` | 像素格式(解码后转 RGB) |
| `video.is_depth_map` | `false` | 不是深度图,是普通彩色相机 |
| `video.fps` | 30 | 视频帧率,与数据集 `fps` 一致,保证逐帧对齐 |
| `video.channels` | 3 | 3 通道彩色 |
| `has_audio` | `false` | 无音轨 |

#### ⑥ `timestamp` — 回合内时间戳

- `dtype: float32`,`shape: [1]`,`names: null`
- 该帧在**本回合内**的时间(秒),从 0 开始按 1/30 递增。
- 作用:与视频对齐——加载器用 `episode起始时间戳 + timestamp` 定位到 mp4 中的具体帧。

#### ⑦ `frame_index` — 回合内帧序号

- `dtype: int64`,`shape: [1]`
- 该帧在本回合内的序号,每个新回合从 0 重新计数(`timestamp ≈ frame_index / fps`)。

#### ⑧ `episode_index` — 回合编号

- `dtype: int64`,`shape: [1]`
- 该帧属于第几个回合(0~59),用于按回合切分/采样数据。

#### ⑨ `index` — 全局帧编号

- `dtype: int64`,`shape: [1]`
- 跨回合连续的全局唯一编号(0~44812),用于全数据集随机索引。

#### ⑩ `task_index` — 任务编号

- `dtype: int64`,`shape: [1]`
- 指向 `meta/tasks.parquet` 的行号(本数据集全为 0)。加载时据此查回任务文本,作为语言条件策略(如 SmolVLA)的文本输入。

### 1.3 `meta/stats.json`(全数据集统计量)

对每个特征(`action`、`observation.state`、三路图像、`timestamp`、`frame_index`、`episode_index`、`index`、`task_index`)存储:

`min / max / mean / std / count / q01 / q10 / q50 / q90 / q99`

作用:**训练时对输入输出做归一化**(如把关节角度标准化到零均值单位方差,或 min-max 归一到 [-1,1])。图像特征的统计量是逐通道的像素均值/方差,用于图像标准化。

### 1.4 `meta/tasks.parquet`(任务表,1 行)

| 列 | 内容 | 作用 |
|---|---|---|
| `task`(索引) | `Place large cube on coaster. Then place small cube on large cube` | 自然语言任务描述,训练语言条件策略时的文本输入 |
| `task_index` | 0 | 任务编号,与 data 中每帧的 `task_index` 对应 |

### 1.5 `meta/episodes/chunk-000/file-000.parquet`(episode 索引表,60 行 × 121 列)

每行描述一个 episode,列分五组:

**① 基本信息**

| 列 | 作用 |
|---|---|
| `episode_index` | 回合编号(0~59) |
| `tasks` | 该回合执行的任务文本列表 |
| `length` | 该回合帧数(如第 0 集 715 帧 ≈ 23.8 秒) |

**② 数据定位**(让加载器无需解析全部文件即可随机访问任意 episode)

| 列 | 作用 |
|---|---|
| `data/chunk_index`、`data/file_index` | 该回合的帧数据在哪个 parquet 文件 |
| `dataset_from_index`、`dataset_to_index` | 该回合在全局帧序列中的起止行号(如第 1 集是第 715~1367 帧) |

**③ 视频定位**(每相机 4 列 × 3 相机 = 12 列)

| 列 | 作用 |
|---|---|
| `videos/<相机名>/chunk_index`、`file_index` | 该回合画面在哪个 mp4 文件 |
| `videos/<相机名>/from_timestamp`、`to_timestamp` | 在该 mp4 中的起止秒数。60 个回合的视频被拼接进少数几个大 mp4,加载器靠这两个时间戳精确切出对应回合的帧 |

**④ 逐回合统计量**(`stats/<特征名>/<统计项>`,共 100 列)

每个特征的 min/max/mean/std/count/q01/q10/q50/q90/q99,按回合粒度存储。作用:合并数据集或重算全局 `stats.json` 时无需重新扫描原始数据。

**⑤ 自引用**

| 列 | 作用 |
|---|---|
| `meta/episodes/chunk_index`、`file_index` | 本行元数据自身所在的文件位置 |

---

## 2. `data/` — 逐帧数值数据(不含图像)

### `data/chunk-000/file-000.parquet`(44813 行 × 7 列,60 个回合按顺序拼接)

| 列 | 类型/形状 | 作用 |
|---|---|---|
| `action` | float32[12] | **监督标签**:12 关节目标位置指令(左臂 6 + 右臂 6),由遥操作主臂发出 |
| `observation.state` | float32[12] | **模型输入**:follower 12 关节实测位置,字段顺序与 action 相同 |
| `timestamp` | float32 | 回合内时间(秒),从 0 按 1/30 递增,用于和视频帧对齐 |
| `frame_index` | int64 | 回合内帧序号(每回合从 0 重计) |
| `episode_index` | int64 | 所属回合编号(0~59) |
| `index` | int64 | 全局唯一帧编号(0~44812) |
| `task_index` | int64 | 指向 `tasks.parquet` 的任务编号(全为 0) |

数据样例(第 0 帧):

```
action            = [-29.32, -92.88, 94.51, 37.98, -8.57, 24.30,   # 左臂 6 关节
                     -4.84, -91.74, 96.53, 47.38, 15.16, 17.85]    # 右臂 6 关节
observation.state = [-29.58, -89.54, 95.03, 38.33, -8.48, 24.75,
                     -4.92, -91.38, 96.35, 48.04, 14.90, 18.77]
timestamp = 0.0   frame_index = 0   episode_index = 0   index = 0   task_index = 0
```

> 注意:**图像不存在 parquet 里**。加载器根据 `episode_index + timestamp` 到 `videos/` 按需解码对应帧——这是 LeRobot 用视频压缩节省空间的核心设计。

---

## 3. `videos/` — 三路相机的视觉观测

| 文件夹 | 视角 | 文件 | 大小 |
|---|---|---|---|
| `observation.images.left_head/` | 头部/全局相机 | `chunk-000/file-000.mp4` | 174 MB(约 1494 秒) |
| `observation.images.left_left/` | 左臂腕部相机 | `chunk-000/file-000.mp4` | 147 MB |
| `observation.images.right_right/` | 右臂腕部相机 | `chunk-000/file-000.mp4` + `file-001.mp4` | 172 MB + 32 MB |

- 每个 mp4 由 60 个回合的画面**按顺序首尾拼接**而成:640×480、30 FPS、h264、yuv420p、无音频(与 `features` 中 video `info` 一致)。
- `right_right` 拼接后超过 `video_files_size_in_mb: 200` 上限,故切成两个文件——这正是 episodes 表中 `videos/.../file_index` 和 `from/to_timestamp` 存在的意义。
- 作用:作为策略网络的视觉输入,训练时按 timestamp 实时解码对应帧。

---

## 4. 三者如何协作(训练数据流)

训练加载第 N 个回合的第 t 帧时:

1. 查 `meta/episodes` → 找到该回合帧数据和视频的文件位置及时间区间;
2. 从 `data/*.parquet` 读出该帧的 `observation.state`(输入)和 `action`(监督信号);
3. 按 `timestamp` 从三个 mp4 解码出三路 480×640 RGB 图像(视觉输入);
4. 按 `task_index` 从 `tasks.parquet` 取任务文本(语言输入);
5. 用 `stats.json` 对各特征归一化。

这正是 SmolVLA / ACT / Diffusion Policy 等策略在 LeRobot 框架中的标准训练数据流。