# Inventário de ambiente — fabio-desktop

- **Data/hora (UTC):** 2026-08-25T22:25:51Z
- **Data/hora (local):** 2026-08-25T19:25:51-0300
- **Usuário:** fabio
- **Script:** `./inventario-ambiente.sh`
- **Propósito:** Sprint 0, item "caderno de campo" — estado do ambiente antes do bring-up.

## Sistema operacional e kernel

**Kernel** — `uname -a`

```
Linux fabio-desktop 7.0.0-30-generic #30~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Fri Aug  7 13:27:52 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```

**Distribuição** — `cat /etc/os-release`

```
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.4 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
LOGO=ubuntu-logo
```

**lsb_release** — `lsb_release -a`

```
Distributor ID:	Ubuntu
Description:	Ubuntu 24.04.4 LTS
Release:	24.04
Codename:	noble
```

**Point release** — `cat /etc/lsb-release 2>/dev/null; cat /var/log/installer/media-info 2>/dev/null`

```
DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=24.04
DISTRIB_CODENAME=noble
DISTRIB_DESCRIPTION="Ubuntu 24.04.4 LTS"
Ubuntu 24.04.4 LTS "Noble Numbat" - Release amd64 (20260210)```

**Uptime** — `uptime`

```
 19:25:51 up 24 min,  1 user,  load average: 0.18, 0.34, 0.26
```


## CPU, memória e disco

**CPU** — `lscpu | head -30`

```
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           48 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  16
On-line CPU(s) list:                     0-15
Vendor ID:                               AuthenticAMD
Model name:                              AMD Ryzen 7 5700X 8-Core Processor
CPU family:                              25
Model:                                   33
Thread(s) per core:                      2
Core(s) per socket:                      8
Socket(s):                               1
Stepping:                                2
Frequency boost:                         enabled
CPU(s) scaling MHz:                      75%
CPU max MHz:                             4665.8350
CPU min MHz:                             562.1490
BogoMIPS:                                6799.77
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 x2apic movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local user_shstk clzero irperf xsaveerptr rdpru wbnoinvd arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif v_spec_ctrl umip pku ospke vaes vpclmulqdq rdpid overflow_recov succor smca fsrm debug_swap
Virtualization:                          AMD-V
L1d cache:                               256 KiB (8 instances)
L1i cache:                               256 KiB (8 instances)
L2 cache:                                4 MiB (8 instances)
L3 cache:                                32 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-15
Vulnerability Gather data sampling:      Not affected
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Not affected
```

**Memória** — `free -h; echo; grep -E "MemTotal|SwapTotal" /proc/meminfo`

```
               total        used        free      shared  buff/cache   available
Mem:            15Gi       4.5Gi       5.3Gi       105Mi       5.6Gi        11Gi
Swap:          4.0Gi          0B       4.0Gi

MemTotal:       16292660 kB
SwapTotal:       4194300 kB
```

**Disco** — `df -h / /home "$HOME" 2>/dev/null | sort -u`

```
/dev/nvme1n1p3  143G   13G  122G  10% /
Filesystem      Size  Used Avail Use% Mounted on
```

**Espaço livre em $HOME** — `du -sh "$HOME" 2>/dev/null | tail -1; df -h "$HOME" | tail -1`

```
893M	/home/fabio
/dev/nvme1n1p3  143G   13G  122G  10% /
```


## GPU: hardware e driver de kernel

**PCI (VGA/Display)** — `lspci -nn | grep -Ei "vga|display|3d"`

```
2d:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Device [1002:7550] (rev c0)
```

**PCI detalhado (link width/speed)** — `lspci -vv 2>/dev/null | grep -A3 -Ei "vga|display" | grep -Ei "vga|display|lnksta|lnkcap" || echo "[requer root para LnkSta]"`

```
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr+ Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O+ Mem+ BusMaster+ SpecCycle+ MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	BridgeCtl: Parity- SERR+ NoISA- VGA- VGA16+ MAbort- >Reset- FastB2B-
2d:00.0 VGA compatible controller: Advanced Micro Devices, Inc. [AMD/ATI] Device 7550 (rev c0) (prog-if 00 [VGA controller])
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem- BusMaster- SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
	Control: I/O- Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx+
```

