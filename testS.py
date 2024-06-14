from CL_For_Image import CL_Image_Preprocessing
import cv2

img = cv2.imread("Bird.jpg")

CL = CL_Image_Preprocessing()
gray = CL.To_gray_pyopencl(img)

bright_gray = CL.Intensity_pyopencl(gray, 1)
bright_img = CL.Intensity_pyopencl(img, 1)
dark_gray = CL.Intensity_pyopencl(gray, 0)
dark_img = CL.Intensity_pyopencl(img, 0)
thresh = CL.Threshhold(img)

cv2.imwrite("output/gray.jpg", gray)
cv2.imwrite("output/bright_gray.jpg", bright_gray)
cv2.imwrite("output/bright_img.jpg", bright_img)
cv2.imwrite("output/dark_gray.jpg", dark_gray)
cv2.imwrite("output/dark_img.jpg", dark_img)
cv2.imwrite("output/thresh_img.jpg", thresh)