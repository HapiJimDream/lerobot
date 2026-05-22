"""
Joy-Con Xbox 控制器适配脚本
用于 Parallels 虚拟机中，Joy-Con 通过 macOS 游戏控制器框架映射为虚拟 Xbox 控制器

运行前需要安装 pygame:
    pip install pygame

使用方法:
    python joycon_xbox_adapter_CN.py
"""

import pygame
import time

# 初始化 pygame
pygame.init()
pygame.joystick.init()

# 查找所有连接的手柄
joystick_count = pygame.joystick.get_count()
print(f"检测到 {joystick_count} 个手柄设备")

if joystick_count == 0:
    print("未检测到任何手柄，请检查:")
    print("  1. macOS 端是否已配对 Joy-Con")
    print("  2. 虚拟机中是否有 /dev/input/js* 设备")
    exit(1)

# 选择 js1（通常是 Joy-Con 映射的设备）
# 如果只有一个设备，则使用 js0
joystick_id = 1 if joystick_count > 1 else 0
joystick = pygame.joystick.Joystick(joystick_id)
joystick.init()

print(f"\n已连接手柄: {joystick.get_name()}")
print(f"按键数量: {joystick.get_numbuttons()}")
print(f"摇杆数量: {joystick.get_numaxes()}")
print(f"方向键数量: {joystick.get_numhats()}")

# 控制状态
position = [0.0, 0.0, 0.0]  # x, y, z
rotation = [0.0, 0.0, 0.0]  # roll, pitch, yaw
gripper_state = 0  # 0: 打开, 1: 关闭
button_control = 0  # 控制按钮状态

# 速度配置
dof_speed = [2, 2, 2, 1, 1, 1]  # 各轴速度

# Xbox 控制器按键映射（Joy-Con 映射后）
# 注意: Parallels 映射可能有所不同，需要实际测试调整
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_LB = 4   # ZL
BUTTON_RB = 5   # ZR
BUTTON_BACK = 6  # -
BUTTON_START = 7 # +
BUTTON_HOME = 8  # Home

# 轴映射
AXIS_LEFT_X = 0    # 左摇杆水平
AXIS_LEFT_Y = 1    # 左摇杆垂直
AXIS_RIGHT_X = 2   # 右摇杆水平
AXIS_RIGHT_Y = 3   # 右摇杆垂直
AXIS_LT = 4        # L 触发
AXIS_RT = 5        # R 触发

print("\n=== 控制说明 ===")
print("左摇杆: 控制 X/Y 轴（前后/左右）")
print("右摇杆: 控制 Roll/Pitch/Yaw")
print("A 按钮: Z 轴上升")
print("B 按钮: Z 轴下降")
print("LB (ZL): 切换夹爪")
print("RB (ZR): 确认/下一帧")
print("Home 按钮: 重置位置")
print("按 Ctrl+C 停止")
print()

def get_axis_value(axis_id, deadzone=0.15):
    """获取轴值，带死区处理"""
    value = joystick.get_axis(axis_id)
    if abs(value) < deadzone:
        return 0.0
    return value

try:
    while True:
        # 处理事件
        pygame.event.pump()
        
        # 读取摇杆值
        left_x = get_axis_value(AXIS_LEFT_X)
        left_y = get_axis_value(AXIS_LEFT_Y)
        right_x = get_axis_value(AXIS_RIGHT_X)
        right_y = get_axis_value(AXIS_RIGHT_Y)
        
        # 更新位置（左摇杆控制 X/Y）
        position[0] += 0.001 * left_y * dof_speed[0]  # X 轴（前后）
        position[1] += 0.001 * left_x * dof_speed[1]  # Y 轴（左右）
        
        # 更新旋转（右摇杆控制 Roll/Pitch）
        rotation[0] += 0.001 * right_x * dof_speed[3]  # Roll
        rotation[1] += 0.001 * right_y * dof_speed[4]  # Pitch
        
        # 读取按键
        button_a = joystick.get_button(BUTTON_A)
        button_b = joystick.get_button(BUTTON_B)
        button_lb = joystick.get_button(BUTTON_LB)
        button_rb = joystick.get_button(BUTTON_RB)
        button_home = joystick.get_button(BUTTON_HOME)
        button_back = joystick.get_button(BUTTON_BACK)
        button_start = joystick.get_button(BUTTON_START)
        
        # Z 轴控制
        if button_a:
            position[2] += 0.001 * dof_speed[2]  # Z 上升
        if button_b:
            position[2] -= 0.001 * dof_speed[2]  # Z 下降
        
        # 夹爪切换
        if button_lb:
            gripper_state = 1 - gripper_state  # 切换状态
        
        # 控制按钮
        if button_rb:
            button_control = 1  # 确认/下一帧
        elif button_back:
            button_control = -1  # 重新开始
        elif button_start:
            button_control = 8  # 重置
        else:
            button_control = 0
        
        # 重置位置
        if button_home:
            position = [0.0, 0.0, 0.0]
            rotation = [0.0, 0.0, 0.0]
        
        # 输出状态
        x, y, z = position
        roll, pitch, yaw = rotation
        print(f"位置: x={x:.3f}, y={y:.3f}, z={z:.3f} | "
              f"旋转: roll={roll:.3f}, pitch={pitch:.3f}, yaw={yaw:.3f} | "
              f"夹爪: {gripper_state} | 控制: {button_control}")
        
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n程序已停止")
    pygame.quit()