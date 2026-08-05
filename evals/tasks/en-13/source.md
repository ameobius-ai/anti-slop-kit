# UART0 Register Map
Base Address: 0x4000_C000

## CTRL - Offset: 0x0000, Width: 32 bits, Reset: 0x0000_0000
- Bit 0: ENABLE (RW)
- Bit 1: LOOPBACK (RW)

## STATUS - Offset: 0x0004, Width: 32 bits, Reset: 0x0000_0100
- Bit 0: TX_EMPTY (RO)
- Bit 8: READY (RO)

## DATA - Offset: 0x0008, Width: 8 bits, Reset: 0x00
- Bits 0-7: DATA_BYTE (RW)

## BAUD - Offset: 0x000C, Width: 16 bits, Reset: 0x0001
- Bits 0-15: DIVISOR (RW)