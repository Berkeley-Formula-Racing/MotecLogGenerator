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

typedef struct {
    //REWRITE THIS FOR MAGIC NUMBERS
    uint32_t data_ptr; //4 BYTE DATA POINTER
    int num_channels; //4 BYTE NUM CHANNELS
    char* driver; //64 BYTE DRIVER
    char* vehicle_id; //64 BYTE VEHICLE_ID
    char* venue; //64 BYTE VENUE
    char* short_comment; //64 BYTE COMMENT
    char* event; //64 BYTE EVENT
    char* session; //64 BYTE SESSION
} LDHeader;

typedef struct {
    LDHeader* head;
    LDChannel** channels;
    int channel_count;
    int channel_capacity;
} LDData;

LDData* ld_read_file(const char* filename);
void ld_free_data(LDData* data);
LDChannel* ld_get_channel_by_name(LDData* data, const char* name);
void ld_write_file(LDData* data, const char* filename);
void initialize_ld_header(LDHeader* header, int num_channels);

#endif