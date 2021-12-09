#!/usr/bin/python3

#Autores:
#Ignacio Sandoval Martinez-Illescas
#Pilar Petruzzella Rodriguez
#Laura Fernandez Galindo

import json
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

def prepareVM(num_serv = 3):
    print("entramos a prepare")
    if(num_serv < 1 or num_serv > 5):
        print('El numero de servidores web tiene que estar entre 1 y 5')
        raise ValueError("Tiene que crear entre 1 y 5 servidores web")#
   else:
        print("El numero de servidores es correcto")
        data = {}
        data['num_serv'] = num_serv
        with open("auto-p2.json",'w') as file:
            json.dump(data, file)
        print("El fichero json se ha creado")
        
        for i in range(1, num_serv+1):
            call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2", "s{}.qcow2".format(i)] )
            call(["cp", "plantilla-vm-pc1.xml", "s{}.xml".format(i)])
            creacionFicherosXML("s{}".format(i), lan2 )
            configuraciones("s{}".format(i))
            call(["sudo", "virsh", "define", "s{}.xml".format(i)])
            
        #creacion C1
        call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2" "c1.qcow2"] )
        call(["cp", "plantilla-vm-pc1.xml", "c1.xml"])
        creacionFicherosXML("c1", lan1)
        configuraciones("c1")
        call(["sudo", "virsh", "define", "c1.xml"])
        #creacion LB
        call(["qemu-image", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2" "lb.qcow2"] )
        call(["cp", "plantilla-vm-pc1.xml", "lb.xml"])
        creacionFicherosXML("lb", lan1)
        configuraciones("lb")
        call(["sudo", "virsh", "define", "lb.xml"])
        #creacionBridges
        createBridges()
        call(["HOME=/mnt/tmp", "sudo", "virt-manager"])
        #configuramos el Host
        call(["sudo", "ifconfig", "LAN1", "10.0.1.3/24"])
        call(["sudo", "ip", "route", "add", "10.0.0.0/16", "via", "10.0.1.1"])

#----------------------------------------------LAUNCH----------------------------------------------------------
#def launch():

      
#---------------------------------------FUNCIONES AUXILIARES---------------------------------------------------
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
    path = str(os.getcwd())
    root.find("./devices/disk/source").set("file", '{}/{}.qcow2'.format(path,nombre))
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


def configuraciones(name):
    #configuramos el archivo /etc/hostname
    f = open("/mnt/tmp/hostname", "w")
    f.write(name)
    f.close()
    call(["sudo", "virt-copy-in", "-a", "{}.qcow2".format(name), "hostname", "/etc"])

    #configuramos archivo /etc/hosts
    #call(["sudo", "virt-copy-out", "-a", "{}.qcow2", "/etc/hosts", "/mnt/tmp/hosts"])
    #hin = open("/mnt/tmp/hosts", "r")
    #hout = open("/mnt/tmp/hosts_mod", "w")
    #for line in hin:
        #if "127.0.1.1" in line:
            #hout.write("127.0.1.1 {} \n".format(name))
        #else:
            #hout.write(line)
    #for line in hout:
        #hin.write(line)
    #hin.close
    #hout.close
    #call(["sudo", "virt-copy-in", "-a", "{}.qcow2".format(name), "hosts", "/etc"])

    #configuramos el archivo /etc/network/interfaces
    if name == 'lb':
        i = """auto lo
        iface lo inet loopback

        auto eth0
        iface eth0 inet static
            address 10.0.1.1
            netmask 255.255.255.0

        auto eth1
        iface eth1 inet static
            address 10.0.2.1
            netmask 255.255.255.0 """
    elif name == 'c1':
        i = """
            auto lo
        iface lo inet loopback
        auto eth0
        iface eth0 inet static
            address 10.0.1.2
            netmask 255.255.255.0
            gateway 10.0.1.1
        """
    else:
        i="""auto lo
        iface lo inet loopback
        auto eth0
        iface eth0 inet static
            address 10.0.2.1{}
            netmask 255.255.255.0
            gateway 10.0.2.1
        """.format(name[1])
    k = open("/mnt/tmp/interfaces", "w")
    k.write(i)
    k.close()
    call(["sudo", "virt-copy-in", "-a", "{}.qcow2".format(name), "interfaces", "/etc/network"])
    #configuramos lb como router
    if name == "lb":
        os.system("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf \-e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'")
    #modificamos las paginas web iniciales
    if name[0]=="s":
        t = open("/mnt/tmp/index.html", "w")
        t.write("S{}".format(name[1]))
        t.close()
        call(["sudo", "virt-copy-in", "-a", "{}.qcow2".format(name), "index.html", "/var/www/html/index.html"])


if sys.argv[1] == "prepare":
    if len(sys.argv) == 2:
        prepareVM()
        print("HABRA TRES SERV POR DEFE CTO")
    else:
        numservi=int(sys.argv[2])
        prepareVM(numservi)
