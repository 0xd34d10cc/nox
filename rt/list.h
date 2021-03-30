#pragma once

#include "types.h"


typedef struct {
  Int refs;

  Int* data;
  Int size;
  Int capacity;
} List;


extern List*  sys_list(void);
extern List*  sys_list_from_data(Int* data, Int n);
extern Int    sys_list_get(List* list, Int i);
extern void   sys_list_set(List* list, Int i, Int val);
extern void   sys_push(List* list, Int val);
extern Int    sys_len(List* list);
extern void   sys_clear(List* list);
extern List*  sys_slice(List* list, Int left, Int right);
extern void   sys_list_ref(List* list);
extern void   sys_list_unref(List* list);