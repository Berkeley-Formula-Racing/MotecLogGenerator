#ifndef LDPARSER_H
#define LDPARSER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_STRING_LENGTH 1024
#define MAX_CHANNELS 500

// channel data dataypes
typedef enum {
    DTYPE_FLOAT16,
    DTYPE_FLOAT32,
    DTYPE_INT16,
    DTYPE_INT32
} DataType;

// channel structure
typedef struct {
    int meta_ptr;
    int prev_meta_ptr;
    int next_meta_ptr;
    int data_ptr;
    int data_len;
    DataType dtype;
    int freq;
    int shift;
    int mul;
    int scale;
    int dec;
    char name[32];
    char short_name[8];
    char unit[12];
    void* data;  
} LDChannel;

// vehicle info
typedef struct {
    char id[64];
    unsigned int weight;
    char type[32];
    char comment[32];
} LDVehicle;

// more vehicle info
typedef struct {
    char name[64];
    int vehicle_ptr;
    LDVehicle* vehicle;
} LDVenue;

// event info
typedef struct {
    char name[64];
    char session[64];
    char comment[1024];
    int venue_ptr;
    LDVenue* venue;
} LDEvent;

typedef struct {
    int meta_ptr;
    int data_ptr;
    int aux_ptr;
    LDEvent* aux;
    char driver[64];
    char vehicleid[64];
    char venue[64];
    time_t datetime;
    char short_comment[64];
    char event[64];
    char session[64];
} LDHeader;

typedef struct {
    LDHeader* head;
    LDChannel** channels;
    int channel_count;
} LDData;

LDData* ld_read_file(const char* filename);
void ld_free_data(LDData* data);
LDChannel* ld_get_channel_by_name(LDData* data, const char* name);
void ld_write_file(LDData* data, const char* filename);



#endif