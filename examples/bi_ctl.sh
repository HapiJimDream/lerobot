#!/usr/bin/env bash
lerobot-teleoperate \
  --robot.type=bi_so_follower \
  --robot.left_arm_config.port=/dev/ttyLeftArm \
  --robot.right_arm_config.port=/dev/ttyRightArm \
  --robot.id=bimanual_follower \
   --robot.left_arm_config.cameras="{
     head: {type: opencv, index_or_path: '/dev/camHead', width: 640, height: 480 , fps: 30},
     left: {type: opencv, index_or_path: '/dev/camLeft', width: 640, height: 480 , fps: 30}
  }" \
  --robot.right_arm_config.cameras="{
     right: {type: opencv, index_or_path: '/dev/camRight', width: 640, height: 480 , fps: 30}
  }" \
  --teleop.type=bi_so_leader \
  --teleop.left_arm_config.port=/dev/ttyLeaderLeft \
  --teleop.right_arm_config.port=/dev/ttyLeaderRight \
  --teleop.id=bimanual_leader \
  --display_data=true
