#pragma once

#include "types.h"

extern void puts(const Byte* s);
extern Handle open(const Byte* filename);
extern Int file_size(Handle file);
extern Byte* mmap(Handle file);