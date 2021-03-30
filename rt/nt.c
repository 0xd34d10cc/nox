#include "types.h"
#include "syscalls.h"
#include "io.h"

#include "common.c"

#define WINAPI __stdcall
extern Handle WINAPI GetProcessHeap(void);
static const Int NO_SYNC = 0x01;
extern Handle WINAPI HeapCreate(Int options, Int size, Int max_size);
extern Byte* WINAPI HeapAlloc(Handle heap, Int flags, Int size);
extern Byte* WINAPI HeapReAlloc(Handle heap, Int flags, Byte* p, Int size);
extern Bool  WINAPI HeapFree(Handle heap, Int flags, Byte* p);
static const Int GET_STDIN  = -10;
static const Int GET_STDOUT = -11;
extern Handle WINAPI GetStdHandle(Int type);
static const Int ACCESS_READ   = 0x80000000L;
static const Int ACCESS_WRITE  = 0x40000000L;
static const Int OPEN_EXISTING = 3;
static const Int NO_ATTRIBUTES = 0x80;
extern Handle WINAPI CreateFileA(const Byte* filename, Int access, Int share, void* security, Int create, Int attributes, Handle template);
extern Bool   WINAPI ReadFile(Handle file, Byte* buffer, Int n, Int* read, void* overlapped);
extern Bool   WINAPI WriteFile(Handle file, const Byte* buffer, Int n, Int* written, void* overlapped);
extern Bool   WINAPI GetFileSizeEx(Handle file, Int* size);
static const Int PAGE_READWRITE = 4;
extern Handle WINAPI CreateFileMappingA(Handle file, void* security, Int protect, Int maxsize_high, Int maxsize_low, const Byte* name);
static const Int MAP_ALL_ACCESS = 0x1 | 0x2 | 0x4 | 0x8 | 0x10 | 0xF0000;
extern Byte*  WINAPI MapViewOfFile(Handle file, Int access, Int offset_high, Int offset_low, Int size);
extern Bool   WINAPI UnmapViewOfFile(Byte* addtess);
extern Bool   WINAPI CloseHandle(Handle handle);
extern void   WINAPI ExitProcess(Int code);

static Handle HEAP;

static Handle STDIN;
typedef struct {
  Byte data[1024];
  Int n;
} IoBuffer;

static IoBuffer STDIN_BUFFER;

static Handle STDOUT;

extern void sys_setup(void) {
  HEAP   = HeapCreate(NO_SYNC, 0, 0);
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

// Memory allocation
static Byte* alloc(Int n) {
  return HeapAlloc(HEAP, 0, n);
}

static Byte* realloc(Byte* p, Int n) {
  return HeapReAlloc(HEAP, 0, p, n);
}

static void dealloc(Byte* p) {
  HeapFree(HEAP, 0, p);
}

// IO functions
extern void puts(const Byte* s) {
  Int len = 0;
  const Byte* p = s;
  while (*p++) ++len;
  WriteFile(STDOUT, s, len, NULL, NULL);
}

extern Handle open(const Byte* filename) {
  Handle file = CreateFileA(filename, ACCESS_READ | ACCESS_WRITE, 0, NULL, OPEN_EXISTING, NO_ATTRIBUTES, NULL);
  if ((Int)file == -1) {
    return NULL;
  }
  return file;
}

extern void close(Handle file) {
  CloseHandle(file);
}

extern Int file_size(Handle file) {
  Int size = 0;
  if (!GetFileSizeEx(file, &size)) {
    return -1;
  }
  return size;
}

extern Byte* mmap(Handle file) {
  Handle mapping = CreateFileMappingA(file, NULL, PAGE_READWRITE, 0, 0, NULL);
  if (!mapping) {
    return NULL;
  }

  Byte* view = MapViewOfFile(mapping, MAP_ALL_ACCESS, 0, 0, 0);
  CloseHandle(mapping);
  return view;
}

extern void munmap(Byte* map) {
  UnmapViewOfFile(map);
}

// syscalls
extern Int sys_input(void) {
  if (!fill_buffer(STDIN, &STDIN_BUFFER)) {
    panic("sys_input() failed: io error\n");
  }

  Int parsed = 0;
  Int val = from_chars(STDIN_BUFFER.data, STDIN_BUFFER.n, &parsed);
  if (parsed <= 0) {
    panic("sys_input() failed: invalid integer\n");
  }

  for (Int i = 0; i < STDIN_BUFFER.n - parsed; ++i) {
    STDIN_BUFFER.data[i] = STDIN_BUFFER.data[i + parsed];
  }
  STDIN_BUFFER.n -= parsed;
  return val;
}

extern void sys_print(Int val) {
  Byte buffer[32];
  Int len = to_chars(buffer, sizeof(buffer), val);
  if (len < 0) {
    panic("sys_print() failed: int conversion\n");
  }

  buffer[len] = '\n';
  ++len;

  Int written = 0;
  Bool success = WriteFile(STDOUT, buffer, len, &written, NULL);
  if (!success) {
    panic("sys_print() failed: io error\n");
  }

  if (written != len) {
    panic("sys_print() failed: short write\n");
  }
}

extern void sys_exit(Int code) {
  ExitProcess(code);
}