from robocrew.core.camera import RobotCamera
from robocrew.core.LLMAgent import LLMAgent
from robocrew.robots.XLeRobot.tools import create_move_forward, create_turn_right, create_turn_left
from robocrew.robots.XLeRobot.servo_controls import ServoControler

# set up main camera
main_camera = RobotCamera("/dev/video0") # camera usb port Eg: /dev/video0

#set up servo controler
right_arm_wheel_usb = "/dev/tty.usbmodem5B141120971"    # provide your right arm usb port. Eg: /dev/ttyACM1
left_arm_head_usb = "/dev/tty.usbmodem5B141156081"      # provide your left arm usb port. Eg: /dev/ttyACM0
servo_controler = ServoControler(right_arm_wheel_usb, left_arm_head_usb)

#set up tools
move_forward = create_move_forward(servo_controler)
turn_left = create_turn_left(servo_controler)
turn_right = create_turn_right(servo_controler)

# init agent
agent = LLMAgent(
    model="openai:gpt-5.4-mini",
    tools=[move_forward, turn_left, turn_right],
    main_camera=main_camera,
    servo_controler=servo_controler,
)

agent.task = "Approach a human."

agent.go()
