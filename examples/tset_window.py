import cv2
import numpy as np

print("创建测试图像...")
img = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(img, 'OpenCV Works!', (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

print("显示窗口...")
cv2.imshow('Test Window', img)
print("按任意键继续...")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("完成!")