**Módulo amdgpu carregado** — `lsmod`

```
Module                  Size  Used by
ccm                    20480  6
rfcomm                102400  4
snd_seq_dummy          12288  0
snd_hrtimer            12288  1
qrtr                   53248  2
cmac                   12288  3
algif_hash             20480  1
algif_skcipher         12288  1
af_alg                 32768  6 algif_hash,algif_skcipher
bnep                   32768  2
binfmt_misc            24576  1
nls_iso8859_1          12288  1
snd_hda_codec_alc662    20480  1
snd_hda_codec_realtek_lib    65536  1 snd_hda_codec_alc662
amdgpu              21188608  22
snd_hda_codec_atihdmi    24576  1
snd_hda_codec_generic   122880  2 snd_hda_codec_alc662,snd_hda_codec_realtek_lib
snd_hda_codec_hdmi     65536  1 snd_hda_codec_atihdmi
snd_hda_intel          61440  2
snd_hda_codec         204800  6 snd_hda_codec_generic,snd_hda_codec_hdmi,snd_hda_intel,snd_hda_codec_alc662,snd_hda_codec_realtek_lib,snd_hda_codec_atihdmi
amdxcp                 12288  1 amdgpu
amd_atl                77824  1
intel_rapl_msr         20480  0
drm_panel_backlight_quirks    12288  1 amdgpu
mt7921e                24576  0
snd_hda_core          151552  7 snd_hda_codec_generic,snd_hda_codec_hdmi,snd_hda_intel,snd_hda_codec_alc662,snd_hda_codec,snd_hda_codec_realtek_lib,snd_hda_codec_atihdmi
intel_rapl_common      57344  1 intel_rapl_msr
snd_usb_audio         589824  2
gpu_sched              69632  1 amdgpu
snd_intel_dspcfg       45056  1 snd_hda_intel
mt7921_common          94208  1 mt7921e
snd_usbmidi_lib        57344  1 snd_usb_audio
snd_intel_sdw_acpi     16384  1 snd_intel_dspcfg
drm_buddy              28672  1 amdgpu
mt792x_lib             73728  2 mt7921e,mt7921_common
btusb                  81920  0
snd_hwdep              24576  2 snd_usb_audio,snd_hda_codec
drm_ttm_helper         20480  1 amdgpu
snd_ump                49152  1 snd_usb_audio
mt76_connac_lib       110592  3 mt792x_lib,mt7921e,mt7921_common
btmtk                  36864  1 btusb
snd_seq_midi           24576  0
ttm                   131072  2 amdgpu,drm_ttm_helper
mt76                  167936  4 mt792x_lib,mt7921e,mt7921_common,mt76_connac_lib
btrtl                  32768  1 btusb
snd_seq_midi_event     16384  1 snd_seq_midi
drm_exec               12288  1 amdgpu
snd_seq               126976  9 snd_seq_midi,snd_seq_midi_event,snd_seq_dummy
snd_rawmidi            57344  3 snd_seq_midi,snd_usbmidi_lib,snd_ump
edac_mce_amd           28672  0
btbcm                  24576  1 btusb
drm_suballoc_helper    24576  1 amdgpu
mac80211             1892352  4 mt792x_lib,mt76,mt7921_common,mt76_connac_lib
drm_display_helper    299008  1 amdgpu
snd_pcm               204800  6 snd_hda_codec_hdmi,snd_hda_intel,snd_usb_audio,snd_hda_codec,snd_hda_core
kvm_amd               253952  0
btintel                69632  1 btusb
snd_seq_device         16384  4 snd_seq,snd_seq_midi,snd_ump,snd_rawmidi
bluetooth            1077248  34 btrtl,btmtk,btintel,btbcm,bnep,btusb,rfcomm
cec                    98304  2 drm_display_helper,amdgpu
ee1004                 16384  0
joydev                 32768  0
input_leds             12288  0
snd_timer              53248  3 snd_seq,snd_hrtimer,snd_pcm
kvm                  1507328  1 kvm_amd
mc                     90112  1 snd_usb_audio
cfg80211             1511424  4 mt76,mac80211,mt7921_common,mt76_connac_lib
rc_core                73728  1 cec
snd                   143360  23 snd_hda_codec_generic,snd_seq,snd_seq_device,snd_hda_codec_hdmi,snd_hwdep,snd_hda_intel,snd_usb_audio,snd_usbmidi_lib,snd_hda_codec,snd_timer,snd_hda_codec_realtek_lib,snd_ump,snd_pcm,snd_rawmidi
i2c_algo_bit           16384  1 amdgpu
video                  77824  1 amdgpu
irqbypass              16384  1 kvm
soundcore              16384  1 snd
libarc4                12288  1 mac80211
i2c_piix4              32768  0
ccp                   188416  1 kvm_amd
k10temp                16384  0
i2c_smbus              20480  1 i2c_piix4
ghash_clmulni_intel    12288  0
wmi_bmof               12288  0
aesni_intel            98304  3
mac_hid                12288  0
gpio_amdpt             16384  0
rapl                   20480  0
sch_fq_codel           28672  2
msr                    12288  0
parport_pc             53248  0
ppdev                  24576  0
lp                     32768  0
parport                73728  3 parport_pc,lp,ppdev
efi_pstore             12288  0
nfnetlink              20480  1
dmi_sysfs              24576  0
ip_tables              32768  0
x_tables               65536  1 ip_tables
autofs4                57344  2
hid_logitech_hidpp     69632  0
hid_logitech_dj        36864  0
nvme                   65536  2
hid_generic            12288  0
nvme_core             237568  3 nvme
usbhid                 77824  2 hid_logitech_dj,hid_logitech_hidpp
hid                   282624  4 usbhid,hid_generic,hid_logitech_dj,hid_logitech_hidpp
nvme_keyring           20480  1 nvme_core
r8169                 147456  0
ahci                   49152  0
nvme_auth              28672  1 nvme_core
realtek                57344  1
libahci                53248  1 ahci
hkdf                   12288  1 nvme_auth
wmi                    36864  2 video,wmi_bmof
```

