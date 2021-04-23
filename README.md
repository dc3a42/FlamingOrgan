# FlamingOrgan

Code to drive the Flaming Organ

Setup on a Raspberry Pi; I used a Pi 4
1. Set up your network access of choice
2. apt-get install alsa soundlib_dev emacs
3. Configure bluetooth keyboard using 'bluetoothctl'
4. info *MAC-adress*
5. trust *MAC-adress*
6. pair *MAC-adress*
7. connect *MAC-adress*

For a BT keyboard that won't connect, see https://www.raspberrypi.org/forums/viewtopic.php?p=947185#p947185

There's probably more -- let me know what I missed!  (Like Python3 support?  mido?)
