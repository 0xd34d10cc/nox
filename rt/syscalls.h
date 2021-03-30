#pragma once

#include "types.h"


enum {
  SYS_EXIT  = 0,

  SYS_LIST = 20,
  SYS_LIST_GET = 21,
  SYS_LIST_SET = 22,
  SYS_LIST_PUSH = 23,
  SYS_LIST_LEN = 24,
  SYS_LIST_CLEAR = 25,
  SYS_LIST_SLICE = 26,
  SYS_LIST_REF = 27,
  SYS_LIST_UNREF = 28,

  SYS_PRINT = 100,
  SYS_INPUT = 101,
};

extern void sys_setup(void);

extern void sys_exit(Int code);

#include "list.h"

extern Int  sys_input(void);
extern void sys_print(Int n);
