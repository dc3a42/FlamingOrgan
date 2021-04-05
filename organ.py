from smbus2 import SMBus
import sys, time
import getch
import mido


# Relay board DIP switch
# ON = 0, OFF = 1; base address 0x20
Board0Port = 0x20
BoardCount = 3
BoardStartNote = 60
#BoardEndNote = BoardStartNote + (BoardCount * 8) - 1 # 8 relays/board
BoardEndNote = 71
AllNote = 72 # turn on all (or at least lots) of the notes

class MonitorPort(mido.ports.BaseOutput):
    ''' MIDI output port that simply prints the MIDI messages sent
    '''
    def _open(self, **kwargs):
        print('Echoing MIDI messages to monitor')
        
    def _send(self, msg):
        print(str(msg))
        
class OrganPort(mido.ports.BaseOutput):
    ''' MIDI output port that writes the notes to the relay ports
    '''
    def _open(self, **kwargs): 
        # set up SMBus (I2C)
        busid = 1
        print('Initializing board at SMBus ' + str(busid)
              + ' Port ' + str(Board0Port))
        self.bus = SMBus(bus=busid)
        self.reset()
        print('Sending output to SMBus ' + str(busid))

    def _close(self):
        # cleanup
        self.reset()
        self.bus.close()
        
    def _send(self, msg):
        if msg.type is 'note_on' or msg.type is 'note_off':
           if msg.note >= BoardStartNote and msg.note <= BoardEndNote:
                print('Executing MIDI msg: ' + str(msg))
                board = int((msg.note - BoardStartNote) / 8)
                relay = (msg.note - BoardStartNote) % 8
                self.portstate[board] = self.portstate[board] ^ (1 << relay)
                self.update(board)
           elif msg.note == AllNote:
               print('Playing All Notes')
               if msg.type is 'note_on':
                   newstate = 0x0F
               else:
                   newstate = 0x0
               board = 0
               self.portstate[board] = newstate
               self.update(board)
           else:
                print('Ignoring MIDI note out of range: ' + str(msg))
        else:
            print('Ignoring MIDI message not note: ' + str(msg))

    def reset(self):
        self.portstate = [0x0] * BoardCount
        for i in range(BoardCount):
            self.update(i)
        
    def update(self, board):
        bdport = Board0Port + board
        self.bus.write_byte_data(bdport, 0, 0)
        self.bus.write_byte_data(bdport, 0x0a, self.portstate[board])
        status0 = self.bus.read_byte_data(bdport, 0x0a)
        status1 = self.bus.read_byte_data(bdport, 0x0a)
        if status1 != self.portstate[board]:
            print("WARNING: tried to set state {0:x} but read state {1:x}".format(self.portstate[board], status1))
        else:
            print('Set board {} relay state to {:x}'.format(str(board), status1))
            


#import pynput
#def KbdInput():
# Generator for MIDI messages based on window-system keyboard events.
# Responsive to key-down and key-up events, so it plays more like a keyboard.
# Doesn't even load on tty inputs like ssh which only have characters.
# need X loaded for this to work.
# Need to differentiate key-down from key-up events.
#    with pynput.keyboard.Events() as events:
#        for event in events:
#            print('Received Keyboard event {}'.format(event))
#            return Message('note_on',
#                           note=60,
#                           velocity=64)

def TtyInput():
    ''' Generator for MIDI messages based on characters from stdin.
    Convert digits 1-8 to MIDI messages toggling notes.
    Spacebar turns all notes off.
    '''
    states = [0] * 10
    def msg(offset):
        return mido.Message('note_on',
                            note=BoardStartNote + offset,
                            velocity=states[offset])

    print('Listening for tty keystrokes')
    while True:
        ch = getch.getch()
        #print('Got tty \'{}\''.format(bytearray(ch, 'ascii')))
        if ch >= '0' and ch <= '9':
            offset = int(ch)
            if states[offset] > 0:
                states[offset] = 0
            else:
                states[offset] = 64
            yield msg(offset)
        elif ch == ' ':
            print('Clearing')
            for offset in range(len(states)):
                if states[offset] > 0:
                    states[offset] = 0
                    yield msg(offset)
        else:
            print('(discarding ' + ch + ')')
            pass
        
def play(inport, outport):
    try:
        for msg in inport:
            time.sleep(msg.time)
            if not msg.is_meta:
                outport.send(msg)
    except KeyboardInterrupt:
        print('Interrupted, exiting')

# Options to play computer keyboard to organ:
#play(TtyInput(), MonitorPort())
#play(TtyInput(), OrganPort())

# Searching for a system-recognized MIDI source (e.g. piano keyboard)
# Use first one of these that matches (startswith) an available port
kbdPortList = [ 'USB Uno MIDI Interface MIDI 1', # USB/MIDI adapter
                'Akai LPK25 Wireless:Akai LPK25 Wireless Bluetooth',
                'Akai LPK25 Wireless:Akai LPK25 Wireless MIDI 1'
             ]
kbdPort = None

print('MIDI Ports available:')
for portname in mido.get_input_names():
    print('  ' + str(portname))

print('Looking for a match ...')
for portname in mido.get_input_names():
    for kbd in kbdPortList:
        if portname.startswith(kbd):
            print('Matched MIDI port ' + kbd)
            if not kbdPort:
                kbdPort = portname
                print('Using this match')

if not kbdPort:
    print('No matching port name: ' + str(kbdPortList))
    print('Giving up')
    print('If Akai LPK25 Wireless is not shown (i.e. not paired):')
    print('Is it turned on?  Is it paired?')
    print('MAC: Device A4:DA:32:36:7E:A9 (public)')
    print('Run bluetoothctl')
    print('[bluetooth]# connect A4:DA:32:36:7E:A9')
    print('Other useful commands: info, pair, trust <MAC>')
    sys.exit(0)

print('Opening MIDI input "' + kbdPort + '"')
#play(mido.open_input(kbdPort), MonitorPort())
play(mido.open_input(kbdPort), OrganPort())

# Playing MidiFile to organ:
#play(mido.MidiFile('Music/Entry_of_the_gladiators.mid'), OrganPort())
#play(mido.MidiFile('THE EAGLES.Hotel California K.mid'), OrganPort())
#play(mido.MidiFile('Music/Toccata-and-Fugue-Dm.mid'), OrganPort())
#play(mido.MidiFile('Music/Smoke-On-The-Water-2.mid'), OrganPort())
