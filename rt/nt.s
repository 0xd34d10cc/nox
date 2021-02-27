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
    MSG db "Hello, world!", 0Ah
    LEN EQU $-MSG ; Address of this line ($) - address of MSG

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

; int sys_read(void)
sys_read:
    mov rax, 2
    ret

; void sys_write(int num)
sys_write:
    ret

; void sys_exit(int code)
sys_exit:
    jmp ExitProcess

; main:
;     sub   rsp, 8                                   ; Align the stack to a multiple of 16 bytes

;     sub   rsp, 32 + 8 + 8                          ; Shadow space + 5th parameter + align stack
;                                                    ; to a multiple of 16 bytes
;     mov   rcx, [rel STDOUT]                        ; 1st parameter
;     lea   rdx, [rel MSG]                           ; 2nd parameter
;     mov   r8, LEN                                  ; 3rd parameter
;     lea   r9, [rel WRITTEN]                        ; 4th parameter
;     mov   qword [rsp + 4 * 8], NULL                ; 5th parameter
;     call  WriteFile                                ; Output can be redirect to a file using >
;     add   rsp, 48                                  ; Remove the 48 bytes

;     xor   rcx, rcx
;     call  ExitProcess
