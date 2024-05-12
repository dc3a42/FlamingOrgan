import time, sys
import spidev


ledcount = 152

SPI_15600_KHz = 15600000
SPI_7800_KHz = 7800000
SPI_3900_KHz = 3900000 # About 500 updates per second
SPI_1953_KHz = 1953000
SPI_976_KHz = 976000


print('Initializing SPI bus')
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = SPI_3900_KHz
#spi.max_speed_hz = SPI_15600_KHz
spi.mode = 0b11

def init_led_array(chipcount = ledcount):
    print('Initializing array for %d leds' % chipcount)
    leds = [0 for a in range(chipcount * 4 + 8)]
    leds[chipcount * 4 + 4] = 0xFF
    leds[chipcount * 4 + 5] = 0xFF
    leds[chipcount * 4 + 6] = 0xFF
    leds[chipcount * 4 + 7] = 0xFF
    return leds

ledarray = init_led_array()

def writeled(ledoffset, redval, greenval, blueval, arr = ledarray):
    ''' Write one LED at offset ledoffset, value redval, greenval, blueval,
    into arr'''
    if (ledoffset < 0 or ledoffset >= ledcount):
        return
    arrayoffset = ledoffset * 4 + 4
    arr[arrayoffset] = 0xF8   # Per-chip brightness
    arr[arrayoffset+1] = blueval & 0xFF
    arr[arrayoffset+2] = redval & 0xFF
    arr[arrayoffset+3] = greenval & 0xFF

def set_all_leds(redval = 0, greenval = 0, blueval = 0, arr = ledarray):
    for ledoff in range(ledcount):
        writeled(ledoff, redval, greenval, blueval, arr)

def testleds(testdelay = 1):
    print('Testing LEDs: all Red, then Green, then Blue, then white')
    set_all_leds(0xFF,0,0)   # Should show Red
    spi.writebytes(ledarray)
    time.sleep(testdelay)
    set_all_leds(0,0xFF,0)   # Should show Green
    spi.writebytes(ledarray)
    time.sleep(testdelay)
    set_all_leds(0,0,0xFF)   # Should show Blue
    spi.writebytes(ledarray)
    time.sleep(testdelay)
    set_all_leds(0xFF,0xFF,0xFF)
    spi.writebytes(ledarray)
    time.sleep(testdelay * 3)
    set_all_leds(0,0,0)
    spi.writebytes(ledarray)

def write_seq(initoff = 0, len = 1, skip = 1):
    ''' Write a repeating sequence of white, starting at initoff,
    len long, then skip and repeat.'''
    set_all_leds()
    for seqoff in range(initoff, ledcount, len + skip):
        for ledoff in range(seqoff, min(ledcount, seqoff + len)):
            writeled(ledoff, 0xFF, 0xFF, 0xFF)
    spi.writebytes(ledarray)

def inchworm(offset):
    print('Inchworm ' + str(offset))
    head_pause = 0.5
    tail_pause = 1
    log_pause = 2
    write_seq(offset, 3, 6)
    time.sleep(head_pause)
    write_seq(offset, 4, 5)
    time.sleep(head_pause)
    write_seq(offset, 5, 4)
    time.sleep(head_pause)
    write_seq(offset, 6, 3)
    time.sleep(tail_pause)
    write_seq(offset + 3, 3, 6)
    time.sleep(tail_pause)

for iter in range(10):
    for offset in range(-3, 6, 3):
        inchworm(offset)
        time.sleep(1)
sys.exit(0)

def runleds(delay = 0.001):
    '''Run 1 led along strip'''
    set_all_leds(0x00, 0x00, 0x00)
    for offset in range(ledcount):
        writeled(offset, 0xFF, 0xFF, 0xFF)
        spi.writebytes(ledarray)
        if (delay > 0):
            time.sleep(delay)
        writeled(offset, 0, 0, 0)

print('Running 1 led along strip 100x')
for i in range(100):
    starttime = time.time()
    runleds(delay=0.0001)
    print('1 run in %.3f seconds' % (time.time() - starttime))    
sys.exit(0)

offarr = ledarray
set_all_leds(0x00, 0x00, 0x00, offarr)
onarr = init_led_array()
set_all_leds(0x00, 0x00, 0xFF, onarr)
spi.writebytes(offarr)
print('Flashing fast')
starttime = time.time()
for i in range(1000):
    spi.writebytes(onarr)
    time.sleep(0.001)
    spi.writebytes(offarr)
    time.sleep(0.001)
print('Done flashing 1000 times in %.3f seconds' % (time.time() - starttime))
