from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

# 카메라 초기화
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))

# 카메라가 켜지는데 걸리는 시간
time.sleep(0.1)

# 카메라에서 영상 캡처
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # numpy 배열로 이미지 가져오기
    image = frame.array

    # 이미지에 대한 처리 (여기에 OpenCV 코드 추가)
    cv2.imshow("Frame", image)
    
    key = cv2.waitKey(1) & 0xFF
    rawCapture.truncate(0)
    
    # 'q' 키를 누르면 반복문 탈출
    if key == ord("q"):
        break

cv2.destroyAllWindows()
