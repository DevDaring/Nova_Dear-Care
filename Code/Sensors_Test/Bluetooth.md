Yes, you can use the TP‑Link UB500 with the RDK S100 and stream audio to your Bose speaker. Below is a **step‑by‑step “any‑tool‑can-follow” setup**, split into small, testable chunks.

***

## 0. Plug in and confirm the dongle is seen

1. Plug the TP‑Link UB500 into any USB‑A port on the RDK S100. [developer.d-robotics](https://developer.d-robotics.cc/rdk_doc/en/Quick_start/hardware_introduction/rdk_x5/)
2. In a terminal:

   ```bash
   lsusb | grep -i -e tp-link -e 2357:0604
   ```

   - You should see a line with `TP-Link UB500` or vendor ID `2357:0604` (Realtek RTL8761B). [forum.endeavouros](https://forum.endeavouros.com/t/tp-link-ub500-compatibility/56220)
   - If you see that, the USB layer is fine; continue.

***

## 1. Make sure the driver + firmware are OK

Modern kernels (≥5.16, esp. ≥6.8) usually support UB500 out of the box via the `btusb` driver plus Realtek firmware. [reddit](https://www.reddit.com/r/TpLink/comments/1ipxqvo/ub500_plus_chipset_compatibility_with_linux/)

1. Check kernel version:

   ```bash
   uname -r
   ```

2. Check if Bluetooth controller appears:

   ```bash
   hciconfig -a || bluetoothctl list
   ```

   - If you see something like `hci0: Type: Primary Bus: USB` or `Controller XX:XX:...` → driver is loaded; **skip to section 2**. [howtogeek](https://www.howtogeek.com/829360/how-to-set-up-bluetooth-on-linux/)
   - If **nothing** appears, install Realtek RTL8761B firmware (safe even if partly working):

     ```bash
     sudo apt update
     sudo apt install -y git curl build-essential dkms bc
     git clone https://github.com/TheSonicMaster/rtl8761b-fw-installer.git
     cd rtl8761b-fw-installer
     sudo bash rtl8761b-fw-installer.sh
     sudo systemctl restart bluetooth
     ```

     This scripts downloads `rtl8761b_fw.bin` / config into `/lib/firmware/rtl_bt/` so `btusb` can bring up the dongle. [github](https://github.com/orgs/home-assistant/discussions/1630)

3. Re‑check:

   ```bash
   hciconfig -a
   ```

   If you now see `hci0`, the dongle is ready.

***

## 2. Install Bluetooth stack and enable the service

Use BlueZ (official Linux Bluetooth stack) and ensure the daemon is running. [ubuntu-mate](https://ubuntu-mate.community/t/installing-bluetooth-dongle-and-its-software/28322)

```bash
sudo apt update
sudo apt install -y bluetooth bluez bluez-tools
```

Enable and start the service:

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo systemctl status bluetooth
```

If `status` shows “active (running)”, you’re good. [oneuptime](https://oneuptime.com/blog/post/2026-03-02-how-to-configure-bluetooth-audio-on-ubuntu/view)

Unblock if needed:

```bash
rfkill list
sudo rfkill unblock bluetooth
```

This clears soft/hard blocks so the adapter can transmit. [ubuntu-mate](https://ubuntu-mate.community/t/installing-bluetooth-dongle-and-its-software/28322)

***

## 3. Install audio stack for Bluetooth speakers

On Ubuntu‑style systems, either PulseAudio or PipeWire handles sound, both via the `pactl` interface. [reddit](https://www.reddit.com/r/linux_gaming/comments/ueq8ez/pipewire_bluetooth_support_status_update/)

Install audio components:

```bash
sudo apt install -y pulseaudio pulseaudio-utils pulseaudio-module-bluetooth pavucontrol
# If your image uses PipeWire (Ubuntu 22.04+), also:
sudo apt install -y pipewire-audio libspa-0.2-bluetooth
```

This adds the Bluetooth A2DP (high‑quality audio) modules. [juniyadi](https://www.juniyadi.id/blog/ubuntu-22-04-fix-bluetooth)

You can safely reboot here so Bluetooth + audio reload cleanly:

```bash
sudo reboot
```

***

## 4. Pair and connect the Bose speaker (bluetoothctl)

We’ll use a reproducible `bluetoothctl` script‑style sequence. [oneuptime](https://oneuptime.com/blog/post/2026-03-02-pair-bluetooth-devices-command-line-ubuntu/view)

1. After reboot, open a terminal and run:

   ```bash
   bluetoothctl
   ```

2. Inside the interactive prompt, run these commands exactly:

   ```text
   [bluetooth]# power on
   [bluetooth]# agent on
   [bluetooth]# default-agent
   [bluetooth]# scan on
   ```

3. Put your **Bose speaker in pairing mode** (LED flashing, as per Bose manual).  
4. In the `bluetoothctl` output, look for a line like:

   ```text
   [NEW] Device AA:BB:CC:DD:EE:FF Bose SoundLink XXX
   ```

   Note the MAC address `AA:BB:CC:DD:EE:FF` (yours will differ). [oneuptime](https://oneuptime.com/blog/post/2026-03-02-pair-bluetooth-devices-command-line-ubuntu/view)

5. Still inside `bluetoothctl`, pair, trust and connect:

   ```text
   [bluetooth]# pair AA:BB:CC:DD:EE:FF
   [bluetooth]# trust AA:BB:CC:DD:EE:FF
   [bluetooth]# connect AA:BB:CC:DD:EE:FF
   ```

   - If prompted to confirm, type `yes` or press Enter.  
   - `info AA:BB:CC:DD:EE:FF` should now show `Connected: yes` and A2DP / headset profiles. [oneuptime](https://oneuptime.com/blog/post/2026-03-02-how-to-configure-bluetooth-audio-on-ubuntu/view)

6. You can now exit:

   ```text
   [bluetooth]# quit
   ```

At this stage the Bose speaker is paired and connected, but might not yet be the default audio output.

***

## 5. Make Bose the default audio output (A2DP)

1. Ensure the card is using the A2DP (high‑quality) profile:

   ```bash
   pactl list cards | grep -A 20 bluez_card
   ```

   - Find the line with `bluez_card.AA_BB_CC_DD_EE_FF` (your MAC with underscores). [oneuptime](https://oneuptime.com/blog/post/2026-03-02-how-to-configure-bluetooth-audio-on-ubuntu/view)
   - Then:

     ```bash
     pactl set-card-profile bluez_card.AA_BB_CC_DD_EE_FF a2dp_sink
     ```

     This forces high‑quality A2DP playback mode. [juniyadi](https://www.juniyadi.id/blog/ubuntu-22-04-fix-bluetooth)

2. Set the Bose speaker as default sink:

   ```bash
   pactl list short sinks
   ```

   Look for a sink like:

   ```text
   bluez_sink.AA_BB_CC_DD_EE_FF.a2dp_sink
   ```

   Then:

   ```bash
   pactl set-default-sink bluez_sink.AA_BB_CC_DD_EE_FF.a2dp_sink
   ```

   Any new audio (YouTube, `aplay`, `vlc`, etc.) should now go to the Bose speaker. [oneuptime](https://oneuptime.com/blog/post/2026-03-02-pair-bluetooth-devices-command-line-ubuntu/view)

3. (Optional GUI check) Run:

   ```bash
   pavucontrol
   ```

   and verify the **Output Device** shows the Bose speaker and the profile is A2DP. [juniyadi](https://www.juniyadi.id/blog/ubuntu-22-04-fix-bluetooth)

***

## 6. Make this “AI‑safe” for future automation

If you want other tools/agents to be able to re‑run or repair this setup without thinking, you can define a simple shell script template:

```bash
# file: setup_bluetooth_bose.sh

BT_MAC="AA:BB:CC:DD:EE:FF"   # replace with your Bose address

sudo apt update
sudo apt install -y bluetooth bluez bluez-tools \
    pulseaudio pulseaudio-utils pulseaudio-module-bluetooth pavucontrol \
    pipewire-audio libspa-0.2-bluetooth

sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo rfkill unblock bluetooth

# Pairing and trusting could still be done once manually via bluetoothctl,
# but reconnect + audio routing can be automated:
pactl set-card-profile "bluez_card.${BT_MAC//:/_}" a2dp_sink
pactl set-default-sink "bluez_sink.${BT_MAC//:/_}.a2dp_sink"
```

- Any “dumb” AI tool just has to:  
  1. Ensure `BT_MAC` is set correctly.  
  2. Run the script (plus `bluetoothctl` pairing once if needed).  
- All low‑level things (driver, service, A2DP profile, default sink) are encoded in commands that are stable across Ubuntu‑like systems. [howtogeek](https://www.howtogeek.com/829360/how-to-set-up-bluetooth-on-linux/)

***

If you paste the output of `hciconfig -a` and `bluetoothctl list`, I can double‑check that the UB500 is fully up before you attempt pairing with the Bose.