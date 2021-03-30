#include "utils.h"
#include "io.h"
#include "syscalls.h"


static void panic(const Byte* message) {
  puts(message);
  sys_exit(-1);
}

static Int to_chars(Byte* s, Int len, Int val) {
  Byte buffer[32];
  Bool negative = val < 0;
  if (negative) {
    val = -val;
  }

  Int i = sizeof(buffer) - 1;
  do {
    buffer[i] = '0' + (val % 10);
    val /= 10;
    i--;
  } while (val != 0);

  if (negative) {
    buffer[i] = '-';
    i--;
  }

  i++;

  Int n = sizeof(buffer) - i;
  if (n > len) {
    return -1;
  }

  memcpy(s, buffer + i, n);
  return n;
}

static Int from_chars(const Byte* buffer, Int len, Int* parsed) {
  Int i = 0;
  while (buffer[i] == ' ' || buffer[i] == '\n' || buffer[i] == '\r') {
    ++i;
  }

  if (i == len) {
    *parsed = -1;
    return -1;
  }

  Bool negative = 0;
  if (buffer[i] == '-') {
    negative = 1;
    ++i;
  }

  if (i == len || buffer[i] > '9' || buffer[i] < '0') {
    *parsed = -1;
    return -1;
  }

  Int val = 0;
  do {
    val *= 10;
    val += buffer[i] - '0';
    ++i;
  } while (i < len && '0' <= buffer[i] && buffer[i] <= '9');

  if (negative) {
    val = -val;
  }

  *parsed = i;
  return val;
}

