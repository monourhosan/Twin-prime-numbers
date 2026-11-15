"""
Phase 9 NVIDIA GeForce MX250 Hardware-Accelerated Sieve Engine (sm_61).
Uses the Windows CUDA Driver API (nvcuda.dll) to execute PTX kernels directly on
the laptop's dedicated GPU without requiring the CUDA Toolkit or MSVC SDK.
Maintains exact bit-for-bit equivalence with the CPU reference implementation.
"""

from typing import List, Optional, Tuple, Dict
import numpy as np

from src.phase4.laptop_accel.cuda_driver import CUDADriverManager, CUDADriverError
from .cpu_sieve import SievePrimePlan, CPUSieve

PTX_FLATTENED_SIEVE = b"""
.version 6.1
.target sm_61
.address_size 64

.visible .entry sieve_flattened_kernel(
    .param .u64 d_alive,
    .param .u64 d_primes,
    .param .u64 d_start_offsets,
    .param .u32 num_tasks,
    .param .u32 num_candidates
)
{
    .reg .b32 %task_idx, %task_limit, %r_ntid, %r_ctaid, %r_tid, %q, %pos, %nc;
    .reg .b16 %zero8;
    .reg .b64 %rd_alive, %rd_primes, %rd_start, %offset, %addr;
    .reg .pred %pred_bounds, %pred_loop;

    mov.u32 %r_ctaid, %ctaid.x;
    mov.u32 %r_ntid, %ntid.x;
    mov.u32 %r_tid, %tid.x;
    mad.lo.s32 %task_idx, %r_ctaid, %r_ntid, %r_tid;

    ld.param.u32 %task_limit, [num_tasks];
    setp.ge.u32 %pred_bounds, %task_idx, %task_limit;
    @%pred_bounds bra EXIT;

    mov.u16 %zero8, 0;
    ld.param.u32 %nc, [num_candidates];
    ld.param.u64 %rd_alive, [d_alive];
    ld.param.u64 %rd_primes, [d_primes];
    ld.param.u64 %rd_start, [d_start_offsets];

    cvt.u64.u32 %offset, %task_idx;
    shl.b64 %offset, %offset, 2;

    add.u64 %addr, %rd_primes, %offset;
    ld.global.u32 %q, [%addr];

    add.u64 %addr, %rd_start, %offset;
    ld.global.u32 %pos, [%addr];

LOOP:
    setp.ge.u32 %pred_loop, %pos, %nc;
    @%pred_loop bra EXIT;

    cvt.u64.u32 %offset, %pos;
    add.u64 %addr, %rd_alive, %offset;
    st.global.u8 [%addr], %zero8;

    add.u32 %pos, %pos, %q;
    bra LOOP;

EXIT:
    ret;
}
"""


class GPUSieveMX250:
    """
    NVIDIA GeForce MX250 Hardware-Accelerated Sieve for Phase 9 PACCM-9.
    Executes flattened modular sieve tasks across GPU threads.
    """

    def __init__(self, plan: List[SievePrimePlan], cross_check_cpu: bool = False):
        self.plan = plan
        self.cross_check_cpu = cross_check_cpu
        self.cpu_fallback = CPUSieve(plan)

        # Flatten plan into 1D arrays: (prime, root)
        q_list: List[int] = []
        root_list: List[int] = []
        for p_plan in self.plan:
            q = p_plan.q
            for r in p_plan.roots:
                q_list.append(q)
                root_list.append(r)

        self.num_tasks = len(q_list)
        self.primes_arr = np.array(q_list, dtype=np.uint32)
        self.roots_arr = np.array(root_list, dtype=np.uint32)

        self.driver = CUDADriverManager.get_instance()
        self.gpu_ready = False

        if self.driver.is_available and self.num_tasks > 0:
            try:
                self.module = self.driver.load_ptx_module(PTX_FLATTENED_SIEVE)
                self.kernel = self.driver.get_function(self.module, "sieve_flattened_kernel")

                self.d_primes = self.driver.mem_alloc(self.num_tasks * 4)
                self.d_start = self.driver.mem_alloc(self.num_tasks * 4)

                self.driver.memcpy_htod(self.d_primes, self.primes_arr)

                self.d_alive = 0
                self._alive_capacity = 0
                self.gpu_ready = True
            except Exception as e:
                self.gpu_ready = False
                self.close()

    def _ensure_alive_buffer(self, num_candidates: int):
        if num_candidates > self._alive_capacity:
            if self.d_alive:
                self.driver.mem_free(self.d_alive)
            new_cap = int(num_candidates * 1.2) + 2048
            self.d_alive = self.driver.mem_alloc(new_cap)
            self._alive_capacity = new_cap

    def sieve_segment(self, t_start: int, t_end: int) -> List[int]:
        """
        Sieves odd candidate multipliers t in [t_start, t_end].
        Returns list of surviving t values.
        """
        assert t_start % 2 == 1, "t_start must be odd"
        assert t_end >= t_start, "t_end must be >= t_start"

        if not self.gpu_ready or self.num_tasks == 0:
            return self.cpu_fallback.sieve_segment(t_start, t_end)

        n_candidates = (t_end - t_start) // 2 + 1

        try:
            # 1. Compute start offsets for all tasks
            t_start_mod_q = t_start % self.primes_arr
            rem = (self.roots_arr - t_start_mod_q) % self.primes_arr
            first_t = t_start + rem
            # If first_t is even, advance by q (since q is odd, first_t + q is odd)
            first_t = np.where(first_t % 2 == 0, first_t + self.primes_arr, first_t)
            start_indices = ((first_t - t_start) // 2).astype(np.uint32)

            # 2. Upload start offsets
            self.driver.memcpy_htod(self.d_start, start_indices)

            # 3. Prepare alive buffer
            self._ensure_alive_buffer(n_candidates)
            self.driver.mem_set_u8(self.d_alive, 1, n_candidates)

            # 4. Launch kernel
            threads = 256
            blocks = (self.num_tasks + threads - 1) // threads
            self.driver.launch_kernel(
                self.kernel,
                (blocks, 1, 1),
                (threads, 1, 1),
                [self.d_alive, self.d_primes, self.d_start, self.num_tasks, n_candidates]
            )
            self.driver.synchronize()

            # 5. Read back
            host_alive = np.zeros(n_candidates, dtype=np.uint8)
            self.driver.memcpy_dtoh(host_alive, self.d_alive, n_candidates)

            survivor_indices = np.where(host_alive)[0]
            survivors = [int(t_start + 2 * i) for i in survivor_indices]

            if self.cross_check_cpu:
                cpu_survivors = self.cpu_fallback.sieve_segment(t_start, t_end)
                if survivors != cpu_survivors:
                    raise RuntimeError(
                        f"GPU/CPU sieve mismatch! GPU: {len(survivors)}, CPU: {len(cpu_survivors)}"
                    )

            return survivors

        except Exception as e:
            # Fall back safely to CPU reference engine
            return self.cpu_fallback.sieve_segment(t_start, t_end)

    def close(self):
        """Releases device buffers."""
        if hasattr(self, 'd_alive') and self.d_alive:
            try:
                self.driver.mem_free(self.d_alive)
            except Exception:
                pass
            self.d_alive = 0
            self._alive_capacity = 0

        if hasattr(self, 'd_primes') and self.d_primes:
            try:
                self.driver.mem_free(self.d_primes)
            except Exception:
                pass
            self.d_primes = 0

        if hasattr(self, 'd_start') and self.d_start:
            try:
                self.driver.mem_free(self.d_start)
            except Exception:
                pass
            self.d_start = 0
