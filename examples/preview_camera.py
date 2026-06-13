import argparse
import cv2

from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig

parser = argparse.ArgumentParser()
parser.add_argument("path", help="camera path, e.g. /dev/video0")
parser.add_argument("--width", type=int, default=640)
parser.add_argument("--height", type=int, default=480)
parser.add_argument("--fps", type=int, default=30)
args = parser.parse_args()

config = OpenCVCameraConfig(
    index_or_path=args.path,
    width=args.width,
    height=args.height,
    fps=args.fps,
)

with OpenCVCamera(config) as camera:
    while True:
        frame = camera.read()

        # LeRobot 默认读出 RGB，cv2.imshow 需要 BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        cv2.imshow(f"Camera: {args.path}", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()