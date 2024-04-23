import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import imutils
import re
import requests
from imutils.perspective import four_point_transform

import pytesseract
from PIL import Image

def plt_imshow(title='image', img=None, figsize=(8 ,5)):
    plt.figure(figsize=figsize)
 
    if type(img) == list:
        if type(title) == list:
            titles = title
        else:
            titles = []
 
            for i in range(len(img)):
                titles.append(title)
 
        for i in range(len(img)):
            if len(img[i].shape) <= 2:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_GRAY2RGB)
            else:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_BGR2RGB)
 
            plt.subplot(1, len(img), i + 1), plt.imshow(rgbImg)
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])
 
        plt.show()
    else:
        if len(img.shape) < 3:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
 
        plt.imshow(rgbImg)
        plt.title(title)
        plt.xticks([]), plt.yticks([])
        plt.show()


# import image.npy
ocr_image_npy = np.load('./ocr.npy')
ocr_image_npy = cv2.cvtColor(ocr_image_npy, cv2.COLOR_RGB2BGR)
# print(ocr_image_npy.shape)

# # npy to Image - 1
# ocr_img = Image.fromarray(ocr_image_npy)
# ratio = ocr_image_npy.shape[1] / float(ocr_image_npy.shape[1])
# # 이미지를 grayscale로 변환하고 blur를 적용
# # 모서리를 찾기위한 이미지 연산
# gray = cv2.cvtColor(ocr_image_npy, cv2.COLOR_BGR2GRAY)
# blurred = cv2.GaussianBlur(gray, (5, 5,), 0)
# edged = cv2.Canny(blurred, 75, 200)
# plt_imshow(['gray', 'blurred', 'edged'], [gray, blurred, edged])
# # contours를 찾아 크기순으로 정렬
# cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# cnts = imutils.grab_contours(cnts)
# cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
# receiptCnt = None
# # 정렬된 contours를 반복문으로 수행하며 4개의 꼭지점을 갖는 도형을 검출
# for c in cnts:
# 	peri = cv2.arcLength(c, True)
# 	approx = cv2.approxPolyDP(c, 0.02 * peri, True)
 
# 	# contours가 크기순으로 정렬되어 있기때문에 제일 첫번째 사각형을 영수증 영역으로 판단하고 break
# 	if len(approx) == 4:
# 		receiptCnt = approx
# 		break
# # 만약 추출한 윤곽이 없을 경우 오류
# if receiptCnt is None:
# 	raise Exception(("Could not find receipt outline."))
# output = ocr_image_npy.copy()
# cv2.drawContours(output, [receiptCnt], -1, (0, 255, 0), 2)
# plt_imshow("Receipt Outline", output)
# # 원본 이미지에 찾은 윤곽을 기준으로 이미지를 보정
# receipt = four_point_transform(ocr_image_npy, receiptCnt.reshape(4, 2) * ratio)
# plt_imshow("Receipt Transform", receipt)


# tesseract vanilla
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
text = pytesseract.image_to_string(ocr_image_npy, lang="eng+kor")
print(text)

# resize
resized_image_npy = cv2.resize(ocr_image_npy, (640, 480))
# show ocr_img by cv2
cv2.imshow('OCR Image', resized_image_npy)
# 키 입력 대기 (0은 무한 대기)
cv2.waitKey(0)
# 모든 창 닫기
cv2.destroyAllWindows()