import cv2

# 测试 0 号摄像头
index = 2
cap = cv2.VideoCapture(index)
print(f"正在测试摄像头 {index}")

if not cap.isOpened():
    print("❌ 摄像头无法打开")
else:
    print("✅ 摄像头已打开")
    
    # 检查摄像头属性
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"分辨率: {width}x{height}")
    print(f"帧率: {fps}")
    
    # 尝试读取 10 帧
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            print(f"✅ 第 {i+1} 帧: {frame.shape}")
            # 保存第一帧查看
            if i == 0:
                cv2.imwrite(f"test_cam{index}.jpg", frame)
                print(f"已保存 test_cam{index}.jpg")
        else:
            print(f"❌ 第 {i+1} 帧读取失败")
    
    cap.release()