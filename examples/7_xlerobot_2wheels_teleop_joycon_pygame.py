# To Run on the host
'''
PYTHONPATH=src python -m lerobot.robots.xlerobot_2wheels.xlerobot_2wheels_host --robot.id=my_xlerobot_2wheels
'''

# To Run the teleop:
'''
PYTHONPATH=src python examples/7_xlerobot_2wheels_teleop_joycon_pygame.py
'''

# Base speed control instructions:
# - When holding any base control button, speed will linearly accelerate to maximum speed
# - After releasing the button, speed will linearly decelerate to 0
# - You can adjust the acceleration and deceleration slopes by modifying the following parameters:
#   * BASE_ACCELERATION_RATE: acceleration slope (speed/second)
#   * BASE_DECE
import numpy as np
import math
import pygame
import time

from lerobot.robots.xlerobot_2wheels import XLerobot2WheelsConfig, XLerobot2Wheels
from lerobot.utils.robot_utils import precise_sleep
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data
from lerobot.model.SO101Robot import SO101Kinematics

# Base speed control parameters - adjustable slopes
BASE_ACCELERATION_RATE = 10.0  # acceleration slope (speed/second)
BASE_DECELERATION_RATE = 10.0  # deceleration slope (speed/second)
BASE_MAX_SPEED = 5.0          # maximum speed multiplier
MIN_VELOCITY_THRESHOLD = 0.02 # minimum velocity to send to motors during deceleration

# Joy-Con Button Mapping (via Parallels Xbox emulation)
# Based on readme.md mapping:
# L: 上:11, 下:12, 左:13, 右:14, ⭕️:15, L:9,-:4, 左摇杆X:轴0, 左摇杆Y:轴1, ZL:轴4
# R: A:0, B:1, X:2,Y:3,主页:5,+:6,R:10,右摇杆X:轴2,右摇杆Y:轴3,ZR:轴5


# Keymaps for Joy-Con via pygame (Xbox mapped)
LEFT_KEYMAP = {
    # Left stick controls left arm XY
    'x+': 'left_stick_up', 'x-': 'left_stick_down',
    'y+': 'left_stick_right', 'y-': 'left_stick_left',
    # L button (9) pressed controls shoulder_pan
    'shoulder_pan+': 'l_pressed_right', 'shoulder_pan-': 'l_pressed_left',
    # ZL (axis4) controls pitch and wrist_roll
    'pitch+': 'zl_up', 'pitch-': 'zl_down',
    'wrist_roll+': 'zl_right', 'wrist_roll-': 'zl_left',
    # ZL trigger controls left gripper
    'gripper+': 'left_trigger',
    # Head motors (X:2, B:1, A:0, Y:3)
    "head_motor_1+": 'x', "head_motor_1-": 'b',
    "head_motor_2+": 'a', "head_motor_2-": 'y',
}

RIGHT_KEYMAP = {
    # Right stick controls right arm XY
    'x+': 'right_stick_up', 'x-': 'right_stick_down',
    'y+': 'right_stick_right', 'y-': 'right_stick_left',
    # R button (10) pressed controls shoulder_pan
    'shoulder_pan+': 'r_pressed_right', 'shoulder_pan-': 'r_pressed_left',
    # ZR (axis5) controls pitch and wrist_roll
    'pitch+': 'zr_up', 'pitch-': 'zr_down',
    'wrist_roll+': 'zr_right', 'wrist_roll-': 'zr_left',
    # ZR trigger controls right gripper
    'gripper+': 'right_trigger',
}

# Base control keymap - Joy-Con direction keys (11-14)
BASE_KEYMAP = {
    'forward': 'dpad_up',      # 11
    'backward': 'dpad_down',   # 12
    'rotate_left': 'dpad_left', # 13
    'rotate_right': 'dpad_right', # 14
}

# Global reset key - Capture button (15)
RESET_KEY = 'capture'

LEFT_JOINT_MAP = {
    "shoulder_pan": "left_arm_shoulder_pan",
    "shoulder_lift": "left_arm_shoulder_lift",
    "elbow_flex": "left_arm_elbow_flex",
    "wrist_flex": "left_arm_wrist_flex",
    "wrist_roll": "left_arm_wrist_roll",
    "gripper": "left_arm_gripper",
}

