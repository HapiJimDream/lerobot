# lerobot_train.py 所有可配置参数详细说明

> 源码位置：`src/lerobot/scripts/lerobot_train.py`
> 配置类：`src/lerobot/configs/train.py` → `TrainPipelineConfig`

---

## 1. 核心训练参数

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--steps` | int | 100000 | 总训练步数（策略更新次数 = forward + backward + optimizer step） |
| `--batch_size` | int | 8 | 每个 GPU 的 batch 大小。有效 batch = batch_size × num_processes（多卡时自动放大） |
| `--seed` | int \| None | 1000 | 随机种子，控制模型初始化、数据打乱、评估环境的可复现性。设 None 则不设置种子 |
| `--resume` | bool | False | True：从上次 checkpoint 继续训练。需要 `--config_path` 指向已有的 `train_config.json` |
| `--output_dir` | Path \| None | `outputs/train/{日期}/{时间}_{job_name}` | 输出目录，存放 checkpoint、日志、评估视频等。若目录已存在且 resume=False 会报错 |
| `--job_name` | str \| None | `{env.type}_{policy.type}` 或 `{policy.type}` | 任务名称，用于输出目录命名和 WandB 分组 |

---

## 2. 数据加载参数

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--num_workers` | int | 4 | DataLoader 子进程数。越多数据加载越快，但占用更多 CPU 和内存。设 0 则在主进程加载 |
| `--prefetch_factor` | int | 4 | 每个 worker 预取的 batch 数量。仅当 num_workers > 0 时生效，设 None 则禁用 |
| `--persistent_workers` | bool | True | DataLoader worker 是否在 epoch 间保持存活，避免重复启动开销。仅 num_workers > 0 时生效 |

> DataLoader 还自动设置：`pin_memory=True`（仅 CUDA 设备）、`drop_last=False`、`shuffle=True`（非流式数据集）

---

## 3. 日志与保存参数

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--log_freq` | int | 200 | 每 N 步打印一次训练日志（loss、grad_norm、lr、update_s、dataloading_s）。设 0 禁用日志 |
| `--save_freq` | int | 20000 | 每 N 步保存一次 checkpoint。最后一步也会保存 |
| `--save_checkpoint` | bool | True | 是否保存 checkpoint。设 False 可完全禁用 |
| `--eval_freq` | int | 20000 | 每 N 步在仿真环境中评估一次策略。设 0 禁用评估 |
| `--tolerance_s` | float | 1e-4 | 时间容差（秒），用于某些时间同步检查 |

---

## 4. 数据集参数（`--dataset.*`）

> 配置类：`src/lerobot/configs/default.py` → `DatasetConfig`

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--dataset.repo_id` | str | **必填** | Hugging Face Hub 数据集 ID（如 `lerobot/pusht`）或本地路径 |
| `--dataset.root` | str \| None | None | 本地数据集根目录。None 时使用 `$HF_LEROBOT_HOME/repo_id` |
| `--dataset.episodes` | list[int] \| None | None | 指定使用哪些 episode 的索引列表（如 `[0,1,2]`）。None 使用全部。不能有负数或重复 |
| `--dataset.revision` | str \| None | None | 数据集的 Git revision（分支/tag/commit），用于版本锁定 |
| `--dataset.use_imagenet_stats` | bool | True | 是否使用 ImageNet 均值/标准差进行图像归一化 |
| `--dataset.video_backend` | str | 自动检测 | 视频解码后端（如 `pyav`、`video_reader` 等），默认使用系统安全可用的编解码器 |
| `--dataset.return_uint8` | bool | False | True：视频帧返回 uint8 张量（0-255）而非 float32（0.0-1.0），减少内存并加速 DataLoader IPC |
| `--dataset.streaming` | bool | False | True：启用流式数据集加载（不下载全部数据到本地） |

### 4.1 图像增强参数（`--dataset.image_transforms.*`）

