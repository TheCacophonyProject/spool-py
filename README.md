# spool-py

This is the micropython code to be run on a spool PCB.

## Uploading code

mpremote is required to use these helper scripts to upload the code to the PCB.

Use `upload <target-folder> --run-main` to upload code to a spool.
The `--run-main` option will run `main.py` after uploading the files so you can see the output.

## Running and Testing code

Use`run <target-folder/src/file.py> --skip-update`
This will update the code on the PCB and then run the target file.
