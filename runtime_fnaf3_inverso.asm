; ========================================================
; INGENIERÍA INVERSA: RUNTIME.JS -> ENSAMBLADOR (ASM)
; Motor Clickteam Fusion / FNAF 3
; ========================================================
section .data
    msg_init db 'Iniciando emulación de FNAF 3 runtime', 0

section .text
global main

main:
    MOV EBP, ESP
    PUSH EBX
    ; Inicialización de registros base del Runtime
    MOV EAX, 0x3F3 ; Cabecera de chunk FNAF 3

func_kb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_lb:
    ; Parámetros: O
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_we:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_ze:
    ; Parámetros: O
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Ae:
    ; Parámetros: O
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Be:
    ; Parámetros: O,qa
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Ce:
    ; Parámetros: O,qa
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_t:
    ; Parámetros: a,b
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_T:
    ; Parámetros: a,b,c
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_V:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_L:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Y:
    ; Parámetros: a,b,c,d
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_ra:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Za:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_la:
    ; Parámetros: a,b
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_ia:
    ; Parámetros: a,b,c
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Fa:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_wa:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_S:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_nb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_da:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_ob:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_pb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_qb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_rb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_sb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_tb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_ub:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_vb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_wb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_xb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_yb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_zb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Ab:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Bb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Cb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Db:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Eb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Fb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Gb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Hb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Ib:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Jb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Kb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Lb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Mb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Nb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Ob:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Pb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET

func_Qb:
    ; Parámetros: 
    PUSH EBP
    MOV EBP, ESP
    XOR EAX, EAX
    LEAVE
    RET
