import pyopencl as cl
import numpy as np
import time

a = np.random.rand(256**3,3).astype(np.float32)
print(a.reshape(-1).shape)
a=a.reshape(-1)
# print(a[0:11])
ctx=cl.create_some_context()
queue=cl.CommandQueue(ctx)

# Creates an OpenCL buffer (a_dev) on the device's memory (ctx).
# cl.mem_flags.READ_WRITE -> specifies that the buffer can be both read from and written to by the kernel.
# size=a.nbytes -> allocates enough memory on the device to hold the data from the NumPy array a.


a_dev=cl.Buffer(ctx,cl.mem_flags.READ_WRITE,size=a.nbytes)
cl._enqueue_write_buffer(queue , a_dev ,a)
# t1=time.time()
prg=cl.Program(ctx,"""
               __kernel void twice(__global float *a)
               {
                a[get_global_id(0)] *=2;}
               """).build()
prg.twice(queue,a.shape , (1,), a_dev)
# print(f"time taken with pyopencl{time.time()-t1}")
result =np.empty_like(a)
# print(result[0:11])
cl._enqueue_read_buffer(queue,a_dev,result).wait()
print(a[0:11])
print(result[0:11])
# print(a.shape)

import numpy.linalg as la
assert la.norm(result - 2*a)==0






