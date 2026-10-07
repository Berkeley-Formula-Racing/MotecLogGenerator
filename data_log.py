import cantools
import csv
import itertools
import math
import os
import tempfile
import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

class DataLog(object):
    """ Container for storing log data which contains a set of channels with time series data."""
    def __init__(self, name=""):
        self.name = name
        self.channels = {}

    def clear(self):
        self.channels = {}
        spool = getattr(self, "_csv_spool", None)
        if spool is not None:
            spool.close()
            self._csv_spool = None

    def add_channel(self, name, units, data_type, decimals, initial_message=None, initial_msgs_size=1):
        msg = None if not initial_message else [initial_message]
        self.channels[name] = Channel(name, units, data_type, decimals, msg, initial_msgs_size)

    def start(self):
        """ Returns the earliest timestamp from all existing channels [s]. """
        t = math.inf
        for name, channel in self.channels.items():
            t = min(t, channel.start())

        if t != math.inf:
            return t
        else:
            return 0.0

    def end(self):
        """ Returns the latest timestamp from all existing channels [s]. """
        end = 0
        for name, channel in self.channels.items():
            end = max(end, channel.end())

        return end

    def duration(self):
        """ Returns the duration of the log [s]. """
        return self.end() - self.start()

    def resample(self, frequency):
        """ Resamples all channels such that all messages occur at a fixed frequency.

        See the resample method of the Channel class for more details.
        """
        start = self.start()
        end = self.end()
        for channel_name in self.channels:
            self.channels[channel_name].resample(start, end, frequency)

    def from_can_log(self, log_lines, can_db):
        """ Creates channels populated with messages from a candump file and can database.

        This will create a channel for each entry in the database that has messages present in the
        log.

        log_lines: List, containing candump log lines (recorded with 'candump' with '-l')
        can_db: cantools.database
        """
        self.clear()

        # Cache all the frame ids in the database for quick lookups
        known_ids = set()
        for msg in can_db.messages:
            known_ids.add(msg.frame_id)

        for line in log_lines:
            stamp, bus, id, data = self.__parse_can_log_line(line)

            if id not in known_ids:
                continue

            db_msg = can_db.get_message_by_frame_id(id)
            msg_decoded = can_db.decode_message(id, data)

            for msg, signal in zip(msg_decoded.items(), db_msg.signals):
                name = msg[0]
                value = msg[1]

                if name in self.channels:
                    self.channels[name].messages.append(Message(stamp, value))
                else:
                    self.add_channel(name, signal.unit, float, 3, Message(stamp, value))

    def from_csv_log(self, log_source, show_progress=False):
        """ Creates channels populated with messages from a CSV log file.

        This will create a channel for each column in the CSV file, with the name of that channel
        taken from the CSV header. All channels will be created without any units. Any non numeric data
        will be ignored, and that channel will be removed. The first column of data must be time

        log_lines: List, containing CSV log lines
        """
        self.clear()

        source_path = self.__csv_source_path(log_source)
        if source_path:
            header, second_row_raw = self.__read_csv_header_rows_from_path(source_path)
            if header is None:
                return

            second_row = [field.strip() for field in second_row_raw] if second_row_raw else []
            has_units_row = self.__csv_has_units_row(second_row)
            channel_units = second_row[1:] if has_units_row else [""] * (len(header) - 1)

            if pd is not None:
                try:
                    self.__from_csv_log_pandas(source_path, header, channel_units, has_units_row, \
                        show_progress)
                    return
                except Exception as exc:
                    print("WARNING: Fast CSV path failed (%s), falling back to standard parser" % \
                        exc)

            with open(source_path, "r", newline="") as file:
                self.__from_csv_log_reader(file, show_progress=show_progress)
            return

        self.__from_csv_log_reader(log_source, show_progress=show_progress)

    def __from_csv_log_reader(self, log_source, show_progress=False):
        reader = csv.reader(log_source)
        try:
            header = [field.strip() for field in next(reader)]
        except StopIteration:
            return

        # Determine whether the CSV includes a units row. The real project data does, while some
        # simpler CSV exports only provide a header followed directly by numeric rows.
        second_row_raw = next(reader, None)
        second_row = [field.strip() for field in second_row_raw] if second_row_raw else []
        has_units_row = self.__csv_has_units_row(second_row)

        if has_units_row:
            channel_units = second_row[1:]
            row_iter = reader
        else:
            channel_units = [""] * (len(header) - 1)
            row_iter = reader if second_row_raw is None else itertools.chain([second_row_raw], reader)

        channel_entries = []
        seen_names = {}
        shared_timestamps = []
        for i, raw_name in enumerate(header[1:]):
            name = self.__unique_channel_name(raw_name, seen_names)
            units = channel_units[i].strip() if i < len(channel_units) else ""
            units = self.__default_units_for_channel(name, units)
            self.add_channel(name, units, float, 3, None, 0)
            channel = self.channels[name]
            channel.set_series(shared_timestamps, [])
            channel_entries.append((name, channel, i))

        progress_step = 5000
        processed_rows = 0

        # Go through each line grabbing all the channel values
        for values in row_iter:
            if not values:
                continue

            # Timestamp is the first element
            t = float(values[0])
            shared_timestamps.append(t)

            invalid_channels = []
            for name, channel, column_index in channel_entries:
                raw_value = values[column_index + 1] if column_index + 1 < len(values) else ""
                if raw_value == "":
                    val = 0.0
                else:
                    try:
                        val = float(raw_value)
                    except ValueError:
                        print("WARNING: Found non numeric values for channel %s, removing channel" % \
                            name)
                        invalid_channels.append(name)
                        continue

                channel.values.append(val)

            if invalid_channels:
                invalid_names = set(invalid_channels)
                channel_entries = [entry for entry in channel_entries if entry[0] not in invalid_names]
                for name in invalid_names:
                    del self.channels[name]

            processed_rows += 1

            if show_progress and processed_rows % progress_step == 0:
                print("CSV parse progress: %d rows" % processed_rows)

        if show_progress and processed_rows and processed_rows % progress_step != 0:
            print("CSV parse progress: %d rows" % processed_rows)

    def __from_csv_log_pandas(self, source_path, header, channel_units, has_units_row, show_progress):
        if show_progress:
            print("CSV parse progress: reading numeric matrix...")

        read_kwargs = {"dtype": np.float32}
        if has_units_row:
            read_kwargs["skiprows"] = [1]

        # Fast in-memory path for modest logs; use CANARY_CSV_MEMORY_LIMIT_MB=0
        # to force bounded-memory conversion on memory-constrained computers.
        limit = int(os.environ.get("CANARY_CSV_MEMORY_LIMIT_MB", "128")) * 1024 * 1024
        if os.path.getsize(source_path) <= limit:
            df = pd.read_csv(source_path, **read_kwargs)
            df.fillna(0.0, inplace=True)
            data = df.to_numpy(dtype=np.float32, copy=False)
            if data.ndim != 2 or data.shape[1] != len(header):
                raise ValueError("unexpected CSV matrix shape")
        else:
            # A disk-backed numeric matrix bounds resident memory even for long logs.
            # Pandas keeps its existing float32 conversion and missing-value behavior.
            spool = tempfile.TemporaryFile()
            rows = 0
            try:
                for chunk in pd.read_csv(source_path, chunksize=8192, **read_kwargs):
                    chunk.fillna(0.0, inplace=True)
                    matrix = chunk.to_numpy(dtype=np.float32, copy=False)
                    if matrix.shape[1] != len(header):
                        raise ValueError("unexpected CSV column count")
                    matrix.tofile(spool)
                    rows += len(matrix)
                if not rows:
                    spool.close()
                    return
                spool.flush()
                data = np.memmap(spool, dtype=np.float32, mode="r", shape=(rows, len(header)))
                self._csv_spool = spool
            except Exception:
                spool.close()
                raise

        shared_timestamps = data[:, 0]
        channel_entries = []
        seen_names = {}
        for i, raw_name in enumerate(header[1:]):
            name = self.__unique_channel_name(raw_name, seen_names)
            units = channel_units[i].strip() if i < len(channel_units) else ""
            units = self.__default_units_for_channel(name, units)
            self.add_channel(name, units, float, 3, None, 0)
            channel = self.channels[name]
            channel.set_series(shared_timestamps, data[:, i + 1])
            channel_entries.append((name, channel, i))

        if show_progress:
            print("CSV parse progress: %d rows" % data.shape[0])

    @staticmethod
    def __csv_source_path(log_source):
        if isinstance(log_source, (str, bytes, os.PathLike)):
            path = os.fspath(log_source)
            return path if os.path.isfile(path) else None

        path = getattr(log_source, "name", None)
        if isinstance(path, str) and os.path.isfile(path):
            return path

        return None

    @staticmethod
    def __read_csv_header_rows_from_path(source_path):
        with open(source_path, "r", newline="") as file:
            reader = csv.reader(file)
            try:
                header = [field.strip() for field in next(reader)]
            except StopIteration:
                return None, None
            second_row = next(reader, None)
        return header, second_row

    @staticmethod
    def __csv_has_units_row(second_row):
        def looks_numeric(value):
            if value == "":
                return True
            try:
                float(value)
                return True
            except ValueError:
                return False

        if not second_row:
            return False

        non_numeric_units = sum(0 if looks_numeric(field) else 1 for field in second_row[1:])
        return non_numeric_units > 0

    @staticmethod
    def __unique_channel_name(name, seen_names):
        base_name = name.strip()
        count = seen_names.get(base_name, 0) + 1
        seen_names[base_name] = count
        if count == 1:
            return base_name
        return "%s_%d" % (base_name, count)

    @staticmethod
    def __default_units_for_channel(name, units):
        normalized_units = str(units).strip()
        if normalized_units:
            try:
                float(normalized_units)
                normalized_units = ""
            except ValueError:
                return normalized_units

        upper_name = name.strip().upper()
        default_units = {
            "ANGRATEX": "deg/s",
            "ANGRATEY": "deg/s",
            "ANGRATEZ": "deg/s",
            "ACCELX": "g",
            "ACCELY": "g",
            "ACCELZ": "g",
            "IMUTEMP": "C",
        }
        return default_units.get(upper_name, "")

    def from_accessport_log(self, log_source, show_progress=False):
        """ Creates channels populated with messages from a COBB Accessport CSV log file.

        This will create a channel for each column in the CSV file, with the name and units of that
        channel taken from the CSV header. Any non numeric data will be ignored, and that channel
        will be removed.

        log_lines: List, containing CSV log lines
        """

        self.from_csv_log(log_source, show_progress=show_progress)

        # Accessport logs have a column for AP info which is not of any value so we'll delete it
        for key in self.channels.keys():
            if "AP Info" in key:
                del self.channels[key]
                break

        # Update all the channel names and units
        for channel_name, channel in self.channels.items():
            # Channels have the format "Name (Units)"
            if " (" in channel.name and channel.name.endswith(")"):
                name, units = channel.name.rsplit(" (", 1)
                units = units[:-1]
            else:
                name = channel.name
                units = channel.units

            channel.name = name
            channel.units = units

    @staticmethod
    def __parse_can_log_line(line):
        """ Extracts the timestamp, bus, arbitration id, and data from a single line in a can log file
        recorded with candump -l.
        """
        stamp, bus, msg = line.split()
        stamp = float(stamp[1:-1])
        id, data = msg.split("#")
        id = int(id, 16)
        data = bytearray.fromhex(data)

        return stamp, bus, id, data

    def __str__(self):
        output = "Log: %s, Duration: %f s" % (self.name, (self.end() - self.start()))
        for channel_name, channel_data in self.channels.items():
            output += "\n\t%s" % channel_data
        return output

