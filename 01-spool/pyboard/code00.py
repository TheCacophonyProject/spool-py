# Program 0 is used for debugging

from util import Spool, PIRs
import time
pirs = PIRs()

while True:
    print("=========")
    print(pirs.pir_1.value())
    print(pirs.pir_2.value())
    time.sleep(0.5)