**amdgpu (filtrado)** — `lsmod | grep -E "^amdgpu|^amdkfd|^amdttm" || echo "[amdgpu NAO carregado]"`

```
amdgpu              21188608  22
```

**Versão do módulo amdgpu** — `modinfo amdgpu 2>/dev/null | grep -E "^(filename|version|srcversion|vermagic):" || echo "[modinfo amdgpu falhou]"`

```
filename:       /lib/modules/7.0.0-30-generic/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko.zst
srcversion:     3C579E7F273939F4A3F71D3
vermagic:       7.0.0-30-generic SMP preempt mod_unload modversions 
```

**DKMS (amdgpu-pro instalado?)** — `dkms status 2>/dev/null || echo "[dkms ausente — provavelmente amdgpu in-kernel]"`

```
[dkms ausente — provavelmente amdgpu in-kernel]
```

**dmesg amdgpu** — `dmesg 2>/dev/null | grep -i amdgpu | tail -40 || journalctl -k 2>/dev/null | grep -i amdgpu | tail -40 || echo "[sem acesso a dmesg/journalctl sem root]"`

```
```

**Firmware carregado** — `dmesg 2>/dev/null | grep -iE "amdgpu.*(firmware|fw|vbios|ip block)" | tail -30 || echo "[indisponivel]"`

```
```


## Permissões de acesso à GPU

**Grupos do usuário** — `id`

```
uid=1000(fabio) gid=1000(fabio) groups=1000(fabio),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),114(lpadmin)
```

**Grupos render/video** — `id -nG | tr " " "\n" | grep -E "^(render|video)$" || echo "[AVISO: usuário NAO esta em render e/ou video — ROCm vai falhar]"`

```
[AVISO: usuário NAO esta em render e/ou video — ROCm vai falhar]
```

**Nós de dispositivo** — `ls -l /dev/kfd /dev/dri/ 2>&1`

```
crw-rw---- 1 root render 511, 0 Aug 25 19:07 /dev/kfd

/dev/dri/:
total 0
drwxr-xr-x  2 root root         80 Aug 25 16:01 by-path
crw-rw----+ 1 root video  226,   1 Aug 25 19:07 card1
crw-rw----+ 1 root render 226, 128 Aug 25 19:07 renderD128
```


