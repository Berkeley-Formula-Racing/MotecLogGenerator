#ifndef MOTEC_LOG_H
#define MOTEC_LOG_H

#include "ldparser.h"
#include "data_log.h"
#include <time.h>
#include <stdint.h>

// constants from original file
#define VEHICLE_PTR 1762
#define VENUE_PTR 5078
#define EVENT_PTR 8180 //0x1FF4
#define META_PTR 11336 //0x2C48

LDData* motec_log_create(int channel_count);
void motec_log_free(LDData* log);
int motec_log_add_channel(LDData* log, Channel* channel);
int motec_log_add_all_channels(LDData* log, DataLog* data_log);
int motec_log_write(LDData* log, const char* filename);
void write_ld_header(LDHeader* header, FILE* f, int channel_count);
void write_ld_channel(LDChannel* channel, FILE* f, int channel_index);

void motec_log_set_metadata(LDData* log, 
                           const char* driver,
                           const char* vehicle_id,
                           const char* venue_name,
                           const char* event_name,
                           const char* event_session,
                           const char* short_comment);

#endif