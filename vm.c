#include "rt/syscalls.h"
#include "rt/io.h"


enum Op {
  LOAD    = 0x00,
  STORE   = 0x01,
  GLOAD   = 0x02,
  GSTORE  = 0x03,
  CONST   = 0x04,
  ADD     = 0x05,
  SUB     = 0x06,
  MUL     = 0x07,
  DIV     = 0x08,
  MOD     = 0x09,
  AND     = 0x0A,
  OR      = 0x0B,
  LT      = 0x0C,
  LE      = 0x0D,
  GT      = 0x0E,
  GE      = 0x0F,
  EQ      = 0x10,
  NE      = 0x11,
  JMP     = 0x12,
  JZ      = 0x13,
  JNZ     = 0x14,
  CALL    = 0x15,
  SYSCALL = 0x16,
  RET     = 0x17,
  ENTER   = 0x18,
  LEAVE   = 0x20
};

typedef struct {
  Byte opcode;
  Byte pad[7];
  Int  arg;
} Instruction;

#define static_assert(cond) typedef Byte _unused[(cond)]

static_assert(sizeof(Instruction) == 16);

typedef struct {
  Int stack[256];
  Int callstack[256];
  Int stackframe[256];
  Int memory[4 * 1024 * 1024];
} State;

static State STATE;

static Int run_code(Instruction* instructions, Int n, Int entrypoint, Int globals) {
  // Move to locals for faster access
  Int* STACK = STATE.stack;
  Int* CALLSTACK = STATE.callstack;
  Int* STACKFRAME = STATE.stackframe;
  Int* MEMORY = STATE.memory;

  Int ip = entrypoint;
  Int stack = 0;
  Int callstack = 0;
  Int stackframe = 0;
  Int mem = globals;

  Int r, l;

  while (ip < n) {
    Instruction* instruction = instructions + ip;
    // puts("IP: ");
    // sys_write(ip);
    // puts("OP: ");
    // sys_write(instruction->opcode);
    // puts("MEM: ");
    // sys_write(mem);
    // puts("STACK: ");
    // sys_write(stack);
    switch (instruction->opcode) {
      case LOAD:
        STACK[stack++] = MEMORY[mem - instruction->arg];
        ++ip;
        break;
      case STORE:
        MEMORY[mem - instruction->arg] = STACK[--stack];
        ++ip;
        break;
      case GLOAD:
        STACK[stack++] = MEMORY[instruction->arg];
        ++ip;
        break;
      case GSTORE:
        MEMORY[instruction->arg] = STACK[--stack];
        ++ip;
        break;
      case CONST:
        STACK[stack++] = instruction->arg;
        ++ip;
        break;
      case ADD:
        r = STACK[--stack];
        STACK[stack-1] += r;
        ++ip;
        break;
      case SUB:
        r = STACK[--stack];
        STACK[stack-1] -= r;
        ++ip;
        break;
      case MUL:
        r = STACK[--stack];
        STACK[stack-1] *= r;
        ++ip;
        break;
      case DIV:
        r = STACK[--stack];
        STACK[stack-1] /= r;
        ++ip;
        break;
      case MOD:
        r = STACK[--stack];
        STACK[stack-1] %= r;
        ++ip;
        break;
      case AND:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l && r;
        ++ip;
        break;
      case OR:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l || r;
        ++ip;
        break;
      case LT:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l < r;
        ++ip;
        break;
      case LE:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l <= r;
        ++ip;
        break;
      case GT:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l > r;
        ++ip;
        break;
      case GE:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l >= r;
        ++ip;
        break;
      case EQ:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l == r;
        ++ip;
        break;
      case NE:
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l != r;
        ++ip;
        break;
      case JMP:
        ip = instruction->arg;
        break;
      case JZ:
        r = STACK[--stack];
        ip = !r ? instruction->arg : (ip + 1);
        break;
      case JNZ:
        r = STACK[--stack];
        ip = r ? instruction->arg : (ip + 1);
        break;
      case CALL:
        CALLSTACK[callstack++] = ip + 1;
        ip = instruction->arg;
        break;
      case SYSCALL:
        switch (instruction->arg) {
          case SYS_READ:
            STACK[stack++] = sys_read();
            break;
          case SYS_WRITE:
            sys_write(STACK[--stack]);
            break;
          case SYS_EXIT:
            return STACK[--stack];
          default:
            puts("Unknown syscall ");
            sys_write(instruction->arg);
            return -1;
        }
        ++ip;
        break;
      case RET:
        ip = CALLSTACK[--callstack];
        mem -= STACKFRAME[--stackframe];
        break;
      case ENTER:
        // n args
        r = instruction->arg & 0xFFFFFFFF;
        // n locals
        l = instruction->arg >> 32;
        STACKFRAME[stackframe++] = r + l;
        mem += r + l;

        for (Int i = 0; i < r; ++i) {
          MEMORY[mem - i] = STACK[--stack];
        }
        ++ip;
        break;
      case LEAVE:
        puts("Reached LEAVE instruction\n");
        return -1;
      default:
        puts("Unhandled opcode ");
        sys_write(instruction->opcode);
        return -1;
    }
  }

  return -1;
}

#ifdef _WIN32
#define WINAPI __stdcall
extern Byte* WINAPI GetCommandLineA();
#define cli_args() GetCommandLineA()
#else
#error "No runtime for platform"
#endif

static Byte* parse_args(void) {
  Byte* args = cli_args();
  while (*args != '\0' && *args != ' ') {
    ++args;
  }

  if (!*args) {
    return NULL;
  }


  while (*args != '\0' && *args == ' ') {
    ++args;
  }

  Byte* filename = args;
  while (*args != '\0' && *args != ' ') {
    ++args;
  }

  if (*args) {
    // We should have a single argument
    return NULL;
  }

  return filename;
}

static const Byte MAGIC[] = {
    '.', 'n', 'o', 'x', 'b', 'c', '-', '-'
};

#define HEADER_SIZE (sizeof(MAGIC) + sizeof(Int))
static_assert(HEADER_SIZE == sizeof(Instruction));

static Bool check_magic(Byte* data) {
  for (Int i = 0; i < sizeof(MAGIC); ++i) {
    if (data[i] != MAGIC[i]) {
      return false;
    }
  }

  return true;
}

static Int run(const Byte* filename) {
  Handle file = open(filename);
  if (!file) {
    puts("Failed to open code file\n");
    return -1;
  }

  Int size = file_size(file);
  if (size < 0) {
    puts("Failed to retrive code file size\n");
    return -1;
  }

  Byte* code = mmap(file);
  if (!code) {
    puts("Failed to map code file to memory\n");
    return -1;
  }

  if (size < sizeof(MAGIC) || !check_magic(code)) {
    puts("Invalid or corrupted file (magic)\n");
    return -1;
  }

  if ((size - HEADER_SIZE) % sizeof(Instruction) != 0) {
    puts("Invalid or corrupted file (size)\n");
    return -1;
  }

  Int entrypoint = *(Int*)(code + sizeof(MAGIC));
  Int globals = entrypoint & 0xFFFFFFFF;
  entrypoint >>= 32;
  Instruction* instructions = (Instruction*)(code + sizeof(Instruction));
  Int n = size / sizeof(Instruction);
  return run_code(instructions, n, entrypoint, globals);
}

int main(void) {
  sys_setup();

  Byte* filename = parse_args();
  if (!filename) {
    puts("Usage: vm <filename>\n");
    sys_exit(-1);
  }

  sys_exit(run(filename));
}