## ROCm: instalação e versão

**ROCm presente?** — `ls -d /opt/rocm* 2>/dev/null || echo "[/opt/rocm NAO existe — ROCm nao instalado]"`

```
[/opt/rocm NAO existe — ROCm nao instalado]
```

**Versão ROCm** — `cat /opt/rocm/.info/version 2>/dev/null; cat /opt/rocm/.info/version-dev 2>/dev/null; echo "---"; ls /opt/rocm/.info/ 2>/dev/null`

```
---
```

**hipconfig** — `hipconfig --version`

```
[AUSENTE: comando "hipconfig" não encontrado no PATH]
```

**hipconfig full** — `hipconfig 2>&1 | head -40`

```
./inventario-ambiente.sh: line 50: hipconfig: command not found
```

**rocm-smi versão** — `rocm-smi --version`

```
[AUSENTE: comando "rocm-smi" não encontrado no PATH]
```

**Pacotes ROCm (dpkg)** — `dpkg -l 2>/dev/null | grep -iE "rocm|hip|miopen|rocblas|rccl|rocwmma|hsa" | awk "{print \$2, \$3}" || echo "[dpkg indisponivel]"`

```
libflashrom1:amd64 1.3.0-2.1ubuntu2
whiptail 0.52.24-2ubuntu2
```

**Repositório APT AMD** — `grep -rIh "repo.radeon.com" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null || echo "[nenhum repo AMD em sources.list]"`

```
[nenhum repo AMD em sources.list]
```


## ROCm: a GPU é enxergada como gfx1201?

**rocminfo (agentes)** — `rocminfo 2>&1 | grep -E "Name:|Marketing Name:|gfx|Compute Unit|Wavefront|Device Type" | head -40 || echo "[rocminfo falhou ou ausente]"`

```
```

**Alvo gfx detectado** — `rocminfo 2>/dev/null | grep -oE "gfx[0-9a-f]+" | sort -u || echo "[nenhum alvo gfx detectado]"`

```
```

**rocm-smi (visão geral)** — `rocm-smi`

```
[AUSENTE: comando "rocm-smi" não encontrado no PATH]
```

**rocm-smi --showhw** — `rocm-smi --showhw 2>&1`

```
./inventario-ambiente.sh: line 50: rocm-smi: command not found
```

**clinfo (OpenCL)** — `clinfo 2>&1 | grep -E "Device Name|Device Version|Driver Version|Max compute units" | head -20 || echo "[clinfo ausente]"`

```
```


## ROCm: instrumentação de potência (gate da hipótese H3)

**showpower** — `rocm-smi --showpower 2>&1`

```
./inventario-ambiente.sh: line 50: rocm-smi: command not found
```

**showpower --json** — `rocm-smi --showpower --json 2>&1`

```
./inventario-ambiente.sh: line 50: rocm-smi: command not found
```

**showtemp** — `rocm-smi --showtemp 2>&1`

```
./inventario-ambiente.sh: line 50: rocm-smi: command not found
```

**showpower+temp+clocks (--showallinfo é verboso; recorte)** — `rocm-smi --showpower --showtemp --showclocks 2>&1`

```
./inventario-ambiente.sh: line 50: rocm-smi: command not found
```


### Amostragem em idle (10 leituras, ~1 s de intervalo)

Se as 10 leituras forem idênticas e "redondas" (ex.: sempre 0.0W), suspeitar de sensor não implementado.

```
[AUSENTE: rocm-smi]
```

**Sensores via sysfs (fallback se rocm-smi falhar)** — `for f in /sys/class/drm/card*/device/hwmon/hwmon*/power*_average /sys/class/drm/card*/device/hwmon/hwmon*/power*_input; do [ -e "$f" ] && echo "$f = $(cat "$f" 2>/dev/null)"; done || echo "[sem power em hwmon]"`

```
/sys/class/drm/card1/device/hwmon/hwmon4/power1_average = 9000000
[sem power em hwmon]
```

**hwmon disponível** — `ls /sys/class/drm/card*/device/hwmon/hwmon*/ 2>/dev/null | sort -u | head -40 || echo "[sem hwmon]"`

