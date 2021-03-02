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
extern  GetLastError
extern  ReadFile
extern  WriteFile
extern  ExitProcess

; Constants
NULL       EQU 0
GET_STDIN  EQU -10
GET_STDOUT EQU -11

; Initialized data segment
section .data
    SYS_READ_FAIL1 db "read() call failed due to io error", 0xa
    SYS_READ_FAIL1_LEN EQU $-SYS_READ_FAIL1

    SYS_READ_FAIL2 db "read() call failed due to invalid int", 0xa
    SYS_READ_FAIL2_LEN EQU $-SYS_READ_FAIL2

    EXAMPLE db "  9 "
    EXAMPLE_LEN EQU $-EXAMPLE ; Address of this line ($) - address of SPACES

; Uninitialized data segment
section .bss
    alignb 8
    STDOUT  resq 1    ; stdout handle
    STDIN   resq 1    ; stdin handle
    NREAD   resq 1    ; number of bytes in buffer
    BUFFER  resb 1024 ; input buffer

; Code segment
section .text

; void sys_setup(void)
sys_setup:
    sub     rsp, 32                                  ; 32 bytes of shadow space
    mov     rcx, GET_STDIN
    call    GetStdHandle
    mov     qword [rel STDIN], rax
    mov     qword [rel NREAD], 0
    mov     rcx, GET_STDOUT
    call    GetStdHandle
    mov     qword [rel STDOUT], rax
    add     rsp, 32                                  ; Remove the 32 bytes
    ret
; end sys_setup()

; panic(char* s, int lne)
panic:
    call    write_str
    mov     rcx, -1
    call    sys_exit
; end panic()

; void consume(int n)
; basically memmove(BUFFER, BUFFER+n, NREAD-n)
consume:
    mov     rax, BUFFER
    add     rax, rcx
    mov     rdx, qword [rel NREAD]
    sub     rdx, rcx
    mov     qword [rel NREAD], rdx
    jmp     consume_cond
consume_body:
    mov     r10b, [rax]
    sub     rax, rcx
    mov     [rax], r10b
    add     rax, rcx
    inc     rax
    dec     rdx
consume_cond:
    test    rdx, rdx
    jnz     consume_body
    ret

; bool read_str(void)
read_str:
    sub     rsp, 16            ; read + overlapped
    mov     rcx, [rel STDIN]   ; in
    mov     rdx, BUFFER
    add     rdx, qword [rel NREAD] ; buffer
    mov     r8, 1024
    sub     r8, qword [rel NREAD]  ; n bytes to read
    mov     qword [rsp + 8], 0
    lea     r9, [rsp + 8]      ; read
    mov     qword [rsp], 0     ; overlapped
    sub     rsp, 32            ; shadow space
    call    ReadFile
    add     rsp, 32
    mov     rcx, qword [rsp + 8]
    add     qword [rel NREAD], rcx
    add     rsp, 16
    test    rax, rax
    jnz     read_str_finish
    call    GetLastError
    cmp     rax, 0x6D ; ERROR_BROKEN_PIPE
    jne     read_str_finish
    mov     rax, 1
read_str_finish:
    ret
; end read_str()

; void write_str(char* s, int len)
write_str:
    sub     rsp, 16 ; written + overlapped

    mov     r8, rdx            ; len
    mov     rdx, rcx           ; msg
    mov     rcx, [rel STDOUT]  ; out
    lea     r9, [rsp + 8]      ; written
    mov     qword [rsp], 0     ; overlapped

    sub     rsp, 32            ; shadow space
    ; FIXME: this function assumes written == len
    call    WriteFile

    add     rsp, 32+16
    ret
; end write_str()

; int skip_spaces(char* s, int len)
skip_spaces:
    xor     rax, rax
    jmp     skip_spaces_cond
skip_spaces_body:
    inc     rax
skip_spaces_cond:
    cmp     rax, rdx
    je      skip_spaces_out
    cmp     byte [rcx + rax], 32 ; ' '
    je      skip_spaces_body
    cmp     byte [rcx + rax], 10 ; '\n'
    je      skip_spaces_body
    cmp     byte [rcx + rax], 13 ; '\r'
    je      skip_spaces_body
    cmp     byte [rcx + rax], 9  ; '\t'
    je      skip_spaces_body
