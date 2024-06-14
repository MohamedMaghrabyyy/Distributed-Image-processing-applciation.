import pyopencl as cl
import numpy as np

def process_grey_R(ctx,queue, R, height, width, grey_kernel):
        """
        Process a single channel for grayscale conversion using OpenCL
        """
        channel_flat = R.reshape(-1)
        empty_matrix = np.empty_like(channel_flat)

        channel_buff = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=channel_flat)
        result_buff = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, size=empty_matrix.nbytes)

        prg = cl.Program(ctx, grey_kernel).build()
        prg.grayscale(queue, (height * width,), None, channel_buff, result_buff)

        result = np.empty_like(channel_flat)
        cl.enqueue_copy(queue, result, result_buff).wait()

        return result.reshape(height, width)
def apply_intensity_kernel_R(ctx,queue, R, value, bright_kernel, dark_kernel):
        """
        Apply brightness/darkness adjustment to a single channel using OpenCL kernel
        """
        channel_flat = R.reshape(-1)
        empty_matrix = np.empty_like(channel_flat)

        channel_buff = cl.Buffer(ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR, hostbuf=channel_flat)
        result_buff = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, size=empty_matrix.nbytes)

        if value == 1:
            prg = cl.Program(ctx, bright_kernel).build()
            prg.bright(queue, channel_flat.shape, None, channel_buff)
        else:
            prg = cl.Program(ctx, dark_kernel).build()
            prg.dark(queue, channel_flat.shape, None, channel_buff)
                

        result = np.empty_like(channel_flat)
        cl.enqueue_copy(queue, result, channel_buff).wait()

        return result.reshape(R.shape)
def Threshold_helper(ctx,queue, v_flat, Thresh_kernel, original_height, original_width):
    
  V_buff = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, size=v_flat.nbytes)  # to save the output of thresh operation later in this variable
  cl.enqueue_copy(queue, V_buff, v_flat)  # firstly, put the input in this variable

  prg = cl.Program(ctx, Thresh_kernel).build() 
  prg.Thresh(queue, v_flat.shape, (1,), V_buff)  # use the thresh function to do the thresh operation and the output is saved in v_buff 
                                                            # because it's a read and write variable or a buffer

  cl.enqueue_copy(queue, v_flat, V_buff) 
  threshed_image = v_flat.reshape((original_height, original_width))  # reshape it in 2D format
  threshed_image = threshed_image.astype(np.uint8)  # to send it back as uint8 image
  return threshed_image
