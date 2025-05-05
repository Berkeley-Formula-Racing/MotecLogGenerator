import ctypes
from ctypes import Structure, c_double, c_char_p, c_int, c_size_t, POINTER
import os

# Define the structures to match our C code
class Message(Structure):
    _fields_ = [
        ("timestamp", c_double),
        ("value", c_double)
    ]

class Channel(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("units", c_char_p),
        ("data_type", c_int),
        ("decimals", c_int),
        ("messages", POINTER(Message)),
        ("messages_count", c_size_t),
        ("messages_capacity", c_size_t)
    ]

class DataLog(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("channels", POINTER(POINTER(Channel))),
        ("channel_names", POINTER(c_char_p)),
        ("channels_count", c_size_t),
        ("channels_capacity", c_size_t)
    ]

# Load the C library
lib_path = os.path.join(os.path.dirname(__file__), "libdatalog.so")
_lib = ctypes.CDLL(lib_path)

# Define function prototypes
_lib.data_log_create.argtypes = [c_char_p]
_lib.data_log_create.restype = POINTER(DataLog)

_lib.data_log_destroy.argtypes = [POINTER(DataLog)]
_lib.data_log_destroy.restype = None

_lib.data_log_clear.argtypes = [POINTER(DataLog)]
_lib.data_log_clear.restype = None

_lib.data_log_add_channel.argtypes = [POINTER(DataLog), c_char_p, c_char_p, c_int, c_int, POINTER(Message)]
_lib.data_log_add_channel.restype = None

_lib.data_log_start.argtypes = [POINTER(DataLog)]
_lib.data_log_start.restype = c_double

_lib.data_log_end.argtypes = [POINTER(DataLog)]
_lib.data_log_end.restype = c_double

_lib.data_log_duration.argtypes = [POINTER(DataLog)]
_lib.data_log_duration.restype = c_double

_lib.data_log_add_message.argtypes = [POINTER(DataLog), c_char_p, POINTER(Message)]
_lib.data_log_add_message.restype = None

class DataLogWrapper:
    """Python wrapper for the C DataLog implementation"""
    def __init__(self, name=""):
        self._log = _lib.data_log_create(name.encode('utf-8'))
        
    def __del__(self):
        if hasattr(self, '_log'):
            _lib.data_log_destroy(self._log)

    def clear(self):
        _lib.data_log_clear(self._log)

    def add_channel(self, name, units, data_type, decimals, initial_message=None):
        if initial_message:
            msg = Message(initial_message.timestamp, initial_message.value)
            _lib.data_log_add_channel(self._log, name.encode('utf-8'), 
                                    units.encode('utf-8'), data_type, decimals, 
                                    ctypes.byref(msg))
        else:
            _lib.data_log_add_channel(self._log, name.encode('utf-8'), 
                                    units.encode('utf-8'), data_type, decimals, 
                                    None)

    def start(self):
        return _lib.data_log_start(self._log)

    def end(self):
        return _lib.data_log_end(self._log)

    def duration(self):
        return _lib.data_log_duration(self._log)

    @property
    def channels(self):
        """Return a dictionary of channels"""
        result = {}
        for i in range(self._log.contents.channels_count):
            chan = self._log.contents.channels[i].contents
            name = chan.name.decode('utf-8')
            result[name] = chan
        return result
    
    def from_csv_log(self, lines):
        """Process CSV log data"""
        # Skip header line
        header = lines[0].strip().split(',')
        
        # Process data lines
        data_by_channel = {}  # Temporary storage for messages
        
        # First collect all data by channel
        for line in lines[1:]:
            values = line.strip().split(',')
            try:
                timestamp = float(values[0])
                for i, value in enumerate(values[1:], 1):
                    if value.strip():  # Skip empty values
                        try:
                            msg = Message(timestamp, float(value))
                            channel_name = header[i]
                            if channel_name not in data_by_channel:
                                data_by_channel[channel_name] = []
                            data_by_channel[channel_name].append(msg)
                        except ValueError:
                            continue
            except ValueError:
                continue
        
        # Now add channels with their collected messages
        for channel_name, messages in data_by_channel.items():
            if messages:  # Only add channel if it has messages
                # Add channel with first message
                self.add_channel(channel_name, "", 0, 0, messages[0])
                
                # Add remaining messages using data_log_add_message
                for msg in messages[1:]:
                    _lib.data_log_add_message(self._log, 
                                            channel_name.encode('utf-8'),
                                            ctypes.byref(msg))