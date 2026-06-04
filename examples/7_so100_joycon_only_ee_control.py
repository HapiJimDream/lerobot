#!/usr/bin/env python3
"""
Dual Joy-Con control for dual SO100/SO101 robots (no keyboard required)
适用于无图形界面环境 (headless environment)
使用左右 Joy-Con 手柄分别控制两个机械臂末端执行器
"""

import logging
import math
import time
import traceback
from joyconrobotics import JoyconRobotics

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Joint calibration coefficients
# Format: [joint_name, zero_position_offset(degrees), scale_factor]
JOINT_CALIBRATION = [
    ["shoulder_pan", 6.0, 1.0],
    ["shoulder_lift", 2.0, 0.97],
    ["elbow_flex", 0.0, 1.05],
    ["wrist_flex", 0.0, 0.94],
    ["wrist_roll", 0.0, 0.5],
    ["gripper", 0.0, 1.0],
]

class FixedAxesJoyconRobotics(JoyconRobotics):
    """Joy-Con 控制类 - 只使用手柄,不依赖键盘"""
    def __init__(self, device, **kwargs):
        super().__init__(device, **kwargs)

        # 左右 Joy-Con 摇杆的物理静止读数不同,必须分别设置中心值,
        # 否则一侧会被误判为「一直在推」而持续漂移(左臂往前漂、控制艰难)。
        # 左右用各自正确的中心后,两臂控制节奏才一致。
        if self.joycon.is_right():
            self.joycon_stick_v_0 = 1900
            self.joycon_stick_h_0 = 2100
        else:  # 左 Joy-Con
            self.joycon_stick_v_0 = 2300
            self.joycon_stick_h_0 = 2000

    def common_update(self):
        speed_scale = 0.0008

        # 垂直摇杆：控制X轴(前后)和Z轴
        joycon_stick_v = self.joycon.get_stick_right_vertical() if self.joycon.is_right() else self.joycon.get_stick_left_vertical()
        joycon_stick_v_0 = self.joycon_stick_v_0
        joycon_stick_v_threshold = 300
        joycon_stick_v_range = 1000
        if joycon_stick_v > joycon_stick_v_threshold + joycon_stick_v_0:
            self.position[0] += speed_scale * (joycon_stick_v - joycon_stick_v_0) / joycon_stick_v_range * self.dof_speed[0] * self.direction_reverse[0] * self.direction_vector[0]
            self.position[2] += speed_scale * (joycon_stick_v - joycon_stick_v_0) / joycon_stick_v_range * self.dof_speed[1] * self.direction_reverse[1] * self.direction_vector[2]
        elif joycon_stick_v < joycon_stick_v_0 - joycon_stick_v_threshold:
            self.position[0] += speed_scale * (joycon_stick_v - joycon_stick_v_0) / joycon_stick_v_range * self.dof_speed[0] * self.direction_reverse[0] * self.direction_vector[0]
            self.position[2] += speed_scale * (joycon_stick_v - joycon_stick_v_0) / joycon_stick_v_range * self.dof_speed[1] * self.direction_reverse[1] * self.direction_vector[2]

        # 水平摇杆：控制Y轴(左右)
        joycon_stick_h = self.joycon.get_stick_right_horizontal() if self.joycon.is_right() else self.joycon.get_stick_left_horizontal()
        joycon_stick_h_0 = self.joycon_stick_h_0
        joycon_stick_h_threshold = 300
        joycon_stick_h_range = 1000
        if joycon_stick_h > joycon_stick_h_threshold + joycon_stick_h_0:
            self.position[1] += speed_scale * (joycon_stick_h - joycon_stick_h_0) / joycon_stick_h_range * self.dof_speed[1] * self.direction_reverse[1]
        elif joycon_stick_h < joycon_stick_h_0 - joycon_stick_h_threshold:
            self.position[1] += speed_scale * (joycon_stick_h - joycon_stick_h_0) / joycon_stick_h_range * self.dof_speed[1] * self.direction_reverse[1]
        
        # R按钮: Z轴上升
        joycon_button_up = self.joycon.get_button_r() if self.joycon.is_right() else self.joycon.get_button_l()
        if joycon_button_up == 1:
            self.position[2] += speed_scale * self.dof_speed[2] * self.direction_reverse[2]
        
        # 摇杆按钮: Z轴下降
        joycon_button_down = self.joycon.get_button_r_stick() if self.joycon.is_right() else self.joycon.get_button_l_stick()
        if joycon_button_down == 1:
            self.position[2] -= speed_scale * self.dof_speed[2] * self.direction_reverse[2]

        # X/B按钮: 微调X轴
        joycon_button_xup = self.joycon.get_button_x() if self.joycon.is_right() else self.joycon.get_button_up()
        joycon_button_xback = self.joycon.get_button_b() if self.joycon.is_right() else self.joycon.get_button_down()
        if joycon_button_xup == 1:
            self.position[0] += 0.001 * self.dof_speed[0]
        elif joycon_button_xback == 1:
            self.position[0] -= 0.001 * self.dof_speed[0]
        
        # Home按钮: 重置位置
        joycon_button_home = self.joycon.get_button_home() if self.joycon.is_right() else self.joycon.get_button_capture()
        if joycon_button_home == 1:
            self.position = self.offset_position_m.copy()
        
        # 夹爪控制逻辑
        for event_type, status in self.button.events():
            if (self.joycon.is_right() and event_type == 'plus' and status == 1) or (self.joycon.is_left() and event_type == 'minus' and status == 1):
                self.reset_button = 1
                self.reset_joycon()
            elif self.joycon.is_right() and event_type == 'a':
                self.next_episode_button = status
            elif self.joycon.is_right() and event_type == 'y':
                self.restart_episode_button = status
            elif ((self.joycon.is_right() and event_type == 'zr') or (self.joycon.is_left() and event_type == 'zl')) and not self.change_down_to_gripper:
                self.gripper_toggle_button = status
            elif ((self.joycon.is_right() and event_type == 'stick_r_btn') or (self.joycon.is_left() and event_type == 'stick_l_btn')) and self.change_down_to_gripper:
                self.gripper_toggle_button = status
            else: 
                self.reset_button = 0
            
        if self.gripper_toggle_button == 1:
            if self.gripper_state == self.gripper_open:
                self.gripper_state = self.gripper_close
            else:
                self.gripper_state = self.gripper_open
            self.gripper_toggle_button = 0

        # 按钮控制状态
        if self.joycon.is_right():
            if self.next_episode_button == 1:
                self.button_control = 1
            elif self.restart_episode_button == 1:
                self.button_control = -1
            elif self.reset_button == 1:
                self.button_control = 8
            else:
                self.button_control = 0
        
        return self.position, self.gripper_state, self.button_control


