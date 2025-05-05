#ifndef DATA_LOG_H
#define DATA_LOG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <stdbool.h>

// Message structure to store timestamp-value pairs
typedef struct {
    double timestamp;
    double value;
} Message;

// Channel structure to store time series data
typedef struct {
    char* name;
    char* units;
    int data_type;  // We'll assume float for simplicity
    int decimals;
    Message* messages;
    size_t messages_count;
    size_t messages_capacity;
} Channel;

// DataLog structure to store multiple channels
typedef struct {
    char* name;
    Channel** channels;  // Array of Channel pointers
    char** channel_names;  // Array of channel names for lookup
    size_t channels_count;
    size_t channels_capacity;
} DataLog;

// DataLog functions
DataLog* data_log_create(const char* name);
void data_log_destroy(DataLog* log);
void data_log_clear(DataLog* log);
void data_log_add_channel(DataLog* log, const char* name, const char* units, 
                         int data_type, int decimals, Message* initial_message);
double data_log_start(DataLog* log);
double data_log_end(DataLog* log);
double data_log_duration(DataLog* log);
void data_log_resample(DataLog* log, double frequency);
void data_log_from_csv_log(DataLog* log, char** log_lines, size_t num_lines);

// Channel functions
Channel* channel_create(const char* name, const char* units, 
                       int data_type, int decimals, Message* initial_message);
void channel_destroy(Channel* channel);
double channel_start(const Channel* channel);
double channel_end(const Channel* channel);
double channel_avg_frequency(const Channel* channel);
void channel_resample(Channel* channel, double start_time, 
                     double end_time, double frequency);

// Message functions
Message* message_create(double timestamp, double value);
void message_destroy(Message* message);
void data_log_add_message(DataLog* log, const char* channel_name, Message* message);

#endif // DATA_LOG_H