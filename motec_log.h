#ifndef MOTEC_LOG_H
#define MOTEC_LOG_H

#include "ldparser.h"
#include "data_log.h"
#include <time.h>

// constants from original file
#define VEHICLE_PTR 1762
#define VENUE_PTR 5078
#define EVENT_PTR 8180
#define HEADER_PTR 11336

typedef struct {
    char driver[64];
    char vehicle_id[64];
    unsigned int vehicle_weight;
    char vehicle_type[32];
    char vehicle_comment[32];
    char venue_name[64];
    char event_name[64];
    char event_session[64];
    char long_comment[1024];
    char short_comment[64];
    time_t datetime;
    
    LDHeader* ld_header;
    LDChannel** ld_channels;
    int channel_count;
    int channel_capacity;
} MotecLog;

MotecLog* motec_log_create(void);
void motec_log_free(MotecLog* log);
int motec_log_initialize(MotecLog* log);
int motec_log_add_channel(MotecLog* log, Channel* channel);
int motec_log_add_all_channels(MotecLog* log, DataLog* data_log);
int motec_log_write(MotecLog* log, const char* filename);
void write_ld_header(LDHeader* header, FILE* f, int channel_count);
void write_ld_channel(LDChannel* channel, FILE* f, int channel_index);

void motec_log_set_metadata(MotecLog* log, 
                           const char* driver,
                           const char* vehicle_id,
                           unsigned int vehicle_weight,
                           const char* vehicle_type,
                           const char* vehicle_comment,
                           const char* venue_name,
                           const char* event_name,
                           const char* event_session,
                           const char* long_comment,
                           const char* short_comment);

#endif