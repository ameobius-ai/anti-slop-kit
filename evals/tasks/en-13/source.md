# UART0 Register Map

Base Address: 0x4000_C000

## Register 0: CTRL
- Offset: 0x0000
- Width: 32 bits
- Reset Value: 0x0000_0000
- Fields:
  - Bit 0: ENABLE (RW)
  - Bit 1: LOOPBACK (RW)
  - Bit 2: INT_ENABLE (RW)
  - Bits 3-7: Reserved (RO)

## Register 1: STATUS
- Offset: 0x0004
- Width: 32 bits
- Reset Value: 0x0000_0100
- Fields:
  - Bit 0: TX_EMPTY (RO)
  - Bit 1: RX_FULL (RO)
  - Bit 2: ERROR (RC)
  - Bit 8: READY (RO)

## Register 2: DATA
- Offset: 0x0008
- Width: 8 bits
- Reset Value: 0x00
- Fields:
  - Bits 0-7: DATA_BYTE (RW)

## Register 3: BAUD
- Offset: 0x000C
- Width: 16 bits
- Reset Value: 0x0001
- Fields:
  - Bits 0-15: DIVISOR (RW)