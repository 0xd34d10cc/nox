#include "intrinsics.h"

extern void memcpy(Byte* dst, Byte* src, Int len) {
  while (len--) {
    *dst++ = *src++;
  }
}