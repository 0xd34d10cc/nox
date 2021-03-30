#pragma once

#include "types.h"


static void panic(const Byte* message);
static Int from_chars(const Byte* buffer, Int len, Int* parsed);
static Int to_chars(Byte* s, Int len, Int val);