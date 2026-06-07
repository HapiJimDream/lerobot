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