def apply_joint_calibration(joint_name, raw_position):
    """Apply joint calibration coefficients"""
    for calibration in JOINT_CALIBRATION:
        if calibration[0] == joint_name:
            zero_offset = calibration[1]
            scale_factor = calibration[2]
            return (raw_position + zero_offset) * scale_factor
    return raw_position


def inverse_kinematics(x, y):
    """
    简单的2D逆运动学求解
    计算shoulder_lift和elbow_flex的目标角度
    """
    # 机械臂参数 (米)
    l1 = 0.12  # 上臂长度
    l2 = 0.12  # 前臂长度
    
    # 计算到目标的距离
    r = math.sqrt(x**2 + y**2)
    
    # 检查是否可达
    if r > l1 + l2:
        r = l1 + l2 - 0.001
    
    # 余弦定理计算角度
    try:
        cos_angle2 = (r**2 - l1**2 - l2**2) / (2 * l1 * l2)
        cos_angle2 = max(-1.0, min(1.0, cos_angle2))  # 限制范围
        angle2 = math.acos(cos_angle2)
        
        angle1 = math.atan2(y, x) - math.atan2(l2 * math.sin(angle2), l1 + l2 * math.cos(angle2))
        
        # 转换为角度
        joint2_deg = math.degrees(angle1)
        joint3_deg = math.degrees(angle2)
        
        return joint2_deg, joint3_deg
    except:
        return 0.0, 0.0


