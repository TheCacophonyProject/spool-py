# Spool with electromagnet release

## Setup

- Finish soldering PCB
  - Photo interrupters
  - 8 Pin connector
  - Battery for RTC

- Power up PCB with 12V supply, power draw before programming should be less than 10mA
- Plug in USB cable, should see it come up on your computer as a storage device.
- Download the latest [micropython release](https://micropython.org/download/RPI_PICO/)
- Copy the `.uf2` to the RP2040
- After a few seconds you should see the storage device go away. It can now be programmed.
