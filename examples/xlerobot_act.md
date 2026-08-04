
# 0. 效果

# 1. 遥操作测试
```
lerobot-teleoperate
--robot.type=so101_follower
--robot.port=/dev/ttyRightArm
--robot.id=right_arm
--teleop.type=so101_leader
--teleop.port=/dev/ttyLeaderRight
--teleop.id=leader_right_arm
```

# 2. 单臂录制
```
lerobot-record \
   --robot.type=so101_follower \
   --robot.port=/dev/ttyRightArm \
   --robot.id=right_arm \
   --robot.cameras="{ head: {type: opencv, index_or_path: '/dev/camHead', width: 640, height: 480 , fps: 30},right: {type: opencv, index_or_path: '/dev/camRight', width: 640, height: 480 , fps: 30}}" \
   --teleop.type=so101_leader \
   --teleop.port=/dev/ttyLeaderRight \  
   --teleop.id=leader_right_arm \
   --display_data=true \
   --play_sounds=false \  
   --dataset.repo_id=jim1234321/pick_red_block0613 \
   --dataset.single_task="Put the red block into your own basket" \
   --dataset.num_episodes=20 \
   --dataset.push_to_hub=false \ 
   --dataset.streaming_encoding=true \
   --dataset.encoder_threads=3 \
   --dataset.vcodec=h264 \
   --dataset.reset_time_s=15 \
   --dataset.episode_time_s=30
```

# 3. 模型训练
```
  lerobot-train \
    --dataset.repo_id=jim1234321/pickred \
    --dataset.root=/home/oosv5xu-/AiSpace/pick_red_block0613_10_20260613_122119 \
    --policy.type=act \
    --policy.repo_id=jim1234321/pickred \
    --output_dir=outputs/train/pick_red_block \
    --batch_size=16 \
    --job_name=pick_red_block \
    --policy.device=cuda \
    --wandb.enable=true \
    --steps=30000
```

# 4. 推理运行
```
lerobot-rollout
--strategy.type=base
--policy.path=/home/jim/AiSpace/train/030000/pretrained_model
--robot.type=so101_follower
--robot.id=right_arm
--robot.port=/dev/ttyRightArm
--robot.cameras="{ head: {type: opencv, index_or_path: '/dev/camHead', width: 640, height: 480 , fps: 30},right: {type: opencv, index_or_path: '/dev/camRight', width: 640, height: 480 , fps: 30}}"
--policy.device=cpu
--task="Pick the red block"
--duration=90
--fps=15
```