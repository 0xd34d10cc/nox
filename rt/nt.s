; win64 calling convention
; args: rcx, rdx, r8, and r9
; ret:  rax
; volatile: RAX, RCX, RDX, R8, R9, R10, R11
; non-volatile: RBX, RBP, RDI, RSI, RSP, R12, R13, R14, R15

global sys_setup
global sys_read
global sys_write
global sys_exit

extern  GetStdHandle
extern  WriteFile
extern  ExitProcess

; Constants
NULL       EQU 0
GET_STDIN  EQU -10
GET_STDOUT EQU -11

; Initialized data segment
section .data
    PARSE_INT_FAIL db "Failed to parse integer", 0xa
    PARSE_INT_FAIL_LEN EQU $-PARSE_INT_FAIL

    EXAMPLE db "  42 "
    EXAMPLE_LEN EQU $-EXAMPLE ; Address of this line ($) - address of SPACES

; Uninitialized data segment
section .bss
    alignb 8
    STDOUT  resq 1
    STDIN   resq 1

; Code segment
section .text

; void sys_setup(void)
sys_setup:
    sub     rsp, 32                                  ; 32 bytes of shadow space
    mov     rcx, GET_STDIN
    call    GetStdHandle
    mov     [rel STDIN], rax
    mov     rcx, GET_STDOUT
    call    GetStdHandle
    mov     [rel STDOUT], rax
    add     rsp, 32                                  ; Remove the 32 bytes
    ret

; panic(char* s, int lne)
panic:
    call write_str
    mov rcx, -1
    call sys_exit
; end panic()

; void write_str(char* s, int len)
write_str:
    sub rsp, 16 ; written + 5th parameter

    mov r8, rdx            ; len
    mov rdx, rcx           ; msg
    mov rcx, [rel STDOUT]  ; out
    lea r9, [rsp + 8]      ; written
    mov qword [rsp], 0     ; overlapped

    sub rsp, 32 ; shadow space
    ; FIXME: this function assumes written == len
    call WriteFile

    add rsp, 32+16
    ret
; end write_str()

; int skip_spaces(char* s, int len)
skip_spaces:
    xor rax, rax
    jmp skip_spaces_cond
skip_spaces_body:
    inc rax
skip_spaces_cond:
    cmp rax, rdx
    je skip_spaces_out
    cmp byte [rcx + rax], 32 ; ' '
    je skip_spaces_body
    cmp byte [rcx + rax], 10 ; '\n'
    je skip_spaces_body
    cmp byte [rcx + rax], 13 ; '\r'
    je skip_spaces_body
    cmp byte [rcx + rax], 9  ; '\t'
    je skip_spaces_body
skip_spaces_out:
    ret
; end skip_spaces()

; int parse_int(char* s, int len, bool* ok)
parse_int:
    ; regs:
    ; s = rcx
    ; len = rdx
    ; ok = r8
    ; is_negative = r10
    ; c = r11

    ; nspaces = skip_spaces(s, len)
    ; s += nspaces
    ; len -= nspaces
    call skip_spaces
    add rcx, rax
    sub rdx, rax
    test rdx, rdx
    jz parse_int_fail

    ; is_negative = *s == '-'
    ; if (is_negative) { ++s; --len; if len == 0 { fail() } }
    xor r10, r10
    cmp byte [rcx], 45
    jne parse_int_start_parsing
    mov r10, 1
    inc rcx
    dec rdx
    test rdx, rdx
    jz parse_int_fail

parse_int_start_parsing:
    cmp byte [rcx], 48 ; '0'
    jb parse_int_fail
    cmp byte [rcx], 57 ; '9'
    ja parse_int_fail

    ; res = 0
    xor rax, rax
parse_int_body:
    ; do { res = res * 10 + (*s - '0'); ++s; --len; } while (len != 0 && isdigit(*s))
    imul rax, 10
    movzx r11, byte [rcx]
    sub r11, 48 ; '0'
    add rax, r11
    inc rcx
    dec rdx
    test rdx, rdx
    jz parse_int_success
    cmp byte [rcx], 48 ; '0'
    jb parse_int_skip_rest
    cmp byte [rcx], 57 ; '9'
    jbe parse_int_body

; if skip_spaces(s, len) != len { fail() }
parse_int_skip_rest:
    push rax
    call skip_spaces
    cmp rax, rdx
    pop rax
    jne parse_int_fail

; if (is_negative) { res = -res; }
parse_int_success:
    test r10, r10
    jz parse_int_success_finish
    neg rax
; *ok = true; return res;
parse_int_success_finish:
    mov byte [r8], 1
    ret

; *ok = false; return res;
parse_int_fail:
    mov rax, -1
    mov byte [r8], 0
    ret
; end parse_int()

; int sys_read(void)
sys_read:
    sub rsp, 8
    mov rcx, EXAMPLE
    mov rdx, EXAMPLE_LEN
    mov r8, rsp
    call parse_int
    cmp byte [rsp], 0
    je sys_read_fail
    add rsp, 8
    ret

sys_read_fail:
    mov rcx, PARSE_INT_FAIL
    mov rdx, PARSE_INT_FAIL_LEN
    call panic

; void sys_write(int num)
sys_write:
    ret

; void sys_exit(int code)
sys_exit:
    jmp ExitProcess