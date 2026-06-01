# spool-py

This is the micropython code to be run on a spool PCB.

## Uploading code

mpremote is required to use these helper scripts to upload the code to the PCB.

Use `./upload` to upload code to a spool.

## Running and Testing code

Use `./run <src/file.py>` to upload all files and then run the target file.
The `--skip-update` option will skip the upload step and just run the file.

## Programs

There is a rotary switch on the PCB to select different programs.

If the program uses the UART then it can commands can be sent though UART to update the software/time and other such commands.

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