class Channel(object):
    """ Represents a singe channel of data containing a time series of values."""
    def __init__(self, name, units, data_type, decimals, messages=None, initial_size=1):
        self.name = str(name)
        self.units = str(units)
        self.data_type = data_type
        self.decimals = decimals
        self.timestamps = None
        self.values = None
        if messages:
            self.messages = messages
        else:
            self.messages = [None]*initial_size if initial_size else []

    def set_series(self, timestamps, values):
        self.timestamps = timestamps
        self.values = values
        self.messages = None

    def sample_count(self):
        if self.values is not None:
            return len(self.values)
        return len(self.messages)

    def iter_values(self):
        if self.values is not None:
            return iter(self.values)
        return (msg.value for msg in self.messages)

    def start(self):
        if self.values is not None:
            return self.timestamps[0] if self.sample_count() else 0
        if self.messages:
            return self.messages[0].timestamp
        else:
            return 0

    def end(self):
        if self.values is not None:
            return self.timestamps[-1] if self.sample_count() else 0
        if self.messages:
            return self.messages[-1].timestamp
        else:
            return 0

    def avg_frequency(self):
        """ Computes the average frequency from the samples based on the duration of the channel
        and the number of messages"""
        if self.sample_count() >= 2:
            dt = self.end() - self.start()
            return self.sample_count() / dt if dt else 0
        else:
            return 0

    def resample(self, start_time, end_time, frequency):
        """ Resamples the data such that all messages occur at a fixed frequency.

        If multiple messages fall within the time interval between messages for the new frequency,
        the latest message will be used. When no existing messages fall within the time interval
        the most recent value will be retained. If no existing message is present within the first
        new time interval, then the first message will be initialized at 0.
        """
        if self.values is not None:
            if not self.sample_count():
                return

            num_msgs = math.floor(frequency * (end_time - start_time))
            dt_step = 1.0 / frequency

            value = 0
            t = start_time
            current_msgs_index = 0
            new_timestamps = [0.0] * num_msgs
            new_values = [0.0] * num_msgs
            for i in range(num_msgs):
                while current_msgs_index < len(self.values):
                    msg_stamp = self.timestamps[current_msgs_index]

                    if msg_stamp < t + 0.5 * dt_step:
                        value = self.values[current_msgs_index]
                        current_msgs_index += 1
                    else:
                        break

                new_timestamps[i] = t
                new_values[i] = value
                t += dt_step

            self.timestamps = new_timestamps
            self.values = new_values
            return

        if not self.messages:
            return

        # Determine how many messages this channel should have,
        num_msgs = math.floor(frequency * (end_time - start_time))
        dt_step = 1.0 / frequency

        # Create a new message at each time new time point based on the frequency. As we step
        # through the new sample points we'll find the latest pre existing message to insert there,
        # and will hold that value until we find another message.
        value = 0
        t = start_time
        current_msgs_index = 0
        new_msgs = [None] * num_msgs
        for i in range(num_msgs):
            # Grab the latest message that falls in this time window, if there is one, and update
            # the current channel value
            while current_msgs_index < len(self.messages):
                msg_stamp = self.messages[current_msgs_index].timestamp

                if msg_stamp < t + 0.5 * dt_step:
                    # This message falls in the time window
                    value = self.messages[current_msgs_index].value
                    current_msgs_index += 1
                else:
                    # This messages belongs in a future window
                    break

            new_msgs[i] = Message(t, value)
            t += dt_step

        self.messages = new_msgs

    def __str__(self):
        return "Channel: %s, Units: %s, Decimals: %d, Messages: %d, Frequency: %.2f Hz" % \
        (self.name, self.units, self.decimals, self.sample_count(), self.avg_frequency())

class Message(object):
    """ A single message in a time series of data. """
    def __init__(self, timestamp=0, value=0):
        self.timestamp = float(timestamp)
        self.value = float(value)

    def __str__(self):
        return "t=%f, value=%f" % (self.timestamp, self.value)
