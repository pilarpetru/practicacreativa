#Autores:
#Ignacio Sandoval Martinez-Illescas
#Pilar Petruzzella Rodriguez
#Laura Fernandez Galindo

#!/usr/bin/python3
import os
import logging
from os import close
import sys
from subprocess import call
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('auto-p2')
from lxml import etree

#Creacion Variables globales
lan1 = "10.10.1.0/24"
lan2 = "10.10.2.0/24"

def prepare(num_serv = 3):
    try:
        nsw=int(num_serv)
        if(num_serv<1 or num_serv>5):
            logger.debug('El numero de servidores web tiene que estar entre 1 y 5')
            raise ValueError("Tiene que crear entre 1 y 5 servidores web")#
        else:
            p= open("auto-p2.json", "p")
            p.write("auto-p2.json={} \n".format(num_serv))
            p=close()

            #filePath=os.path.join('/mnt/tmp', 'hostname')


            for i in range(1, num_serv+1):
                 
                call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2" "s{}.qcow2".format(i)] )
                call(["cp", "plantilla-vm-pc1.xml", "s{}.xml".format(i)])
                creacionFicherosXML("s{}".format(i), lan2 )
                call(["sudo", "virsh", "define", "s{}.xml".format(i)])
            
            #creacion C1
            call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2" "c1.qcow2"] )
            call(["cp", "plantilla-vm-pc1.xml", "c1.xml"])
            creacionFicherosXML("c1", lan1)
            call(["sudo", "virsh", "define", "c1.xml"])
            #creacion LB
            call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2" "lb.qcow2"] )
            call(["cp", "plantilla-vm-pc1.xml", "lb.xml"])
            creacionFicherosXML("lb", lan1)
            call(["sudo", "virsh", "define", "lb.xml"])
            #creacionBridges
            createBridges()
            call(["HOME=/mnt/tmp", "sudo", "virt-manager"])
            

    except:
        logger.debug('Debe introducir un numero entero')
        sys.exit()

    
      
    
def creacionFicherosXML(nombre, lan):
    fichero = '{}.xml'.format(nombre)
    #cargamos ficheros XML que dice el enunciado
    tree = etree.parse(fichero)
    #obtenemos el nodo raiz
    root = tree.getroot()
    #buscamos la etiqueta nombre
    name = root.find("name")
    name.text = "{}".format(nombre)
    #buscamos y cambiamos el atributo file del fichero XML en la etiqueta device/disk/source
    root.find("./devices/disk/source").set("file", os.path + '/' + nombre + '.qcow2')
    if nombre!="lb":
        #buscamos y cambiamos el atributo bridge del fichero XML en la etiqueta device/interface/source
        root.find("./devices/interface/source").set("bridge", lan)
    else:
        #para asegurarnos que hacemos bridge con lan1 y lan2, nos olvidamos del parametro lan
        root.find("./devices/interface/source").set("bridge", lan1)
        #anadir source y model a la interfaz duplicada
        interfaceDuplicada = etree.Element("interface", type = "bridge")
        interfaceDuplicada.append(etree.Element("source", bridge = lan2))
        interfaceDuplicada.append(etree.Element("model", type = "virtio"))
        #anadir interfaz duplicada a devices
        dev = root.find("devices")
        dev.append(interfaceDuplicada)
    p = open(fichero, "w")
    p.write(etree.tounicode(tree, pretty_print=True))
    p.close()

def createBridges():
    call(["sudo", "brctl", "addbr", lan1])
    call(["sudo", "brctl", "addbr", lan2])
    call(["sudo", "ifconfig", lan1, "up"])
    call(["sudo", "ifconfig", lan2, "up"])    


logger.debug('mensaje debug1')
logger.debug('mensaje debug2')
