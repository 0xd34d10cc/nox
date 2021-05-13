#include "rt/syscalls.h"
#include "rt/io.h"

#define _STR(x) #x
#define STR(x) _STR(x)
#define FILE_LINE __FILE__ ":" STR(__LINE__)

#ifdef RT_CHECKS_ON
#define RT_CHECK(cond)                                           \
  do {                                                           \
    if (!(cond)) {                                               \
      puts("Failed to execute instruction at ip=");              \
      sys_print(ip);                                             \
      puts("Condition at " FILE_LINE  " is false: " #cond "\n"); \
      return -1;                                                 \
    }                                                            \
  } while (0)
#else
#define RT_CHECK(cond)
#endif

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

#define MAX_STACK_DEPTH 256
// assuming less than 16 args+locals per function on average
#define MAX_MEM MAX_STACK_DEPTH * 16
typedef struct {
  Int stack[MAX_STACK_DEPTH];
  Int callstack[MAX_STACK_DEPTH];
  Int stackframe[MAX_STACK_DEPTH];
  Int memory[MAX_MEM];
} State;

static State STATE;

static Int run_code(Instruction* instructions, Int n, Int entrypoint, Int globals) {
  Int* STACK = STATE.stack;
  Int* CALLSTACK = STATE.callstack;
  Int* STACKFRAME = STATE.stackframe;
  Int* MEMORY = STATE.memory;

  Int ip = entrypoint;
  Int stack = 0;
  Int callstack = 0;
  Int stackframe = 0;
  Int mem = globals;

  List* list;
  Int r, l, idx, val;

  while (ip < n) {
    Instruction* instruction = instructions + ip;
    // puts("IP: ");
    // sys_print(ip);
    // puts("OP: ");
    // sys_print(instruction->opcode);
    // puts("MEM: ");
    // sys_print(mem);
    // puts("STACK: ");
    // sys_print(stack);
    switch (instruction->opcode) {
      case LOAD:
        RT_CHECK(stack < MAX_STACK_DEPTH);
        RT_CHECK(stackframe > 0);
        RT_CHECK(instruction->arg < STACKFRAME[stackframe-1]);
        STACK[stack++] = MEMORY[mem - instruction->arg];
        ++ip;
        break;
      case STORE:
        RT_CHECK(stack > 0);
        RT_CHECK(stackframe > 0);
        RT_CHECK(instruction->arg < STACKFRAME[stackframe-1]);
        MEMORY[mem - instruction->arg] = STACK[--stack];
        ++ip;
        break;
      case GLOAD:
        RT_CHECK(stack < MAX_STACK_DEPTH);
        RT_CHECK(instruction->arg < globals);
        STACK[stack++] = MEMORY[instruction->arg];
        ++ip;
        break;
      case GSTORE:
        RT_CHECK(stack > 0);
        RT_CHECK(instruction->arg < globals);
        MEMORY[instruction->arg] = STACK[--stack];
        ++ip;
        break;
      case CONST:
        RT_CHECK(stack < MAX_STACK_DEPTH);
        STACK[stack++] = instruction->arg;
        ++ip;
        break;
      case ADD:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        STACK[stack-1] += r;
        ++ip;
        break;
      case SUB:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        STACK[stack-1] -= r;
        ++ip;
        break;
      case MUL:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        STACK[stack-1] *= r;
        ++ip;
        break;
      case DIV:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        STACK[stack-1] /= r;
        ++ip;
        break;
      case MOD:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        STACK[stack-1] %= r;
        ++ip;
        break;
      case AND:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l && r;
        ++ip;
        break;
      case OR:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l || r;
        ++ip;
        break;
      case LT:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l < r;
        ++ip;
        break;
      case LE:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l <= r;
        ++ip;
        break;
      case GT:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l > r;
        ++ip;
        break;
      case GE:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l >= r;
        ++ip;
        break;
      case EQ:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l == r;
        ++ip;
        break;
      case NE:
        RT_CHECK(stack > 1);
        r = STACK[--stack];
        l = STACK[stack-1];
        STACK[stack-1] = l != r;
        ++ip;
        break;
      case JMP:
        RT_CHECK(instruction->arg < n);
        ip = instruction->arg;
        break;
      case JZ:
        RT_CHECK(instruction->arg < n);
        r = STACK[--stack];
        ip = !r ? instruction->arg : (ip + 1);
        break;
      case JNZ:
        RT_CHECK(instruction->arg < n);
        r = STACK[--stack];
        ip = r ? instruction->arg : (ip + 1);
        break;
      case CALL:
        RT_CHECK(instruction->arg < n);
        RT_CHECK(instructions[instruction->arg].opcode == ENTER);
        RT_CHECK(callstack < MAX_STACK_DEPTH);
        CALLSTACK[callstack++] = ip + 1;
        ip = instruction->arg;
        break;
      case SYSCALL:
        switch (instruction->arg) {
          case SYS_LIST:
            RT_CHECK(stack < MAX_STACK_DEPTH);
            STACK[stack++] = (Int)sys_list();
            break;
          case SYS_LIST_GET:
            RT_CHECK(stack > 1);
            list = (List*)STACK[--stack];
            idx = STACK[--stack];
            STACK[stack++] = sys_list_get(list, idx);
            break;
          case SYS_LIST_SET:
            RT_CHECK(stack > 2);
            list = (List*)STACK[--stack];
            idx = STACK[--stack];
            sys_list_set(list, idx, STACK[--stack]);
            break;
          case SYS_LIST_PUSH:
            RT_CHECK(stack > 1);
            list = (List*)STACK[--stack];
            val = STACK[--stack];
            sys_push(list, val);
            break;
          case SYS_LIST_LEN:
            RT_CHECK(stack > 0);
            list = (List*)STACK[--stack];
            STACK[stack++] = sys_len(list);
            break;
          case SYS_LIST_CLEAR:
            RT_CHECK(stack > 0);
            list = (List*)STACK[--stack];
            sys_clear(list);
            break;
          case SYS_LIST_SLICE:
            RT_CHECK(stack > 2);
            list = (List*)STACK[--stack];
            l = STACK[--stack];
            r = STACK[--stack];
            STACK[stack++] = (Int)sys_slice(list, l, r);
            break;
          case SYS_LIST_REF:
            RT_CHECK(stack > 0);
            list = (List*)STACK[--stack];
            sys_list_ref(list);
            break;
          case SYS_LIST_UNREF:
            RT_CHECK(stack > 0);
            list = (List*)STACK[--stack];
            sys_list_unref(list);
            break;
          case SYS_INPUT:
            RT_CHECK(stack < MAX_STACK_DEPTH);
            STACK[stack++] = sys_input();
            break;
          case SYS_PRINT:
            RT_CHECK(stack > 0);
            sys_print(STACK[--stack]);
            break;
          case SYS_EXIT:
            RT_CHECK(stack > 0);
            return STACK[--stack];
          default:
            puts("Unknown syscall ");
            sys_print(instruction->arg);
            return -1;
        }
        ++ip;
        break;
      case RET:
        RT_CHECK(callstack > 0);
        RT_CHECK(stackframe > 0);
        ip = CALLSTACK[--callstack];
        mem -= STACKFRAME[--stackframe];
        break;
      case ENTER:
        RT_CHECK(stackframe < MAX_STACK_DEPTH);
        // n args
        r = instruction->arg & 0xFFFFFFFF;
        // n locals
        l = instruction->arg >> 32;
        STACKFRAME[stackframe++] = r + l;
        mem += r + l;

        RT_CHECK(r <= stack);
        RT_CHECK(mem < MAX_MEM);
        for (Int i = 0; i < r; ++i) {
          MEMORY[mem - i] = STACK[--stack];
        }
        ++ip;
        break;
      case LEAVE:
        puts("Reached LEAVE instruction\n");
        return -1;
      default:
        puts("Unknown opcode ");
        sys_print(instruction->opcode);
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
  while (*args && *args != ' ') {
    ++args;
  }

  if (!*args) {
    return NULL;
  }


  while (*args && *args == ' ') {
    ++args;
  }

  Byte* filename = args;
  while (*args && *args != ' ') {
    ++args;
  }

  if (*args) {
    // We should have only one argument
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

  if (size < HEADER_SIZE || !check_magic(code)) {
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
  Instruction* instructions = (Instruction*)(code + HEADER_SIZE);
  Int n = size / sizeof(Instruction);
  if (entrypoint >= n) {
    puts("Invalid or corrupted file (entrypoint)\n");
    return -1;
  }

  Int ret = run_code(instructions, n, entrypoint, globals);
  munmap(code);
  close(file);
  return ret;
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