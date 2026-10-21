#pragma once
#include <stdint.h>

#define FB_BASE		0x9d400000UL	/* reserved-memory cont_splash_region */
#define FB_W		1080
#define FB_H		1920
#define FB_STRIDE	(FB_W * 4)	/* a8r8g8b8, matches mainline simplefb */

#define RED	0xffff0000U
#define BLUE	0xff0000a0U
#define WHITE	0xffffffffU
#define YELLOW	0xffffff00U
#define GREEN	0xff00ff00U
#define CYAN	0xff00ffffU
#define MAGENTA	0xffff00ffU
#define ORANGE	0xffff8000U
#define PURPLE	0xff8000ffU
#define GREY	0xff808080U

extern volatile uint32_t *con_fb;

void con_diag(int slot, uint32_t color);
void con_clear(uint32_t bg);
void con_skip(void);
void con_str(const char *label, const char *s);
void con_hex(const char *label, uint64_t v);
/* label, then "a=xxxxxxxx b=xxxxxxxx" style pairs of 32-bit values */
void con_hex2(const char *label, const char *a, uint32_t va, const char *b, uint32_t vb);