> 配置类：`src/lerobot/transforms/transforms.py` → `ImageTransformsConfig`
> 所有增强使用 torchvision.transforms.v2，通过 `RandomSubsetApply` 随机采样应用

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--dataset.image_transforms.enable` | bool | False | 是否启用图像增强 |
| `--dataset.image_transforms.max_num_transforms` | int | 3 | 每帧最多应用多少个变换（从可用变换中采样） |
| `--dataset.image_transforms.random_order` | bool | False | True：以随机顺序应用变换；False：按 Torchvision 推荐顺序 |

**默认增强方法（通过 `--dataset.image_transforms.tfs` 配置）：**

| 增强名称 | 类型 | 默认参数 | 说明 |
|---|---|---|---|
| brightness | ColorJitter | brightness=(0.8, 1.2) | 亮度抖动 |
| contrast | ColorJitter | contrast=(0.8, 1.2) | 对比度抖动 |
| saturation | ColorJitter | saturation=(0.5, 1.5) | 饱和度抖动 |
| hue | ColorJitter | hue=(-0.05, 0.05) | 色调抖动 |
| sharpness | SharpnessJitter | sharpness=(0.5, 1.5) | 锐度抖动 |
| affine | RandomAffine | degrees=(-5.0, 5.0), translate=(0.05, 0.05) | 随机仿射变换 |

每个增强可通过 `weight` 参数控制采样概率。

---

## 5. 策略参数（`--policy.*`）

> 配置类：`src/lerobot/configs/policies.py` → `PreTrainedConfig`（基类）
> 每个策略（act/diffusion/pi0/smolvla 等）有自己的子类配置

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--policy` | str | **必填** | 策略类型名称（如 `act`、`diffusion`、`pi0`、`pi05`、`smolvla`、`vqbet`、`tdmpc`、`rtc`、`sarm`、`walloss`、`groot`、`xvla` 等） |
| `--policy.path` | str/Path | None | 从本地路径或 HF Hub 加载预训练策略权重和配置 |
| `--policy.pretrained_path` | Path \| None | None | 预训练权重路径（通常由 `--policy.path` 自动设置） |
| `--policy.n_obs_steps` | int | 1 | 传给策略的观测步数（当前步 + 回看的历史步数） |
| `--policy.device` | str \| None | 自动检测 | 设备：`cuda`、`cuda:0`、`cpu`、`mps`。Accelerator 会自动检测，若指定设备不可用会自动切换 |
| `--policy.use_amp` | bool | False | 是否使用自动混合精度（AMP）训练和评估。仅 CUDA/部分设备支持 |
| `--policy.use_peft` | bool | False | 策略是否使用 PEFT（Parameter-Efficient Fine-Tuning） |
| `--policy.push_to_hub` | bool | True | 训练完成后是否推送模型到 Hugging Face Hub |
| `--policy.repo_id` | str \| None | None | 推送到 Hub 的 repo ID（push_to_hub=True 时必须指定） |
| `--policy.private` | bool \| None | None | Hub 仓库是否设为私有 |
| `--policy.tags` | list[str] \| None | None | Hub 上的模型标签 |
| `--policy.license` | str \| None | None | Hub 上的模型许可证 |
| `--policy.input_features` | dict | 自动推断 | 输入特征定义（从数据集自动推断或手动指定） |
| `--policy.output_features` | dict | 自动推断 | 输出特征定义（从数据集自动推断或手动指定） |

---

## 6. 环境参数（`--env.*`）

> 配置类：`src/lerobot/envs/configs.py` → `EnvConfig`（基类）
> 每个仿真环境（pusht/aloha/libero/metaworld 等）有自己的子类

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--env` | str \| None | None | 仿真环境类型。真实机器人训练设为 None（评估用 `lerobot-eval` 单独做） |
| `--env.task` | str \| None | None | 环境任务名称（如 `PushT-v0`、`AlohaInsertion-v0`） |
| `--env.fps` | int | 30 | 环境帧率 |
| `--env.features` | dict | {} | 环境观测特征定义 |
| `--env.features_map` | dict | {} | 环境特征映射 |
| `--env.max_parallel_tasks` | int | 1 | 最大并行任务数（用于评估时多任务并行） |
| `--env.disable_env_checker` | bool | True | 是否禁用 gym 环境检查器 |

### 6.1 评估参数（`--eval.*`）

> 配置类：`src/lerobot/configs/default.py` → `EvalConfig`

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--eval.n_episodes` | int | 50 | 每次评估运行多少个 episode |
| `--eval.batch_size` | int | 0（自动） | 评估时的并行环境数（gym VectorEnv）。0 表示自动：基于 CPU 核心数计算（cpu_cores × 0.7），上限 64 且不超过 n_episodes |
| `--eval.use_async_envs` | bool | True | 是否使用异步环境（AsyncVectorEnv 多进程）。batch_size=1 时自动降级为 SyncVectorEnv |

---

## 7. 优化器参数（`--optimizer.*`）

