import cv2

# 카메라 객체 생성
cap = cv2.VideoCapture(0)

while True:
    # 프레임 캡처
    ret, frame = cap.read()
    
    # 프레임 처리 (예: 그레이스케일 변환)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 처리된 프레임 출력
    cv2.imshow('frame', gray)
    
    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