```
device
fan1_enable
fan1_input
fan1_max
fan1_min
fan1_target
freq1_input
freq1_label
freq2_input
freq2_label
in0_input
in0_label
name
power
power1_average
power1_cap
power1_cap_default
power1_cap_max
power1_cap_min
power1_label
pwm1
pwm1_max
pwm1_min
subsystem
temp1_crit
temp1_crit_hyst
temp1_emergency
temp1_input
temp1_label
temp2_crit
temp2_crit_hyst
temp2_emergency
temp2_input
temp2_label
temp3_crit
temp3_crit_hyst
temp3_emergency
temp3_input
temp3_label
uevent
```


## Vulkan (rota do VkSplat — independente do ROCm)

**vulkaninfo --summary** — `vulkaninfo --summary`

```
[AUSENTE: comando "vulkaninfo" não encontrado no PATH]
```

**Driver Vulkan (RADV vs AMDVLK)** — `vulkaninfo 2>/dev/null | grep -iE "driverName|driverInfo|driverID|deviceName|apiVersion" | sort -u | head -20 || echo "[vulkaninfo falhou]"`

```
```

**ICDs Vulkan instalados** — `ls -1 /usr/share/vulkan/icd.d/ /etc/vulkan/icd.d/ 2>/dev/null || echo "[sem ICDs]"`

```
/etc/vulkan/icd.d/:

/usr/share/vulkan/icd.d/:
asahi_icd.json
gfxstream_vk_icd.json
intel_hasvk_icd.json
intel_icd.json
lvp_icd.json
nouveau_icd.json
radeon_icd.json
virtio_icd.json
```

**Pacotes Vulkan/Mesa** — `dpkg -l 2>/dev/null | grep -iE "vulkan|mesa|libdrm|radv|amdvlk" | awk "{print \$2, \$3}" || echo "[dpkg indisponivel]"`

```
libdrm-amdgpu1:amd64 2.4.125-1ubuntu0.1~24.04.2
libdrm-common 2.4.125-1ubuntu0.1~24.04.2
libdrm-intel1:amd64 2.4.125-1ubuntu0.1~24.04.2
libdrm-nouveau2:amd64 2.4.125-1ubuntu0.1~24.04.2
libdrm-radeon1:amd64 2.4.125-1ubuntu0.1~24.04.2
libdrm2:amd64 2.4.125-1ubuntu0.1~24.04.2
libegl-mesa0:amd64 25.2.8-0ubuntu0.24.04.2
libgl1-mesa-dri:amd64 25.2.8-0ubuntu0.24.04.2
libglu1-mesa:amd64 9.0.2-1.1build1
libglx-mesa0:amd64 25.2.8-0ubuntu0.24.04.2
libvulkan1:amd64 1.3.275.0-1build1
mesa-libgallium:amd64 25.2.8-0ubuntu0.24.04.2
mesa-va-drivers:amd64 25.2.8-0ubuntu0.24.04.2
mesa-vdpau-drivers:amd64 25.2.8-0ubuntu0.24.04.2
mesa-vulkan-drivers:amd64 25.2.8-0ubuntu0.24.04.2
```


### Extensões relevantes para matmul em Vulkan

VK_KHR_cooperative_matrix é a exposição, em Vulkan, das unidades matriciais (WMMA em RDNA).
Presença/ausência aqui é dado direto para a discussão Tensor Core vs WMMA (Cap. 3/5).

**cooperative_matrix / subgroup / FP16** — `vulkaninfo 2>/dev/null | grep -iE "cooperative_matrix|VK_KHR_shader_float16|subgroupSize|shaderFloat16|VK_KHR_16bit_storage|VK_EXT_subgroup" | sort -u | head -30 || echo "[vulkaninfo falhou]"`

```
```

**Filas de compute** — `vulkaninfo 2>/dev/null | grep -iE "queueFlags|queueCount" | head -20 || echo "[indisponivel]"`

```
```

**Compilador de shaders** — `for c in glslc glslangValidator spirv-val shaderc; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done`

```
glslc: [ausente]
glslangValidator: [ausente]
spirv-val: [ausente]
shaderc: [ausente]
```


## Python, PyTorch e Taichi

