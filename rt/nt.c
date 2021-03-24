#include "types.h"
#include "syscalls.h"

#define WINAPI __stdcall
static const int GET_STDIN  = -10;
static const int GET_STDOUT = -11;
extern Handle WINAPI GetStdHandle(int type);
extern Bool   WINAPI ReadFile(Handle file, Byte* buffer, Int n, Int* read, void* overlapped);
extern Bool   WINAPI WriteFile(Handle file, const Byte* buffer, Int n, Int* written, void* overlapped);
extern void   WINAPI ExitProcess(Int code);

static Handle STDIN;
typedef struct {
  Byte data[1024];
  Int n;
} IoBuffer;

static IoBuffer STDIN_BUFFER;

static Handle STDOUT;

extern void sys_setup(void) {
  STDIN  = GetStdHandle(GET_STDIN);
  STDOUT = GetStdHandle(GET_STDOUT);
  STDIN_BUFFER.n = 0;
}

static Bool fill_buffer(Handle* file, IoBuffer* buffer) {
  static const Int ERROR_BROKEN_PIPE = 0x6d;

  Int read = 0;
  Bool success = ReadFile(file, buffer->data + buffer->n, sizeof(buffer->data) - buffer->n, &read, NULL);
  if (!success) {
    success = GetLastError() == ERROR_BROKEN_PIPE;
  }

  if (success) {
    buffer->n += read;
  }

  return success;
}

static void puts(const char* s) {
  Int len = 0;
  const char* p = s;
  while (*p++) ++len;
  WriteFile(STDOUT, s, len, NULL, NULL);
}

static void panic(const char* s) {
  puts(s);
  ExitProcess(-1);
}

static Int parse_int(const Byte* buffer, Int len, Int* parsed) {
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

extern Int sys_read(void) {
  if (!fill_buffer(STDIN, &STDIN_BUFFER)) {
    panic("sys_read() failed: io error\n");
  }

  Int parsed = 0;
  Int val = parse_int(STDIN_BUFFER.data, STDIN_BUFFER.n, &parsed);
  if (parsed <= 0) {
    panic("sys_read() failed: invalid integer\n");
  }

  for (Int i = 0; i < STDIN_BUFFER.n - parsed; ++i) {
    STDIN_BUFFER.data[i] = STDIN_BUFFER.data[i + parsed];
  }
  STDIN_BUFFER.n -= parsed;
  return val;
}

extern void sys_write(Int val) {
  Byte buffer[32];
  Bool negative = val < 0;
  if (negative) {
    val = -val;
  }

  buffer[31] = '\n';
  Int i = 30;
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
  Int written = 0;
  Bool success = WriteFile(STDOUT, buffer + i, sizeof(buffer) - i, &written, NULL);
  if (!success) {
    panic("sys_write() failed: io error\n");
  }

  if (written != sizeof(buffer) - i) {
    panic("sys_write() failed: short write\n");
  }
}

extern void sys_exit(Int code) {
  ExitProcess(code);
}