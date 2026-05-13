# spool-py

This is the micropython code to be run on a spool PCB.

## Uploading code

mpremote is required to use these helper scripts to upload the code to the PCB.

Use `./upload` to upload code to a spool.
The `--run-main` option will run `main.py` after uploading so you can see the output.

## Running and Testing code

Use `./run <src/file.py>` to upload all files and then run the target file.
The `--skip-update` option will skip the upload step and just run the file.

## Programs

There is a rotary switch on the PCB to select different programs.
Program 0 is a special case where from program 0 it can run any other program and also update the software of the trap.

### Program 0

With the rotary dial to 0 when the trap powers on it will try to connect to the camera over UART. If it fails to do so after 10 seconds it will run the default program.

If the trap does connect to the camera the camera can send commands over UART changing.

- [ ] Default program to run. This can be helpful so traps can be configured to run different programs without needing to open them up.
- [ ] Update time. The RTC on the trap will slowly drift so the camera can update the time.
- [ ] Camera can read logs from trap. The trap can make some minimal logs for tracking when the trap was triggered and such.
- [ ] Collect error logs.
- [ ] Update software. The camera can send new files over UART for the trap to run.
- [ ] Read list of files and the hash. This is so the camera can check that the trap has the correct files on it.
- [ ] Update trap configuration.

### Program 1

Program 1 is a basic PIR triggered trap.
It can be configured to only trigger at night or day and night.

### Program 2

Program 2 is a PIR triggered trap with a basic digital enable/disable on the RX pin. Enable being high and disable being low.

### Program 3

Program 3 is a PIR triggered trap with UART communications with the camera.

The camera can:

- [ ] Restart the trap.
- [ ] Enable/Disable through UART.
- [ ] Update the time of the RTC.


Set `PROGRAM` in `config.py` to select which program runs on boot via `main.py`.



| Program | File | Description |
| ------- | ---- | ----------- |
| 0 | `code00.py` | Debugging — listens for commands over UART (reset spool, trigger spool, read PIRs, read spool). |
| 1 | `code01.py` | PIR-triggered trap with a time-based active window from the RTC clock. |
| 2 | `code02.py` | PIR-triggered trap enabled/disabled by a high signal on the Rx pin. |
| 3 | `code03.py` | Same as program 2 but the enable signal is active-low. |
| 4 | `code04.py` | PIR or thermal (MLX90640) triggered trap with a time-based active window. Set `TRIGGER_SOURCE` in `config.py` to `"pir"` or `"thermal"`. |
| 5 | `code05.py` | LED indicator test — no spool triggering. `led1` lights on PIR motion, `led2` lights on thermal motion. Prints frame stats. |
| 6 | `code06.py` | MLX90640 SNR measurement tool. Collects a quiet baseline then prints per-frame signal-to-noise stats to help tune `MLX_THRESHOLD`. |
| 7 | `code07.py` | PIR audio test — buzzer plays different tones depending on which PIRs are active. |
| 8 | `code08.py` | Spool cycle test — repeatedly runs reset → release → home on a configurable interval. |
