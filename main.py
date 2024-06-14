from CL_For_Image import CL_Image_Preprocessing
import cv2

img = cv2.imread("Bird.jpg")

CL = CL_Image_Preprocessing()

thresh_img = CL.Threshhold(img)

gray = CL.To_gray_pyopencl(img)

bright_gray = CL.Intensity_pyopencl(gray, 1)

bright_img = CL.Intensity_pyopencl(img, 1)

dark_gray = CL.Intensity_pyopencl(gray, 0)

dark_img = CL.Intensity_pyopencl(img, 0)

thresh = CL.Threshhold(img)
# print(CL.Intensity_pyopencl.__doc__)

cv2.imshow("orginal", img)
cv2.imshow("gray", gray)
cv2.imshow("bright_gray", bright_gray)
cv2.imshow("bright_img", bright_img)
cv2.imshow("dark_gray", dark_gray)
cv2.imshow("dark_img", dark_img)
cv2.imshow("thresh_img", thresh)


cv2.waitKey(0)
cv2.destroyAllWindows()
