#include "list.h"

#include "mem.h"
#include "intrinsics.h"
#include "utils.h"


extern List* sys_list(void) {
  List* list = (List*)alloc(sizeof(List));
  list->refs = 0;
  list->data = NULL;
  list->size = 0;
  list->capacity = 0;
  return list;
}

extern List* sys_list_from_data(Int* data, Int n) {
  List* list = sys_list();
  list->data = (Int*)alloc(n * sizeof(Int));
  list->size = n;
  list->capacity = n;
  memcpy((Byte*)list->data, (Byte*)data, n * sizeof(Int));
  return list;
}

extern Int sys_list_get(List* list, Int i) {
  if (i < 0 || i >= list->size) {
    panic("sys_list_get: index out of range\n");
  }

  return list->data[i];
}

extern void sys_list_set(List* list, Int i, Int val) {
  if (i < 0 || i >= list->size) {
    panic("sys_list_set: index out of range\n");
  }

  list->data[i] = val;
}

extern void sys_list_push(List* list, Int val) {
  if (list->size == list->capacity) {
    if (!list->data) {
      list->data = (Int*)alloc(sizeof(Int));
      list->capacity = 1;
    }
    else {
      Int new_cap = list->size * 2;
      list->data = (Int*)realloc((Byte*)list->data, new_cap * sizeof(Int));
      list->capacity = new_cap;
    }
  }

  list->data[list->size++] = val;
}

extern void sys_list_clear(List* list) {
  list->size = 0;
}

extern List* sys_list_slice(List* list, Int left, Int right) {
  if (left >= list->size || right >= list->size) {
    panic("sys_list_slice: slice bound is out of range");
  }

  if (left < 0) {
    if (left == -1) {
      left = 0;
    }
    else {
      panic("sys_list_slice: slice left bound is negative");
    }
  }

  if (right < 0) {
    if (right == -1) {
      right = list->size;
    }
    else {
      panic("sys_list_slice: slice right bound is negative");
    }
  }

  Int* start = list->data + left;
  Int size = right - left;
  return sys_list_from_data(start, size);
}

extern void sys_list_ref(List* list) {
  ++list->refs;
}

extern void sys_list_unref(List* list) {
  if (!--list->refs) {
    dealloc((Byte*)list->data);
    dealloc((Byte*)list);
  }
}
