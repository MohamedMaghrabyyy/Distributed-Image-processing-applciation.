# import pyopencl as cl
import queue
import numpy as np
import cv2
import serverMaster
class CL_Image_Preprocessing:

    def __init__(self) -> None:
        # self.ctx = cl.create_some_context()
        # self.queue = cl.CommandQueue(self.ctx)
        self.kernels = {
            'bright': """
                __kernel void bright(__global float* V) {
                    int i = get_global_id(0);
                    if (V[i] + 60.0f <= 255.0f)
                        V[i] = V[i] + 60.0f;
                    else
                        V[i] = 255.0f;
                }
            """,
            'dark': """
                __kernel void dark(__global float* V) {
                    int i = get_global_id(0);
                    if (V[i] - 60.0f >= 0.0f)
                        V[i] = V[i] - 60.0f;
                    else
                        V[i] = 0.0f;
                }
            """,
            'threshold': """
                __kernel void Thresh(__global float* V) { 
                    int i = get_global_id(0);
                    if (V[i] >= 127.0f) 
                        V[i] = 255.0f;
                    else
                        V[i] = 0.0f;
                }
            """,
            'grey': """
                __kernel void grayscale(__global float* channel, __global float* result) {
                    int i = get_global_id(0);
                    result[i] = channel[i];
                }
            """
        }
    def To_gray_pyopencl(self, img):
        """
        This function takes a 3 channel image 
        and then converts it to a grayscale 1 Channel image 
        """
        gray = (len(img.shape) == 2)
        
        if gray:
            return img

        img = img.astype(np.float32)

        original_height, original_width, channels = img.shape

        B, G, R = cv2.split(img)

        Grey_img = self.TaskScheduler("to_grey", R, G, B, 0, original_height, original_width)
        return cv2.cvtColor(Grey_img, cv2.COLOR_BGR2GRAY)
    
    def TaskScheduler(self, name, r, g, b, value, height = 0, width = 0):
        print(f"Sending task to masterTask")
        result_queue=queue.Queue()
        mT=serverMaster.masterT(name,r,g,b,value,result_queue,height,width)
        mT.start()
        while result_queue.empty():
            continue
        res=result_queue.get(block=True)
        return res
        # return serverMaster.MasterTask(name, r, g, b, value, height, width)
        # if name == 'intensity':
        #     adjusted_R = gp1.apply_intensity_kernel_R(self, r, value, self.kernels['bright'], self.kernels['dark'])
        #     adjusted_B = gp2.apply_intensity_kernel_B(self, b, value, self.kernels['bright'], self.kernels['dark'])
        #     adjusted_G = gp3.apply_intensity_kernel_G(self, g, value, self.kernels['bright'], self.kernels['dark'])
        #     bright_image = cv2.merge((adjusted_R, adjusted_G, adjusted_B))
        #     return bright_image
        # elif name == "to_grey":
        #     grey_R = gp1.process_grey_R(self, r, height, width, self.kernels['grey'])
        #     grey_G = gp3.process_grey_G(self, g, height, width, self.kernels['grey'])
        #     grey_B = gp2.process_grey_B(self, b, height, width, self.kernels['grey'])

        #     Grey_img = cv2.merge((grey_B, grey_G, grey_R))
        #     Grey_img = Grey_img.astype(np.uint8)
        #     return Grey_img

    

    def Intensity_pyopencl(self, img, value):
        """
        This Function takes an image with value either 0 or 1:
        1 -> decides that you want to brighten the image 
        0 -> decide that you want to darken the image 
        """

        img = img.astype(np.float32)
        gray = (len(img.shape) == 2)
        
        if gray:
            original_height, original_width = img.shape
            v_flat = img.reshape(-1)
            # bright_image = gp2.apply_intensity_kernel_grey(self, v_flat, value, self.kernels['bright'], self.kernels['dark'])
            bright_image = self.TaskScheduler("intensity-grey", v_flat,None,None, value)
            bright_image = bright_image.reshape((original_height, original_width))
        else:
            original_height, original_width, channels = img.shape
            R, G, B = cv2.split(img)
            bright_image = self.TaskScheduler("intensity", R, G, B, value)
            
            

        bright_image = bright_image.astype(np.uint8)

        return bright_image
    
    
    def Threshhold(self, img):
        img_32 = img.astype(np.float32)  # changed the image from uint8 to float32  
        gray = (len(img_32.shape) == 2)  # check if the image is grey or not 

        if gray:  # if grey will make it 1D format 
            original_height, original_width = img_32.shape
            v_flat = img_32.reshape(-1)  # 1D format image and put it in a variable to use later 
        else: 
            gray_img = self.To_gray_pyopencl(img)  # if not will turn it to gray image and reshape it to be 1D format
            gray_img = gray_img.astype(np.float32) 
            original_height, original_width = gray_img.shape
            v_flat = gray_img.reshape(-1)

            
        # return gp1.Threshold_helper(self, v_flat, self.kernels['threshold'], original_height, original_width)
        return self.TaskScheduler("threshold", v_flat,None,None, -1,original_height,original_width)

    
    

        
    