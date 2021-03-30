#pragma once

#include "types.h"

enum {
  SYS_EXIT  = 0,

  SYS_PRINT = 100,
  SYS_INPUT = 101,
};

extern void sys_setup(void);
extern Int  sys_input(void);
extern void sys_print(Int n);
extern void sys_exit(Int code);
