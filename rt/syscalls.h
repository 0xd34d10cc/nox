#pragma once

#include "types.h"

extern void sys_setup(void);
extern Int  sys_read(void);
extern void sys_write(Int n);
extern void sys_exit(Int code);
