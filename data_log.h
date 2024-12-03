#ifndef DATA_LOG_H
#define DATA_LOG_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>

// Message structure
typedef struct Message {
    double timestamp;
    double value;
} Message;

// Channel structure
typedef struct Channel {
    char* name;
    char* units;
    int decimals;
    Message* messages;
    size_t message_count;
    size_t message_capacity;
    double (*data_type)(double); 
    double frequency;
} Channel;

// DataLog structure
typedef struct DataLog {
    char* name;
    Channel** channels;
    size_t channel_count;
    size_t channel_capacity;
} DataLog;


void trim_whitespace(char* str);

int datalog_from_can_log(DataLog* log, FILE* f, const char* dbc_path);
int datalog_from_csv_log(DataLog* log, FILE* f);
int datalog_from_accessport_log(DataLog* log, FILE* f);
int datalog_channel_count(DataLog* log);
void datalog_free(DataLog* log);
void data_log_print_channels(DataLog* log);
DataLog* datalog_create(const char* name);
void datalog_destroy(DataLog* log);
void datalog_clear(DataLog* log);
void datalog_add_channel(DataLog* log, const char* name, const char* units, int decimals);
double datalog_start(DataLog* log);
double datalog_end(DataLog* log);
double datalog_duration(DataLog* log);
void datalog_resample(DataLog* log, double frequency);
int datalog_from_csv(DataLog* log, const char* filename);



Channel* channel_create(const char* name, const char* units, int decimals, size_t initial_size);
void channel_destroy(Channel* channel);
double channel_start(Channel* channel);
double channel_end(Channel* channel);
double channel_avg_frequency(Channel* channel);


#endif