RIGHT_JOINT_MAP = {
    "shoulder_pan": "right_arm_shoulder_pan",
    "shoulder_lift": "right_arm_shoulder_lift",
    "elbow_flex": "right_arm_elbow_flex",
    "wrist_flex": "right_arm_wrist_flex",
    "wrist_roll": "right_arm_wrist_roll",
    "gripper": "right_arm_gripper",
}

HEAD_MOTOR_MAP = {
    "head_motor_1": "head_motor_1",
    "head_motor_2": "head_motor_2",
}


class SimpleHeadControl:
    def __init__(self, initial_obs, kp=1):
        self.kp = kp
        self.degree_step = 2
        self.target_positions = {
            "head_motor_1": initial_obs.get("head_motor_1.pos", 0.0),
            "head_motor_2": initial_obs.get("head_motor_2.pos", 0.0),
        }
        self.zero_pos = {"head_motor_1": 0.0, "head_motor_2": 0.0}

    def move_to_zero_position(self, robot):
        self.target_positions = self.zero_pos.copy()
        action = self.p_control_action(robot)
        robot.send_action(action)

    def handle_keys(self, key_state):
        if key_state.get('head_motor_1+'):
            self.target_positions["head_motor_1"] += self.degree_step
            print(f"[HEAD] head_motor_1: {self.target_positions['head_motor_1']}")
        if key_state.get('head_motor_1-'):
            self.target_positions["head_motor_1"] -= self.degree_step
            print(f"[HEAD] head_motor_1: {self.target_positions['head_motor_1']}")
        if key_state.get('head_motor_2+'):
            self.target_positions["head_motor_2"] += self.degree_step
            print(f"[HEAD] head_motor_2: {self.target_positions['head_motor_2']}")
        if key_state.get('head_motor_2-'):
            self.target_positions["head_motor_2"] -= self.degree_step
            print(f"[HEAD] head_motor_2: {self.target_positions['head_motor_2']}")

    def p_control_action(self, robot):
        obs = robot.get_observation()
        action = {}
        for motor in self.target_positions:
            current = obs.get(f"{HEAD_MOTOR_MAP[motor]}.pos", 0.0)
            error = self.target_positions[motor] - current
            control = self.kp * error
            action[f"{HEAD_MOTOR_MAP[motor]}.pos"] = current + control
        return action


