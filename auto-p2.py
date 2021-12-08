import sys
from subprocess import call

#!/usr/bin/python3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('auto-p2')

def prepare(nsw = 3):
    try:
        nsw=int(nsw)
        if(1>nsw or 5<nsw):
            print("El numero de servidores web tiene que estar entre 1 y 5")
            sys.exit()
    except:
        sys.exit()
    for i in range(0, nsw):
        call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-p2.qcow2" "s{}.qcow2".format(i)] )
        call(["cp", "plantilla-vm-p2.xml", "s{}.xml".format(i)])

