#pragma once

#include "types.h"

enum {
  SYS_READ  = 0,
  SYS_WRITE = 1,
  SYS_EXIT  = 2
};

extern void sys_setup(void);
extern Int  sys_read(void);
extern void sys_write(Int n);
extern void sys_exit(Int code);
