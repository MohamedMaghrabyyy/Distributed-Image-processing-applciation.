import pyopencl as cl
import numpy as np

def process_grey_G(ctx,queue, G, height, width, grey_kernel):
  """
  Process a single channel for grayscale conversion using OpenCL
  """
  channel_flat = G.reshape(-1)
  empty_matrix = np.empty_like(channel_flat)

  channel_buff = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=channel_flat)
  result_buff = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, size=empty_matrix.nbytes)

  grey_kernel = """__kernel void grayscale(__global float* channel, __global float* result) {
            int i = get_global_id(0);
            result[i] = channel[i];
        }"""

  prg = cl.Program(ctx, grey_kernel).build()
  prg.grayscale(queue, (height * width,), None, channel_buff, result_buff)

  result = np.empty_like(channel_flat)
  cl.enqueue_copy(queue, result, result_buff).wait()

  return result.reshape(height, width)
def apply_intensity_kernel_G(ctx,queue, G, value, bright_kernel, dark_kernel):
        """
        Apply brightness/darkness adjustment to a single channel using OpenCL kernel
        """
        channel_flat = G.reshape(-1)
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

        return result.reshape(G.shape)