> 配置类：`src/lerobot/optim/optimizers.py` → `OptimizerConfig`（基类）
> 默认使用策略自带的 preset（`use_policy_training_preset=True`）

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--optimizer` | str | 由策略 preset 决定 | 优化器类型选择（见下表） |
| `--use_policy_training_preset` | bool | True | True：使用策略默认的优化器/调度器；False：必须手动指定 optimizer 和 scheduler |

### 7.1 可选优化器类型

#### `adam`（默认）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `lr` | 1e-3 | 学习率 |
| `betas` | (0.9, 0.999) | Adam β1, β2 |
| `eps` | 1e-8 | 数值稳定性参数 |
| `weight_decay` | 0.0 | 权重衰减 |
| `grad_clip_norm` | 10.0 | 梯度裁剪最大范数。0 表示不裁剪（但仍会监控 grad_norm） |

#### `adamw`

| 参数 | 默认值 | 说明 |
|---|---|---|
| `lr` | 1e-3 | 学习率 |
| `betas` | (0.9, 0.999) | Adam β1, β2 |
| `eps` | 1e-8 | 数值稳定性参数 |
| `weight_decay` | 1e-2 | 权重衰减（AdamW 默认更大） |
| `grad_clip_norm` | 10.0 | 梯度裁剪最大范数 |

#### `sgd`

| 参数 | 默认值 | 说明 |
|---|---|---|
| `lr` | 1e-3 | 学习率 |
| `momentum` | 0.0 | 动量因子 |
| `dampening` | 0.0 | 阻尼因子 |
| `nesterov` | False | 是否使用 Nesterov 动量 |
| `weight_decay` | 0.0 | 权重衰减 |
| `grad_clip_norm` | 10.0 | 梯度裁剪最大范数 |

#### `xvla-adamw`（XVLA 专用）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `lr` | 1e-4 | 基础学习率 |
| `betas` | (0.9, 0.99) | Adam β1, β2 |
| `eps` | 1e-8 | 数值稳定性参数 |
| `weight_decay` | 0.0 | 权重衰减 |
| `grad_clip_norm` | 10.0 | 梯度裁剪最大范数 |
| `soft_prompt_lr_scale` | 1.0 | Soft-prompt 学习率缩放因子 |
| `soft_prompt_warmup_lr_scale` | None | Soft-prompt 预热学习率缩放（如 0.01） |

> 自动将参数分为三组：VLM 参数(lr×0.1)、Soft-prompt 参数、其他参数(lr×1.0)

#### `multi_adam`（多优化器，如 SAC）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `lr` | 1e-3 | 默认学习率 |
| `weight_decay` | 0.0 | 默认权重衰减 |
| `grad_clip_norm` | 10.0 | 梯度裁剪最大范数 |
| `optimizer_groups` | {} | 字典，每个参数组可独立配置 lr/betas/eps/weight_decay |

---

## 8. 学习率调度器参数（`--scheduler.*`）

> 配置类：`src/lerobot/optim/schedulers.py` → `LRSchedulerConfig`（基类）

### 8.1 `diffuser`（基于 diffusers 库）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `name` | "cosine" | 调度器名称（cosine / linear / constant 等，参考 diffusers.get_scheduler） |
| `num_warmup_steps` | None | 预热步数 |

### 8.2 `cosine_decay_with_warmup`（Pi0 等策略使用）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `num_warmup_steps` | int（必填） | 线性预热步数 |
| `num_decay_steps` | int（必填） | 余弦衰减总步数。若 steps < num_decay_steps 会自动缩放 |
| `peak_lr` | float（必填） | 预热结束时的峰值学习率 |
| `decay_lr` | float（必填） | 衰减结束时的最终学习率 |

### 8.3 `vqbet`（VQBeT 专用）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `num_warmup_steps` | int（必填） | 预热步数 |
| `num_vqvae_training_steps` | int（必填） | VQ-VAE 预训练步数（此期间 lr 恒定） |
| `num_cycles` | 0.5 | 余弦周期数 |

---

## 9. WandB 日志参数（`--wandb.*`）

> 配置类：`src/lerobot/configs/default.py` → `WandBConfig`

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--wandb.enable` | bool | False | 是否启用 WandB 在线日志 |
| `--wandb.project` | str | "lerobot" | WandB 项目名 |
| `--wandb.entity` | str \| None | None | WandB 团队/组织名 |
| `--wandb.notes` | str \| None | None | WandB 运行备注 |
| `--wandb.run_id` | str \| None | None | WandB 运行 ID（用于恢复中断的运行） |
| `--wandb.mode` | str \| None | None | `online`（在线）/ `offline`（离线缓存）/ `disabled`（完全禁用） |
| `--wandb.disable_artifact` | bool | False | True：禁用 artifact 保存（即使 save_checkpoint=True） |
| `--wandb.add_tags` | bool | True | True：将配置参数作为 tags 保存到 WandB 运行中 |

---

## 10. PEFT 微调参数（`--peft.*`）