def compute_joycon_targets(pose):
    """把一次 Joy-Con pose 映射成 5 个手臂关节的目标角度(夹爪单独处理)。

    基准姿态与控制循环共用同一映射,保证「以初始姿态为基准」的偏移计算一致。
    """
    x, y, z, roll_, pitch_, yaw = pose
    pitch = -pitch_ * 60 + 20
    current_x = 0.1629 + x
    current_y = 0.1131 + z
    roll = roll_ * 50

    shoulder_pan = y * 300.0  # Joy-Con 的 y 值控制 shoulder_pan
    joint2_target, joint3_target = inverse_kinematics(current_x, current_y)
    wrist_flex = -joint2_target - joint3_target + pitch
    return {
        "shoulder_pan": shoulder_pan,
        "shoulder_lift": joint2_target,
        "elbow_flex": joint3_target,
        "wrist_flex": wrist_flex,
        "wrist_roll": roll,
    }


def move_to_zero_position(robot, target_positions, duration=3.0, control_freq=50):
    """
    使用P控制缓慢移动到零位
    """
    print(f"Moving to zero position using P control over {duration} seconds...")
    kp = 0.5
    control_period = 1.0 / control_freq
    total_steps = int(duration * control_freq)
    
    for step in range(total_steps):
        progress = (step + 1) / total_steps * 100
        if step % 10 == 0:
            print(f"Moving to zero position progress: {progress:.1f}%")
        
        current_obs = robot.get_observation()
        robot_action = {}
        
        for key, value in current_obs.items():
            if key.endswith(".pos"):
                motor_name = key.removesuffix(".pos")
                current_pos = apply_joint_calibration(motor_name, value)
                target_pos = target_positions.get(motor_name, current_pos)
                
                error = target_pos - current_pos
                control_output = kp * error
                new_position = current_pos + control_output
                
                robot_action[f"{motor_name}.pos"] = new_position
        
        if robot_action:
            robot.send_action(robot_action)
        
        time.sleep(control_period)
    
    print("Robot has moved to zero position")


def p_control_loop(robot, target_positions, joyconrobotics, initial_positions=None, arm_name="arm1", kp=0.5, control_freq=50):
    """
    纯Joy-Con控制的P控制循环(无键盘依赖)

    Args:
        robot: 机器人实例
        target_positions: 目标位置字典
        joyconrobotics: Joy-Con控制器实例
        initial_positions: 上电时的初始关节角(用于把摇杆中立锚定到初始姿态)
        arm_name: 机械臂名称(用于日志输出)
        kp: 比例增益
        control_freq: 控制频率(Hz)
    """
    control_period = 1.0 / control_freq

    # 选项A:以启动时的真实姿态为基准。读一次 Joy-Con 当前读数,算出它对应的
    # 关节目标,用「初始关节角 - 该目标」得到偏移;之后每帧把摇杆目标加上该偏移,
    # 于是中立读数恰好映射到初始姿态,启动瞬间机械臂保持静止、不归零、不跳动。
    arm_joints = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
    joint_offset = {j: 0.0 for j in arm_joints}
    if initial_positions:
        init_pose, _, _ = joyconrobotics.get_control()
        neutral_targets = compute_joycon_targets(init_pose)
        for j in arm_joints:
            joint_offset[j] = initial_positions.get(j, neutral_targets[j]) - neutral_targets[j]
        print(f"{arm_name} 已锚定到初始姿态,启动保持静止")

    print(f"Starting P control loop for {arm_name}, control frequency: {control_freq}Hz, proportional gain: {kp}")
    print(f"{arm_name} Joy-Con Control:")
    print("  - Right Stick: X/Y axis control")
    print("  - R Button: Z up")
    print("  - Stick Button: Z down")
    print("  - ZR: Toggle gripper")
    print("  - Home: Reset position")
    print("  - Ctrl+C: Exit")

    while True:
        try:
            # 只获取Joy-Con输入
            pose, gripper, control_button = joyconrobotics.get_control()

            # 摇杆 -> 关节目标,并叠加初始姿态偏移(选项A:相对初始姿态控制)
            joycon_targets = compute_joycon_targets(pose)
            for joint_name, value in joycon_targets.items():
                target_positions[joint_name] = value + joint_offset[joint_name]

            # 夹爪控制
            if gripper == 1:
                target_positions["gripper"] = 60
            else:
                target_positions["gripper"] = 0
            
            # 获取机器人当前状态
            current_obs = robot.get_observation()

            # 提取当前关节位置
            current_positions = {}
            for key, value in current_obs.items():
                if key.endswith(".pos"):
                    motor_name = key.removesuffix(".pos")
                    calibrated_value = apply_joint_calibration(motor_name, value)
                    current_positions[motor_name] = calibrated_value

            # P控制计算
            robot_action = {}
            for joint_name, target_pos in target_positions.items():
                if joint_name in current_positions:
                    current_pos = current_positions[joint_name]
                    error = target_pos - current_pos
                    control_output = kp * error
                    new_position = current_pos + control_output
                    robot_action[f"{joint_name}.pos"] = new_position

            # 发送控制指令
            if robot_action:
                robot.send_action(robot_action)

            time.sleep(control_period)

        except KeyboardInterrupt:
            print("\nUser interrupted program")
            break
        except Exception as e:
            print(f"P control loop error: {e}")
            traceback.print_exc()
            break


