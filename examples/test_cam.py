import cv2
import os
import glob

print("=== 摄像头扫描 ===")

# 构建 index → 设备路径 的映射
v4l_paths = {}
by_path_dir = "/dev/v4l/by-path"
if os.path.exists(by_path_dir):
    for link in glob.glob(os.path.join(by_path_dir, "*")):
        real = os.path.realpath(link)
        if "video" in real:
            idx_str = real.replace("/dev/video", "")
            if idx_str.isdigit():
                v4l_paths[int(idx_str)] = link

# 也列出 /dev/video* 设备
all_video_devices = sorted(glob.glob("/dev/video*"), key=lambda x: int(x.replace("/dev/video", "")) if x.replace("/dev/video", "").isdigit() else 999)
print(f"系统视频设备: {all_video_devices}\n")

found = []

for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            device_path = v4l_paths.get(i, f"/dev/video{i} (无 by-path 映射)")
            print(f"✅ 摄像头 {i}: {w}x{h} @ {fps:.1f}fps")
            print(f"   设备路径: {device_path}")
            print(f"   实际设备: /dev/video{i}")
            print(f"   frame shape: {frame.shape}")

            save_path = f"test_cam{i}.jpg"
            cv2.imwrite(save_path, frame)
            print(f"   已保存: {os.path.abspath(save_path)}")
            found.append((i, device_path))
        else:
            print(f"⚠️  摄像头 {i}: 能打开但读不到帧")
        cap.release()
    else:
        print(f"❌ 摄像头 {i}: 无法打开")

print(f"\n=== 共发现 {len(found)} 个可用摄像头 ===")
for idx, path in found:
    print(f"  index={idx}  →  {path}")