> 配置类：`src/lerobot/configs/default.py` → `PeftConfig`
> 需要配合 `--policy.use_peft=True` 使用

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--peft.target_modules` | str \| list \| None | None | 需要适配的模块名称（后缀匹配或 `all-linear`）。部分策略有默认值 |
| `--peft.full_training_modules` | list \| None | None | 完全微调的模块名称（对应 PEFT 的 `modules_to_save`）。默认为策略新建的层 |
| `--peft.method_type` | str | "LORA" | PEFT 适配器方法类型（如 LORA、ADALORA 等） |
| `--peft.init_type` | str \| None | None | 适配器初始化方法（具体取决于 PEFT 适配器文档） |
| `--peft.r` | int | 16 | 适配器的秩（rank）。越高越接近全量微调，参数越多 |

---

## 11. RA-BC 参数（Reward-Aligned Behavior Cloning）

> 与 SARM 策略配合使用，通过预计算的进度权重对样本进行加权训练

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--use_rabc` | bool | False | 启用奖励加权训练 |
| `--rabc_progress_path` | str \| None | 自动推断 | 预计算的 SARM 进度 parquet 文件路径。自动推断规则：本地数据集 → `{root}/sarm_progress.parquet`；Hub → `hf://datasets/{repo_id}/sarm_progress.parquet` |
| `--rabc_kappa` | float | 0.01 | 高质量样本的硬阈值（低于此值的样本权重设为 0） |
| `--rabc_epsilon` | float | 1e-6 | 数值稳定性常数（防止分母为 0） |
| `--rabc_head_mode` | str | "sparse" | 双头模型模式：`sparse` 或 `dense` |

---

## 12. 其他参数

| CLI 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--cudnn_deterministic` | bool | False | True：使用确定性 cuDNN 算法（禁用 cudnn.benchmark），保证可复现但训练速度慢 10~20% |
| `--rename_map` | dict | {} | 重命名观测特征键的映射。如将 `observation.image` 改为 `observation.images.cam0`。影响预处理器的观测重命名 |

---

## 13. 使用示例

```bash
# 基础训练（ACT 策略，pusht 数据集）
uv run lerobot-train \
  --dataset.repo_id=lerobot/pusht \
  --policy=act \
  --env=pusht \
  --env.task=PushT-v0 \
  --steps=100000 \
  --batch_size=8

# 从预训练模型继续训练
uv run lerobot-train \
  --policy.path=lerobot/act_pusht \
  --dataset.repo_id=lerobot/pusht \
  --env=pusht \
  --env.task=PushT-v0 \
  --resume=True \
  --config_path=outputs/train/xxx/checkpoints/last/pretrained_model/train_config.json

# 自定义优化器和调度器
uv run lerobot-train \
  --dataset.repo_id=lerobot/pusht \
  --policy=act \
  --use_policy_training_preset=False \
  --optimizer.type=adamw \
  --optimizer.lr=5e-4 \
  --optimizer.weight_decay=0.01 \
  --optimizer.grad_clip_norm=10.0 \
  --scheduler.type=cosine_decay_with_warmup \
  --scheduler.num_warmup_steps=500 \
  --scheduler.num_decay_steps=100000 \
  --scheduler.peak_lr=5e-4 \
  --scheduler.decay_lr=1e-6

# 启用 WandB + 图像增强
uv run lerobot-train \
  --dataset.repo_id=lerobot/pusht \
  --policy=act \
  --wandb.enable=True \
  --wandb.project=my_project \
  --dataset.image_transforms.enable=True \
  --dataset.image_transforms.max_num_transforms=3

# PEFT 微调（LoRA）
uv run lerobot-train \
  --policy.path=lerobot/pi0_aloha \
  --policy.use_peft=True \
  --dataset.repo_id=my_dataset \
  --peft.method_type=LORA \
  --peft.r=16 \
  --peft.target_modules=all-linear

# 指定本地数据集 + 特定 episodes
uv run lerobot-train \
  --dataset.repo_id=my_dataset \
  --dataset.root=/path/to/local/dataset \
  --dataset.episodes='[0,1,2,3,4]' \
  --policy=act
```

---

## 14. 训练流程概览

1. **验证配置** → `cfg.validate()`（检查 policy、output_dir、optimizer 等）
2. **创建 Accelerator** → 自动检测多卡/单卡/CPU 模式
3. **设置随机种子** → 保证可复现性
4. **创建数据集** → 主进程先下载，其他进程等待后加载
5. **创建评估环境**（如有 env 配置）→ gym VectorEnv
6. **创建策略** → 从预训练加载或随机初始化
7. **创建 Processor** → 数据预处理/后处理管道（归一化、设备迁移等）
8. **创建优化器和调度器** → 基于策略 preset 或手动配置
9. **创建 DataLoader** → EpisodeAwareSampler（如策略需要 drop_n_last_frames）
10. **主训练循环** → 每步：取 batch → preprocessor → forward/backward → clip gradients → optimizer step
11. **定期操作** → log_freq 打印日志、save_freq 保存 checkpoint、eval_freq 评估策略
12. **训练结束** → 推送模型到 Hub（如配置）、清理分布式环境
