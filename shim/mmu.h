#pragma once
#include <stdint.h>

#define FB_PHYS	0x9d400000UL

struct mmu_info {
	uint64_t img_lo, img_hi, ttbr;
	uint64_t sctlr_before, sctlr_after;
	int n_l3;
};

int mmu_enable(struct mmu_info *info);
uint64_t mmu_probe(uintptr_t va);

/*
 * Bring-up self test: enable the 16K-granule MMU this XNU build needs, check
 * that AT S1E1R translates the shim and the splash framebuffer, then repeat
 * with TCR.TBI0 set (XNU's own TCR has it) to find out whether these cores
 * implement top-byte-ignore.  Leaves the MMU off again.
 * Returns 0 when 16K translation works, -1 otherwise; *tbi_ok tells whether
 * TBI0 kept working.
 */
int mmu_selftest(int *tbi_ok);
