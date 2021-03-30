#pragma once

#include "types.h"


static Byte* alloc(Int n);
static Byte* realloc(Byte* memory, Int n);
static void dealloc(Byte* memory);