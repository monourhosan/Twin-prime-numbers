"""
Windows-Native CUDA Driver API Wrapper via ctypes for NVIDIA GeForce MX250.
No external CUDA Toolkit installation or MSVC SDK headers required.
Communicates directly with nvcuda.dll (installed with the NVIDIA display driver)
and compiles PTX code using the NVIDIA driver's built-in JIT compiler.
Enforces explicit 64-bit Windows AMD64 ctypes argtypes and restypes.
"""

import ctypes
from typing import List, Optional, Tuple, Any

CUDA_SUCCESS = 0

class CUDADriverError(Exception):
    def __init__(self, code: int, message: str = ""):
        super().__init__(f"CUDA Driver API Error {code}: {message}")
        self.code = code

class CUDADriverManager:
    _instance: Optional["CUDADriverManager"] = None

    def __init__(self):
        self._cuda = None
        self._device = None
        self._context = None
        self._is_available = False
        self._compute_major = 0
        self._compute_minor = 0
        self._device_name = ""
        self._init_driver()

    @classmethod
    def get_instance(cls) -> "CUDADriverManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_driver(self):
        try:
            self._cuda = ctypes.WinDLL("nvcuda.dll")

            # Declare function signatures
            self._cuda.cuInit.argtypes = [ctypes.c_uint]
            self._cuda.cuInit.restype = ctypes.c_int

            self._cuda.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
            self._cuda.cuDeviceGetCount.restype = ctypes.c_int

            self._cuda.cuDeviceGet.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
            self._cuda.cuDeviceGet.restype = ctypes.c_int

            self._cuda.cuDeviceGetName.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
            self._cuda.cuDeviceGetName.restype = ctypes.c_int

            self._cuda.cuDeviceComputeCapability.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
            self._cuda.cuDeviceComputeCapability.restype = ctypes.c_int

            self._cuda.cuCtxCreate_v2.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint, ctypes.c_int]
            self._cuda.cuCtxCreate_v2.restype = ctypes.c_int

            self._cuda.cuCtxDestroy_v2.argtypes = [ctypes.c_void_p]
            self._cuda.cuCtxDestroy_v2.restype = ctypes.c_int

            self._cuda.cuCtxSynchronize.argtypes = []
            self._cuda.cuCtxSynchronize.restype = ctypes.c_int

            self._cuda.cuMemAlloc_v2.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
            self._cuda.cuMemAlloc_v2.restype = ctypes.c_int

            self._cuda.cuMemFree_v2.argtypes = [ctypes.c_uint64]
            self._cuda.cuMemFree_v2.restype = ctypes.c_int

            self._cuda.cuMemsetD8_v2.argtypes = [ctypes.c_uint64, ctypes.c_ubyte, ctypes.c_size_t]
            self._cuda.cuMemsetD8_v2.restype = ctypes.c_int

            self._cuda.cuMemcpyHtoD_v2.argtypes = [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t]
            self._cuda.cuMemcpyHtoD_v2.restype = ctypes.c_int

            self._cuda.cuMemcpyDtoH_v2.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_size_t]
            self._cuda.cuMemcpyDtoH_v2.restype = ctypes.c_int

            self._cuda.cuModuleLoadDataEx.argtypes = [
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.c_char_p,
                ctypes.c_uint,
                ctypes.POINTER(ctypes.c_uint),
                ctypes.POINTER(ctypes.c_void_p)
            ]
            self._cuda.cuModuleLoadDataEx.restype = ctypes.c_int

            self._cuda.cuModuleGetFunction.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_char_p]
            self._cuda.cuModuleGetFunction.restype = ctypes.c_int

            self._cuda.cuLaunchKernel.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                ctypes.c_uint,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.POINTER(ctypes.c_void_p)
            ]
            self._cuda.cuLaunchKernel.restype = ctypes.c_int

            res = self._cuda.cuInit(0)
            if res != CUDA_SUCCESS:
                self._is_available = False
                return

            dev_count = ctypes.c_int()
            if self._cuda.cuDeviceGetCount(ctypes.byref(dev_count)) != CUDA_SUCCESS or dev_count.value == 0:
                self._is_available = False
                return

            self._device = ctypes.c_int()
            if self._cuda.cuDeviceGet(ctypes.byref(self._device), 0) != CUDA_SUCCESS:
                self._is_available = False
                return

            name_buf = (ctypes.c_char * 256)()
            self._cuda.cuDeviceGetName(name_buf, 256, self._device.value)
            self._device_name = name_buf.value.decode("utf-8", errors="ignore")

            major = ctypes.c_int()
            minor = ctypes.c_int()
            self._cuda.cuDeviceComputeCapability(ctypes.byref(major), ctypes.byref(minor), self._device.value)
            self._compute_major = major.value
            self._compute_minor = minor.value

            self._is_available = True
        except Exception:
            self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def compute_capability(self) -> Tuple[int, int]:
        return (self._compute_major, self._compute_minor)

    def create_context(self):
        if not self._is_available:
            raise RuntimeError("CUDA driver is not available.")
        if self._context is not None:
            return self._context

        ctx = ctypes.c_void_p()
        res = self._cuda.cuCtxCreate_v2(ctypes.byref(ctx), 0, self._device.value)
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, "cuCtxCreate_v2 failed")
        self._context = ctx
        return ctx

    def destroy_context(self):
        if self._context is not None:
            self._cuda.cuCtxDestroy_v2(self._context)
            self._context = None

    def load_ptx_module(self, ptx_bytes: bytes) -> ctypes.c_void_p:
        self.create_context()
        module = ctypes.c_void_p()
        err_buf = ctypes.create_string_buffer(8192)
        opts = (ctypes.c_uint * 2)(5, 6)
        opt_vals = (ctypes.c_void_p * 2)(ctypes.cast(err_buf, ctypes.c_void_p), ctypes.cast(8192, ctypes.c_void_p))

        res = self._cuda.cuModuleLoadDataEx(ctypes.byref(module), ptx_bytes, 2, opts, opt_vals)
        if res != CUDA_SUCCESS:
            msg = err_buf.value.decode("utf-8", errors="ignore")
            raise CUDADriverError(res, f"cuModuleLoadDataEx failed: {msg}")
        return module

    def get_function(self, module: ctypes.c_void_p, kernel_name: str) -> ctypes.c_void_p:
        func = ctypes.c_void_p()
        res = self._cuda.cuModuleGetFunction(ctypes.byref(func), module, kernel_name.encode("utf-8"))
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuModuleGetFunction for '{kernel_name}' failed with code {res}")
        return func

    def mem_alloc(self, size_bytes: int) -> int:
        self.create_context()
        d_ptr = ctypes.c_uint64(0)
        res = self._cuda.cuMemAlloc_v2(ctypes.byref(d_ptr), ctypes.c_size_t(size_bytes))
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuMemAlloc_v2 failed for {size_bytes} bytes")
        return d_ptr.value

    def mem_free(self, d_ptr_val: int):
        if d_ptr_val:
            self._cuda.cuMemFree_v2(ctypes.c_uint64(d_ptr_val))

    def mem_set_u8(self, d_ptr_val: int, value: int, count: int):
        res = self._cuda.cuMemsetD8_v2(ctypes.c_uint64(d_ptr_val), ctypes.c_ubyte(value), ctypes.c_size_t(count))
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, "cuMemsetD8_v2 failed")

    def memcpy_htod(self, d_ptr_val: int, host_data: Any):
        if isinstance(host_data, bytes):
            host_buf = host_data
            size_bytes = len(host_data)
        elif hasattr(host_data, "ctypes"):
            host_buf = host_data.ctypes.data_as(ctypes.c_void_p)
            size_bytes = host_data.nbytes
        else:
            host_buf = host_data
            size_bytes = len(host_data)

        res = self._cuda.cuMemcpyHtoD_v2(ctypes.c_uint64(d_ptr_val), host_buf, ctypes.c_size_t(size_bytes))
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuMemcpyHtoD_v2 failed for {size_bytes} bytes")

    def memcpy_dtoh(self, host_buffer: Any, d_ptr_val: int, size_bytes: int):
        if hasattr(host_buffer, "ctypes"):
            dst_ptr = host_buffer.ctypes.data_as(ctypes.c_void_p)
        elif isinstance(host_buffer, int):
            dst_ptr = ctypes.c_void_p(host_buffer)
        else:
            dst_ptr = ctypes.cast(host_buffer, ctypes.c_void_p)

        res = self._cuda.cuMemcpyDtoH_v2(dst_ptr, ctypes.c_uint64(d_ptr_val), ctypes.c_size_t(size_bytes))
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuMemcpyDtoH_v2 failed for {size_bytes} bytes")

    def launch_kernel(
        self,
        func: ctypes.c_void_p,
        grid_dim: Tuple[int, int, int],
        block_dim: Tuple[int, int, int],
        args: List[Any],
        shared_mem_bytes: int = 0
    ):
        gx, gy, gz = grid_dim
        bx, by, bz = block_dim
        arg_ptrs = (ctypes.c_void_p * len(args))()
        kept_refs = []
        for i, val in enumerate(args):
            if isinstance(val, int):
                if -0x80000000 <= val <= 0x7FFFFFFF:
                    cval = ctypes.c_int32(val)
                elif 0 <= val <= 0xFFFFFFFF:
                    cval = ctypes.c_uint32(val)
                else:
                    cval = ctypes.c_uint64(val)
            elif isinstance(val, ctypes.c_void_p):
                cval = ctypes.c_uint64(val.value or 0)
            elif isinstance(val, (ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64, ctypes.c_int64, ctypes.c_float, ctypes.c_double)):
                cval = val
            else:
                cval = ctypes.c_uint64(val)
            kept_refs.append(cval)
            arg_ptrs[i] = ctypes.cast(ctypes.byref(cval), ctypes.c_void_p)

        res = self._cuda.cuLaunchKernel(
            func,
            gx, gy, gz,
            bx, by, bz,
            shared_mem_bytes,
            None,
            arg_ptrs,
            None
        )
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuLaunchKernel failed with code {res}")

    def synchronize(self):
        res = self._cuda.cuCtxSynchronize()
        if res != CUDA_SUCCESS:
            raise CUDADriverError(res, f"cuCtxSynchronize failed with code {res}")