class SimpleTeleopArm:
    def __init__(self, kinematics, joint_map, initial_obs, prefix="left", kp=1):
        self.kinematics = kinematics
        self.joint_map = joint_map
        self.prefix = prefix
        self.kp = kp
        self.joint_positions = {
            "shoulder_pan": initial_obs[f"{prefix}_arm_shoulder_pan.pos"],
            "shoulder_lift": initial_obs[f"{prefix}_arm_shoulder_lift.pos"],
            "elbow_flex": initial_obs[f"{prefix}_arm_elbow_flex.pos"],
            "wrist_flex": initial_obs[f"{prefix}_arm_wrist_flex.pos"],
            "wrist_roll": initial_obs[f"{prefix}_arm_wrist_roll.pos"],
            "gripper": initial_obs[f"{prefix}_arm_gripper.pos"],
        }
        self.current_x = 0.1629
        self.current_y = 0.1131
        self.pitch = 0.0
        self.degree_step = 2
        self.xy_step = 0.005
        self.target_positions = {
            "shoulder_pan": 0.0,
            "shoulder_lift": 0.0,
            "elbow_flex": 0.0,
            "wrist_flex": 0.0,
            "wrist_roll": 0.0,
            "gripper": 0.0,
        }
        self.zero_pos = {
            'shoulder_pan': 0.0,
            'shoulder_lift': 0.0,
            'elbow_flex': 0.0,
            'wrist_flex': 0.0,
            'wrist_roll': 0.0,
            'gripper': 0.0
        }

    def move_to_zero_position(self, robot):
        print(f"[{self.prefix}] Moving to Zero Position: {self.zero_pos} ......")
        self.target_positions = self.zero_pos.copy()
        self.current_x = 0.1629
        self.current_y = 0.1131
        self.pitch = 0.0
        self.target_positions["wrist_flex"] = 0.0
        action = self.p_control_action(robot)
        robot.send_action(action)

    def handle_keys(self, key_state):
        if key_state.get('shoulder_pan+'):
            self.target_positions["shoulder_pan"] += self.degree_step
            print(f"[{self.prefix}] shoulder_pan: {self.target_positions['shoulder_pan']}")
        if key_state.get('shoulder_pan-'):
            self.target_positions["shoulder_pan"] -= self.degree_step
            print(f"[{self.prefix}] shoulder_pan: {self.target_positions['shoulder_pan']}")
        if key_state.get('wrist_roll+'):
            self.target_positions["wrist_roll"] += self.degree_step
            print(f"[{self.prefix}] wrist_roll: {self.target_positions['wrist_roll']}")
        if key_state.get('wrist_roll-'):
            self.target_positions["wrist_roll"] -= self.degree_step
            print(f"[{self.prefix}] wrist_roll: {self.target_positions['wrist_roll']}")
        
        if key_state.get('gripper+'):
            self.target_positions["gripper"] = 2
            print(f"[{self.prefix}] gripper: CLOSED")
        else:
            self.target_positions["gripper"] = 90
        
        if key_state.get('pitch+'):
            self.pitch += self.degree_step
            print(f"[{self.prefix}] pitch: {self.pitch}")
        if key_state.get('pitch-'):
            self.pitch -= self.degree_step
            print(f"[{self.prefix}] pitch: {self.pitch}")

        moved = False
        if key_state.get('x+'):
            self.current_x += self.xy_step
            moved = True
        if key_state.get('x-'):
            self.current_x -= self.xy_step
            moved = True
        if key_state.get('y+'):
            self.current_y += self.xy_step
            moved = True
        if key_state.get('y-'):
            self.current_y -= self.xy_step
            moved = True
        if moved:
            joint2, joint3 = self.kinematics.inverse_kinematics(self.current_x, self.current_y)
            self.target_positions["shoulder_lift"] = joint2
            self.target_positions["elbow_flex"] = joint3

        self.target_positions["wrist_flex"] = (
            -self.target_positions["shoulder_lift"]
            -self.target_positions["elbow_flex"]
            + self.pitch
        )

    def p_control_action(self, robot):
        obs = robot.get_observation()
        current = {j: obs[f"{self.prefix}_arm_{j}.pos"] for j in self.joint_map}
        action = {}
        for j in self.target_positions:
            error = self.target_positions[j] - current[j]
            control = self.kp * error
            action[f"{self.joint_map[j]}.pos"] = current[j] + control
        return action


class SmoothBaseController:
    """Simplified smooth base controller with acceleration/deceleration"""
    
    def __init__(self):
        self.current_speed = 0.0
        self.last_time = time.time()
        self.last_direction = {"x.vel": 0.0, "theta.vel": 0.0}
        self.is_moving = False
        self.has_reported_stopped = True
    
    def update(self, pressed_keys, robot):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        base_keys = [
            robot.teleop_keys['forward'],
            robot.teleop_keys['backward'], 
            robot.teleop_keys['rotate_left'],
            robot.teleop_keys['rotate_right']
        ]
        any_key_pressed = any(key in pressed_keys for key in base_keys)
        
        base_action = {"x.vel": 0.0, "theta.vel": 0.0}
        
        if any_key_pressed:
            if not self.is_moving:
                self.is_moving = True
                self.has_reported_stopped = False
                print("[BASE] Starting acceleration")
            
            speed_setting = robot.speed_levels[robot.speed_index]
            linear_speed = speed_setting["linear"]
            angular_speed = speed_setting["angular"]
            
            if robot.teleop_keys["forward"] in pressed_keys:
                base_action["x.vel"] += linear_speed
            if robot.teleop_keys["backward"] in pressed_keys:
                base_action["x.vel"] -= linear_speed
            if robot.teleop_keys["rotate_left"] in pressed_keys:
                base_action["theta.vel"] += angular_speed
            if robot.teleop_keys["rotate_right"] in pressed_keys:
                base_action["theta.vel"] -= angular_speed
            
            self.last_direction = base_action.copy()
            self.current_speed += BASE_ACCELERATION_RATE * dt
            self.current_speed = min(self.current_speed, BASE_MAX_SPEED)
        else:
            if self.is_moving:
                self.is_moving = False
                print("[BASE] Starting deceleration")
            
            if self.current_speed > 0.01 and self.last_direction:
                base_action = self.last_direction.copy()
            
            self.current_speed -= BASE_DECELERATION_RATE * dt
            self.current_speed = max(self.current_speed, 0.0)
        
        if base_action:
            for key in base_action:
                if 'vel' in key:
                    original_value = base_action[key]
                    base_action[key] *= self.current_speed
                    if self.current_speed > 0.01 and abs(base_action[key]) < MIN_VELOCITY_THRESHOLD:
                        base_action[key] = MIN_VELOCITY_THRESHOLD if original_value > 0 else -MIN_VELOCITY_THRESHOLD
        
        if self.current_speed <= 0.01 and not self.has_reported_stopped:
            self.has_reported_stopped = True
            print(f"[BASE] STOPPED: Speed={self.current_speed:.2f}")
        
        return base_action