**Pythons disponíveis** — `for p in python3 python3.10 python3.11 python3.12 python3.13; do printf "%s: " "$p"; command -v "$p" >/dev/null 2>&1 && "$p" --version 2>&1 || echo "[ausente]"; done`

```
python3: Python 3.12.3
python3.10: [ausente]
python3.11: [ausente]
python3.12: Python 3.12.3
python3.13: [ausente]
```

**pip** — `python3 -m pip --version`

```
/usr/bin/python3: No module named pip

[exit code: 1]
```

**venv/conda ativo?** — `echo "VIRTUAL_ENV=${VIRTUAL_ENV:-<nenhum>}"; echo "CONDA_PREFIX=${CONDA_PREFIX:-<nenhum>}"; command -v conda >/dev/null 2>&1 && conda --version || echo "conda: [ausente]"`

```
VIRTUAL_ENV=<nenhum>
CONDA_PREFIX=<nenhum>
conda: [ausente]
```


### PyTorch — build e visibilidade da GPU

```
[AUSENTE] PyTorch nao importavel: No module named 'torch'
```


### Taichi — backends detectados

```
[AUSENTE] Taichi nao importavel: No module named 'taichi'
```

**Pacotes Python relevantes** — `python3 -m pip list 2>/dev/null | grep -iE "torch|taichi|nerfstudio|gsplat|numpy|opencv|plyfile|tinycudann|colmap|lpips|scikit-image" || echo "[pip list falhou ou nada relevante]"`

```
[pip list falhou ou nada relevante]
```


## Toolchain de build

**Compiladores** — `for c in gcc g++ clang clang++ hipcc amdclang++; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done`

```
gcc: [ausente]
g++: [ausente]
clang: [ausente]
clang++: [ausente]
hipcc: [ausente]
amdclang++: [ausente]
```

**Build tools** — `for c in cmake ninja make git pkg-config; do printf "%s: " "$c"; command -v "$c" >/dev/null 2>&1 && "$c" --version 2>&1 | head -1 || echo "[ausente]"; done`

```
cmake: [ausente]
ninja: [ausente]
make: [ausente]
git: git version 2.43.0
pkg-config: [ausente]
```

**COLMAP (SfM para datasets próprios)** — `command -v colmap >/dev/null 2>&1 && colmap --help 2>&1 | head -3 || echo "[ausente — necessario apenas para cenas proprias]"`

```
[ausente — necessario apenas para cenas proprias]
```

**ffmpeg** — `command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version 2>&1 | head -1 || echo "[ausente]"`

```
[ausente]
```


## Rede e contexto

**Hostname / IPs** — `hostname -f 2>/dev/null; ip -brief addr 2>/dev/null | grep -v "^lo" || ifconfig 2>/dev/null | head -20`

```
fabio-desktop
enp42s0          DOWN           
wlo1             UP             192.168.0.13/24 2804:14c:de51:810a:bde9:176d:1eeb:f485/64 2804:14c:de51:810a:42c6:73a0:6cae:9777/64 fe80::f849:cc1f:9e4e:8d28/64 
```

**Tailscale** — `command -v tailscale >/dev/null 2>&1 && tailscale status 2>&1 | head -10 || echo "[tailscale ausente]"`

```
[tailscale ausente]
```

**Docker (opcional, p/ fixar ambiente)** — `command -v docker >/dev/null 2>&1 && docker --version && docker info 2>/dev/null | grep -iE "server version|storage driver" || echo "[docker ausente]"`

```
[docker ausente]
```


## Resumo automático (checklist de gates do Sprint 0)

| Gate | Resultado |
|---|---|
| ROCm enxerga gfx1201 (RDNA 4) | NAO — rocminfo falhou/ausente |
| rocm-smi reporta potência numérica (gate H3) | NAO / indeterminado — acionar plano B (wattímetro) |
| PyTorch vê a GPU (gate 3DGS-HIP + baseline) | NAO |
| Vulkan operacional (gate VkSplat — desenho 2x2) | NAO |
| VK_KHR_cooperative_matrix (WMMA via Vulkan) | NAO / nao detectado |
| Usuário em render+video | NAO — corrigir antes de qualquer teste ROCm |

---

_Gerado por `inventario-ambiente.sh` em 2026-08-25T22:25:51Z._