skip_spaces_out:
    ret
; end skip_spaces()

; int parse_int(char* s, int len, int* read)
parse_int:
    ; regs:
    ; s = rcx
    ; len = rdx
    ; read = r8
    ; is_negative = r10
    ; c = r11

    ; nspaces = skip_spaces(s, len)
    ; s += nspaces
    ; len -= nspaces
    mov     qword [r8], rdx
    call    skip_spaces
    add     rcx, rax
    sub     rdx, rax
    test    rdx, rdx
    jz      parse_int_fail

    ; is_negative = *s == '-'
    ; if (is_negative) { ++s; --len; if len == 0 { fail() } }
    xor     r10, r10
    cmp     byte [rcx], 45
    jne     parse_int_start_parsing
    mov     r10, 1
    inc     rcx
    dec     rdx
    test    rdx, rdx
    jz      parse_int_fail

parse_int_start_parsing:
    cmp     byte [rcx], 48 ; '0'
    jb      parse_int_fail
    cmp     byte [rcx], 57 ; '9'
    ja      parse_int_fail

    ; res = 0
    xor     rax, rax
parse_int_body:
    ; do { res = res * 10 + (*s - '0'); ++s; --len; } while (len != 0 && isdigit(*s))
    imul    rax, 10
    movzx   r11, byte [rcx]
    sub     r11, 48 ; '0'
    add     rax, r11
    inc     rcx
    dec     rdx
    test    rdx, rdx
    jz      parse_int_success
    cmp     byte [rcx], 48 ; '0'
    jb      parse_int_success
    cmp     byte [rcx], 57 ; '9'
    jbe     parse_int_body

; if (is_negative) { res = -res; }
parse_int_success:
    test    r10, r10
    jz      parse_int_success_finish
    neg     rax
; *ok = true; return res;
parse_int_success_finish:
    sub     qword [r8], rdx
    ret

; *ok = false; return res;
parse_int_fail:
    mov     rax, -1
    mov     qword [r8], 0
    ret
; end parse_int()

; int sys_read(void)
sys_read:
    call    read_str
    test    rax, rax
    jz      sys_read_fail1
    sub     rsp, 8
    mov     rcx, BUFFER
    mov     rdx, qword [rel NREAD]
    mov     r8, rsp
    call    parse_int
    cmp     qword [rsp], 0
    je      sys_read_fail2
    mov     rcx, [rsp]
    mov     [rsp], rax
    call    consume
    mov     rax, [rsp]
    add     rsp, 8
    ret

sys_read_fail1:
    mov     rcx, SYS_READ_FAIL1
    mov     rdx, SYS_READ_FAIL1_LEN
    call    panic

sys_read_fail2:
    mov     rcx, SYS_READ_FAIL2
    mov     rdx, SYS_READ_FAIL2_LEN
    call    panic
; end sys_read()

; void sys_write(int num)
sys_write:
    ; s = rsp
    ; len = rcx
    ; is_negative = r10
    sub     rsp, 32 ; space for str
    xor     r10, r10
    mov     rax, rcx
    cmp     rax, 0
    jge      sys_write_start
    mov     r10, 1
    neg     rax
sys_write_start:
    mov     byte [rsp + 31], 10 ; '\n'
    mov     rcx, 30

sys_write_body:
    cqo
    mov     r8, 10
    idiv    r8
    add     rdx, 48 ; '\0'
    mov     byte [rsp + rcx], dl
    dec     rcx
    cmp     rax, 0
    jnz     sys_write_body
    test    r10, r10
    jz      sys_write_write
    mov     byte [rsp + rcx], 45  ; '-'
    dec     rcx
sys_write_write:
    inc     rcx
    lea     rax, [rsp + rcx]
    neg     rcx
    add     rcx, 32
    mov     rdx, rcx
    mov     rcx, rax
    call    write_str
    jmp     sys_write_end

sys_write_end:
    add     rsp, 32
    ret
; end sys_write()

; void sys_exit(int code)
sys_exit:
    jmp     ExitProcess