# Global smooth controller instance
smooth_controller = SmoothBaseController()


def get_joycon_key_state(joystick, keymap):
    """
    Map Joy-Con controller state (via Parallels Xbox emulation) to semantic actions.
    Based on readme.md mapping for Joy-Con via pygame.
    """
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    
    # Joy-Con specific button states
    l_pressed = bool(buttons[9]) if len(buttons) > 9 else False   # L button
    r_pressed = bool(buttons[10]) if len(buttons) > 10 else False  # R button
    
    # ZL/ZR trigger states (axis 4 and 5)
    zl_pressed = axes[4] > 0.5 if len(axes) > 4 else False
    zr_pressed = axes[5] > 0.5 if len(axes) > 5 else False

    state = {}
    for action, control in keymap.items():
        # Trigger controls - ZL/ZR
        if control == 'left_trigger':
            state[action] = axes[4] > 0.5 if len(axes) > 4 else False
        elif control == 'right_trigger':
            state[action] = axes[5] > 0.5 if len(axes) > 5 else False
        # Face buttons - A:0, B:1, X:2, Y:3
        elif control == 'a':
            state[action] = bool(buttons[0])
        elif control == 'b':
            state[action] = bool(buttons[1])
        elif control == 'x':
            state[action] = bool(buttons[2])
        elif control == 'y':
            state[action] = bool(buttons[3])
        # D-pad buttons - 上:11, 下:12, 左:13, 右:14
        elif control == 'dpad_up':
            state[action] = bool(buttons[11]) if len(buttons) > 11 else False
        elif control == 'dpad_down':
            state[action] = bool(buttons[12]) if len(buttons) > 12 else False
        elif control == 'dpad_left':
            state[action] = bool(buttons[13]) if len(buttons) > 13 else False
        elif control == 'dpad_right':
            state[action] = bool(buttons[14]) if len(buttons) > 14 else False
        # Left stick controls - axis 0 (X), axis 1 (Y)
        elif control == 'left_stick_up':
            state[action] = (not l_pressed) and (axes[1] < -0.5) if len(axes) > 1 else False
        elif control == 'left_stick_down':
            state[action] = (not l_pressed) and (axes[1] > 0.5) if len(axes) > 1 else False
        elif control == 'left_stick_left':
            state[action] = (not l_pressed) and (axes[0] < -0.5) if len(axes) > 0 else False
        elif control == 'left_stick_right':
            state[action] = (not l_pressed) and (axes[0] > 0.5) if len(axes) > 0 else False
        # Right stick controls - axis 2 (X), axis 3 (Y)
        elif control == 'right_stick_up':
            state[action] = (not r_pressed) and (axes[3] < -0.5) if len(axes) > 3 else False
        elif control == 'right_stick_down':
            state[action] = (not r_pressed) and (axes[3] > 0.5) if len(axes) > 3 else False
        elif control == 'right_stick_left':
            state[action] = (not r_pressed) and (axes[2] < -0.5) if len(axes) > 2 else False
        elif control == 'right_stick_right':
            state[action] = (not r_pressed) and (axes[2] > 0.5) if len(axes) > 2 else False
        # L/R pressed controls
        elif control == 'l_pressed_right':
            state[action] = l_pressed and (axes[0] > 0.5) if len(axes) > 0 else False
        elif control == 'l_pressed_left':
            state[action] = l_pressed and (axes[0] < -0.5) if len(axes) > 0 else False
        elif control == 'r_pressed_right':
            state[action] = r_pressed and (axes[2] > 0.5) if len(axes) > 2 else False
        elif control == 'r_pressed_left':
            state[action] = r_pressed and (axes[2] < -0.5) if len(axes) > 2 else False
        # ZL pressed controls
        elif control == 'zl_up':
            state[action] = zl_pressed and (axes[1] < -0.5) if len(axes) > 1 else False
        elif control == 'zl_down':
            state[action] = zl_pressed and (axes[1] > 0.5) if len(axes) > 1 else False
        elif control == 'zl_right':
            state[action] = zl_pressed and (axes[0] > 0.5) if len(axes) > 0 else False
        elif control == 'zl_left':
            state[action] = zl_pressed and (axes[0] < -0.5) if len(axes) > 0 else False
        # ZR pressed controls
        elif control == 'zr_up':
            state[action] = zr_pressed and (axes[3] < -0.5) if len(axes) > 3 else False
        elif control == 'zr_down':
            state[action] = zr_pressed and (axes[3] > 0.5) if len(axes) > 3 else False
        elif control == 'zr_right':
            state[action] = zr_pressed and (axes[2] > 0.5) if len(axes) > 2 else False
        elif control == 'zr_left':
            state[action] = zr_pressed and (axes[2] < -0.5) if len(axes) > 2 else False
        else:
            state[action] = False
    return state