def main():
    try:
        print("Dual Joy-Con Only Dual-Arm SO100 Control (No Keyboard Required)")
        print("=" * 60)

        from lerobot.robots.so_follower.so_follower import SO100Follower
        from lerobot.robots.so_follower.config_so_follower import SO100FollowerConfig

        # 获取端口
        print("\n=== 配置机械臂端口 ===")
        print("右臂 (由右Joy-Con控制):")
        port1 = input("  请输入右臂SO100机器人的USB端口 (例如: /dev/ttyACM0): ").strip()
        if not port1:
            port1 = "/dev/ttyACM0"
            print(f"  使用右臂默认端口: {port1}")
        else:
            print(f"  右臂将连接到端口: {port1}")
        
        print("\n左臂 (由左Joy-Con控制):")
        port2 = input("  请输入左臂SO100机器人的USB端口 (例如: /dev/ttyACM1): ").strip()
        if not port2:
            port2 = "/dev/ttyACM1"
            print(f"  使用左臂默认端口: {port2}")
        else:
            print(f"  左臂将连接到端口: {port2}")

        # 配置机器人
        print(f"\n配置右臂机器人 (端口: {port1})...")
        robot1_config = SO100FollowerConfig(port=port1)
        print(f"配置左臂机器人 (端口: {port2})...")
        robot2_config = SO100FollowerConfig(port=port2)
        robot1 = SO100Follower(robot1_config)
        robot2 = SO100Follower(robot2_config)

        # 连接机器人
        print("\n连接右臂机器人...")
        robot1.connect()
        print("连接左臂机器人...")
        robot2.connect()
        
        # 初始化双Joy-Con控制器
        joyconrobotics_right = FixedAxesJoyconRobotics(
            "right",
            dof_speed=[2, 2, 2, 1, 1, 1]
        )
        joyconrobotics_left = FixedAxesJoyconRobotics(
            "left",
            dof_speed=[2, 2, 2, 1, 1, 1]
        )

        print("\n=== Joy-Con 控制说明 ===")
        print("\n[右Joy-Con - 控制右臂]")
        print("  垂直摇杆: 只控制X轴(前后)")
        print("  水平摇杆: 只控制Y轴(左右)")
        print("  R按钮: Z轴上升")
        print("  摇杆按钮: Z轴下降")
        print("  Home按钮: 重置位置")
        print("  ZR按钮: 切换夹爪")
        print("\n[左Joy-Con - 控制左臂]")
        print("  垂直摇杆: 只控制X轴(前后)")
        print("  水平摇杆: 只控制Y轴(左右)")
        print("  L按钮: Z轴上升")
        print("  摇杆按钮: Z轴下降")
        print("  Capture按钮: 重置位置")
        print("  ZL按钮: 切换夹爪")
        print("\n按Ctrl+C停止\n")

        # 校准
        recalibrate = input("是否重新校准两个机械臂? (y/n): ").strip().lower()
        if recalibrate == 'y':
            print("请按照校准说明进行操作...")
            # 这里可以添加校准逻辑
        else:
            print("使用之前的校准数据")

        # 读取初始关节角度
        print("\n读取两个机械臂的初始关节角度...")
        
        # 右臂
        print("\n右臂初始关节角度:")
        current_obs1 = robot1.get_observation()
        initial_positions1 = {}
        for key, value in current_obs1.items():
            if key.endswith(".pos"):
                motor_name = key.removesuffix(".pos")
                calibrated_value = apply_joint_calibration(motor_name, value)
                initial_positions1[motor_name] = calibrated_value
                print(f"  {motor_name}: {calibrated_value:.0f}°")
        
        # 左臂
        print("\n左臂初始关节角度:")
        current_obs2 = robot2.get_observation()
        initial_positions2 = {}
        for key, value in current_obs2.items():
            if key.endswith(".pos"):
                motor_name = key.removesuffix(".pos")
                calibrated_value = apply_joint_calibration(motor_name, value)
                initial_positions2[motor_name] = calibrated_value
                print(f"  {motor_name}: {calibrated_value:.0f}°")

        # 目标位置(零位)
        target_positions1 = {
            "shoulder_pan": 0.0,
            "shoulder_lift": 0.0,
            "elbow_flex": 0.0,
            "wrist_flex": 0.0,
            "wrist_roll": 0.0,
            "gripper": 60.0,
        }
        target_positions2 = {
            "shoulder_pan": 0.0,
            "shoulder_lift": 0.0,
            "elbow_flex": 0.0,
            "wrist_flex": 0.0,
            "wrist_roll": 0.0,
            "gripper": 60.0,
        }

        # 选项A:启动时不强制归零,两臂保持上电时的初始静态姿态。
        # 摇杆中立会被锚定到该初始姿态(见 p_control_loop 中的 joint_offset)。
        print("\n启动时保持两臂初始静态姿态(不归零)")

        # 使用多线程启动双控制循环
        import threading

        def control_right_arm():
            """控制右臂的线程函数"""
            p_control_loop(
                robot1, target_positions1, joyconrobotics_right,
                initial_positions=initial_positions1,
                arm_name="右臂", kp=0.5, control_freq=50
            )

        def control_left_arm():
            """控制左臂的线程函数"""
            p_control_loop(
                robot2, target_positions2, joyconrobotics_left,
                initial_positions=initial_positions2,
                arm_name="左臂", kp=0.5, control_freq=50
            )
        
        print("\n启动双臂控制...")
        thread1 = threading.Thread(target=control_right_arm, daemon=True)
        thread2 = threading.Thread(target=control_left_arm, daemon=True)
        
        thread1.start()
        thread2.start()
        
        # 主线程等待(处理KeyboardInterrupt)
        try:
            while thread1.is_alive() and thread2.is_alive():
                thread1.join(timeout=1.0)
                thread2.join(timeout=1.0)
        except KeyboardInterrupt:
            print("\nUser interrupted program")

        # 断开连接
        print("\n断开机械臂连接...")
        robot1.disconnect()
        robot2.disconnect()
        print("程序成功结束")

    except Exception as e:
        print(f"程序执行失败: {e}")
        traceback.print_exc()
        print("\n请检查:")
        print("1. 两个机械臂是否正确连接")
        print("2. USB端口是否正确")
        print("3. 是否有足够的权限访问USB设备")
        print("4. 两个Joy-Con是否已通过蓝牙连接")


if __name__ == "__main__":
    main()
