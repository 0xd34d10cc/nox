#pragma once

#include "types.h"

extern void   puts(const Byte* s);
extern Handle open(const Byte* filename);
extern void   close(Handle file);
extern Int    file_size(Handle file);
extern Byte*  mmap(Handle file);
extern void   munmap(Byte* map);