def get_base_action_from_joycon(joystick, robot):
    """
    Get base action from Joy-Con direction keys for differential drive.
    """
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    
    pressed_keys = set()
    
    # Joy-Con direction keys: 上11, 下12, 左13, 右14
    if bool(buttons[11]) if len(buttons) > 11 else False:  # 上 - forward
        pressed_keys.add(robot.teleop_keys['forward'])
    if bool(buttons[12]) if len(buttons) > 12 else False:  # 下 - backward
        pressed_keys.add(robot.teleop_keys['backward'])
    if bool(buttons[13]) if len(buttons) > 13 else False:  # 左 - rotate left
        pressed_keys.add(robot.teleop_keys['rotate_left'])
    if bool(buttons[14]) if len(buttons) > 14 else False:  # 右 - rotate right
        pressed_keys.add(robot.teleop_keys['rotate_right'])
    
    return pressed_keys


def main():
    FPS = 30
    
    # Try to use saved calibration file
    robot_config = XLerobot2WheelsConfig(id="my_xlerobot_2wheels_lab")
    robot = XLerobot2Wheels(robot_config)
    
    try:
        robot.connect()
        print(f"[MAIN] Successfully connected to robot")
        if robot.is_calibrated:
            print(f"[MAIN] Robot is calibrated and ready to use!")
        else:
            print(f"[MAIN] Robot requires calibration")
    except Exception as e:
        print(f"[MAIN] Failed to connect to robot: {e}")
        print(f"[MAIN] Robot config: {robot_config}")
        print(f"[MAIN] Robot: {robot}")
        return

    init_rerun(session_name="xlerobot_2wheels_teleop_joycon_pygame")

    # Initialize pygame and Joy-Con controller
    print("[MAIN] Initializing Joy-Con controller via pygame...")
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("[MAIN] No controller detected! Please connect Joy-Con via Bluetooth.")
        return
    
    # Use the first joystick (Joy-Con mapped via Parallels)
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"[MAIN] Connected to: {joystick.get_name()}")
    print(f"[MAIN] Buttons: {joystick.get_numbuttons()}, Axes: {joystick.get_numaxes()}")

    # Init the arm and head instances
    obs = robot.get_observation()
    kin_left = SO101Kinematics()
    kin_right = SO101Kinematics()
    left_arm = SimpleTeleopArm(kin_left, LEFT_JOINT_MAP, obs, prefix="left")
    right_arm = SimpleTeleopArm(kin_right, RIGHT_JOINT_MAP, obs, prefix="right")
    head_control = SimpleHeadControl(obs)

    # Move both arms and head to zero position at start
    left_arm.move_to_zero_position(robot)
    right_arm.move_to_zero_position(robot)
    head_control.move_to_zero_position(robot)

    # Print comprehensive keymap information
    print("\n" + "="*80)
    print("🤖 XLeRobot 2Wheels Joy-Con (pygame) Control Instructions")
    print("="*80)
    
    print("\n📱 Base Control (Joy-Con Direction Keys):")
    print("    ↑ (Button 11): Forward")
    print("    ↓ (Button 12): Backward")
    print("    ← (Button 13): Rotate Left")
    print("    → (Button 14): Rotate Right")
    print("    🚀 Smooth Control: Linear acceleration/deceleration")
    
    print("\n🦾 Left Arm Control (Left Joy-Con):")
    print("   Joystick Control:")
    print("    - Vertical (Axis 1): X-axis +/-")
    print("    - Horizontal (Axis 0): Y-axis +/-")
    print("    - L Button (9) + Stick: Shoulder Pan +/-")
    print("    - ZL (Axis 4) + Stick: Pitch & Wrist Roll")
    print("   Gripper: ZL Trigger (Axis 4)")
    print("   Head: X(2)/B(1)/A(0)/Y(3)")
    
    print("\n🦾 Right Arm Control (Right Joy-Con):")
    print("   Joystick Control:")
    print("    - Vertical (Axis 3): X-axis +/-")
    print("    - Horizontal (Axis 2): Y-axis +/-")
    print("    - R Button (10) + Stick: Shoulder Pan +/-")
    print("    - ZR (Axis 5) + Stick: Pitch & Wrist Roll")
    print("   Gripper: ZR Trigger (Axis 5)")
    
    print("\n🔄 Global Reset:")
    print("    Capture Button (15): Reset all to zero position")
    
    print(f"\n⚙️ Robot Configuration:")
    print(f"   Wheel Radius: {robot.config.wheel_radius:.3f}m")
    print(f"   Wheelbase: {robot.config.wheelbase:.3f}m")
    print(f"   Speed Levels: {len(robot.speed_levels)} levels")
    for i, level in enumerate(robot.speed_levels):
        print(f"      Level {i+1}: Linear {level['linear']:.1f}m/s, Angular {level['angular']:.0f}°/s")
    
    print(f"\n🚀 Smooth Control Parameters:")
    print(f"   Acceleration Rate: {BASE_ACCELERATION_RATE:.1f} speed/second")
    print(f"   Deceleration Rate: {BASE_DECELERATION_RATE:.1f} speed/second")
    print(f"   Max Speed Multiplier: {BASE_MAX_SPEED:.1f}x")
    
    print("\n" + "="*80)
    print("🎮 Control started! Use Joy-Con to control robot")
    print("="*80 + "\n")

    try:
        while True:
            pygame.event.pump()
            
            left_key_state = get_joycon_key_state(joystick, LEFT_KEYMAP)
            right_key_state = get_joycon_key_state(joystick, RIGHT_KEYMAP)
            
            # Check for global reset (Capture button - 15)
            buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
            global_reset = bool(buttons[15]) if len(buttons) > 15 else False
            
            if global_reset:
                print("[MAIN] Global reset triggered!")
                left_arm.move_to_zero_position(robot)
                right_arm.move_to_zero_position(robot)
                head_control.move_to_zero_position(robot)
                continue

            # Handle both arms separately and simultaneously
            left_arm.handle_keys(left_key_state)
            right_arm.handle_keys(right_key_state)
            head_control.handle_keys(left_key_state)

            left_action = left_arm.p_control_action(robot)
            right_action = right_arm.p_control_action(robot)
            head_action = head_control.p_control_action(robot)

            # Get base action from Joy-Con direction keys
            pressed_keys = get_base_action_from_joycon(joystick, robot)
            
            # Apply smooth speed control to base action
            smooth_base_action = smooth_controller.update(pressed_keys, robot)

            # Merge all actions
            action = {**left_action, **right_action, **head_action, **smooth_base_action}
            robot.send_action(action)

            obs = robot.get_observation()
            log_rerun_data(obs, action)
            
            precise_sleep(1.0 / FPS)
    finally:
        robot.disconnect()
        pygame.quit()
        print("Teleoperation ended.")


if __name__ == "__main__":
    main()
