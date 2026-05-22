"""
Joy-Con 按键映射调试脚本
用于确认 Parallels 映射后 Joy-Con 的按键和轴的实际编号

运行方法:
    python joycon_debug_CN.py

然后按 Joy-Con 的各个按键/摇杆，观察输出的编号变化
"""

import pygame
import time

pygame.init()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()
print(f"检测到 {joystick_count} 个手柄设备")

if joystick_count == 0:
    print("未检测到任何手柄")
    exit(1)

# 列出所有手柄
for i in range(joystick_count):
    j = pygame.joystick.Joystick(i)
    j.init()
    print(f"  [{i}] {j.get_name()}")

# 选择要调试的手柄
joystick_id = int(input("\n输入要调试的手柄编号 (默认: 1): ") or "1")
if joystick_id >= joystick_count:
    joystick_id = 0

joystick = pygame.joystick.Joystick(joystick_id)
joystick.init()

print(f"\n=== 手柄信息 ===")
print(f"名称: {joystick.get_name()}")
print(f"按键数量: {joystick.get_numbuttons()}")
print(f"轴数量: {joystick.get_numaxes()}")
print(f"方向键数量: {joystick.get_numhats()}")
print("\n按 Joy-Con 的各个按键和摇杆，观察编号变化...")
print("按 Ctrl+C 停止\n")

last_buttons = [0] * joystick.get_numbuttons()
last_axes = [0.0] * joystick.get_numaxes()

try:
    while True:
        pygame.event.pump()
        
        # 检测按键变化
        for i in range(joystick.get_numbuttons()):
            current = joystick.get_button(i)
            if current != last_buttons[i]:
                if current == 1:
                    print(f"[按键 {i}] 按下 ↓")
                else:
                    print(f"[按键 {i}] 释放 ↑")
                last_buttons[i] = current
        
        # 检测轴变化（超过阈值时显示）
        for i in range(joystick.get_numaxes()):
            current = joystick.get_axis(i)
            if abs(current - last_axes[i]) > 0.1:
                print(f"[轴 {i}] 值: {current:.3f}")
                last_axes[i] = current
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n调试结束")
    pygame.quit()