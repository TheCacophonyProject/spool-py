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

With the rotary dial to 0 when the trap powers on it will try to connect to the camera over UART. If it fails to do so after 10 seconds it will run the default program set in the configuration.

If the trap does connect to the camera the camera can send commands over UART changing:

- [ ] Default program to run. This can be helpful so traps can be configured to run different programs without needing to open them up.
- [ ] Update time. The RTC on the trap will slowly drift so the camera can update the time on the RTC.
- [ ] Camera can read logs from trap. The trap can make some minimal logs for tracking when the trap was triggered and such.
- [ ] Collect error logs.
- [ ] Update software. The camera can send new files over UART for the trap to run.
- [ ] Read list of files and the hash. This is so the camera can check that the trap has the correct files on it.
- [ ] Update trap configuration.
- [ ] Trigger resets/triggers of the trap.
- [ ] Read state of sensors on the trap.

### Program 1

Program 1 is a basic PIR triggered trap.
It can be configured to only trigger at night or day and night.
Can connect to the camera through UART to notify when the trap triggered.

### Program 2

Program 2 is a PIR triggered trap with a basic digital enable/disable on the RX pin. Enable being high and disable being low.

### Program 3

Program 3 is a PIR triggered trap with UART communications with the camera.

The camera can:

- [ ] Restart the trap.
- [ ] Enable/Disable through UART.
- [ ] Update the time of the RTC.

### Program 8

Program 8 is a test program, will communicate with the trap over UART for logging purposes.

## Events

When the trap communicates with the camera it can send though messages that the camera will turn into events. These are:

- trapMotion: Each time the trap detects motion it will report this, limited to one every 30 seconds. This is intended to help with seeing how the trap might be over/under triggering.
- trapEnabled: The trap was disabled but it is now enabled.
- trapDisabled: The trap is disabled, a new message will be sent every time the disabled reason changes
- trapEnableCommand: The trap has had a message from the camera that it can be enable. Note that the trap might still be disabled for other reasons (daytime, cage switch)
- trapDisableCommand: The trap has had a message from the camera to disable it.
- trapError: This catches a couple different types of errors.
  - error-code: An recognised error has happened. This will also make the trap beep.
  - runtime-error: An python runtime error occurred.
- trapTriggered: The trap has just triggered.
- trapSpoolReset: The spool on the trap was reset
- trapRunning: The program that is running on the trap.
