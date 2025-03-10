#include "motec_log.h"
#include <string.h>
#include <stdint.h>

#define INITIAL_CHANNEL_CAPACITY 1000

LDData* motec_log_create(int channel_count) {
    LDData* log = (LDData*)malloc(sizeof(LDData));
    if (!log) return NULL;
    
    memset(log, 0, sizeof(LDData));
    
    log->channel_capacity = INITIAL_CHANNEL_CAPACITY;
    log->channels = (LDChannel**)malloc(sizeof(LDChannel*) * log->channel_capacity);
    if (!log->channels) {
        free(log);
        return NULL;
    }
    
    log->channel_count = channel_count;
    log->head = (LDHeader*)malloc(sizeof(LDHeader*));
    //time_t curTime = time(NULL); //NEED TO DO MANUALLY
    //struct tm *info = localtime(&curTime); //DATE FORMAT SHOULD BE M/D/Y and H/M/S
    
    return log;
}

void motec_log_free(LDData* log) {
    //REWRITE THIS FOR MAGIC NUMBERS
    ld_free_data(log);
}


int motec_log_add_channel(LDData* log, Channel* channel) {
    if (!log || !channel) return -1;

    // Debug
    // printf("Debug - Adding channel '%s' with unit '%s'\n", 
    //     channel->name, channel->units);
    
    if (log->channel_count >= log->channel_capacity) {
        int new_capacity = log->channel_capacity * 2;
        LDChannel** new_channels = (LDChannel**)realloc(log->channels, 
            sizeof(LDChannel*) * new_capacity);
        if (!new_channels) return -1;
        
        log->channels = new_channels;
        log->channel_capacity = new_capacity;
    }
    
    log->head->data_ptr += sizeof(LDChannel);
    
    for (int i = 0; i < log->channel_count; i++) {
        log->channels[i]->data_ptr += sizeof(LDChannel);
    }
    
    int meta_ptr, prev_meta_ptr, data_ptr;
    if (log->channel_count > 0) {
        meta_ptr = log->channels[log->channel_count-1]->next_meta_ptr;
        prev_meta_ptr = log->channels[log->channel_count-1]->meta_ptr;
        data_ptr = log->channels[log->channel_count-1]->data_ptr + 
            log->channels[log->channel_count-1]->data_len * sizeof(float);
    } else {
        meta_ptr = META_PTR;
        prev_meta_ptr = 0;
        data_ptr = log->head->data_ptr;
    }
    
    LDChannel* ld_channel = (LDChannel*)malloc(sizeof(LDChannel));
    if (!ld_channel) return -1;
    
    ld_channel->meta_ptr = meta_ptr;
    ld_channel->prev_meta_ptr = prev_meta_ptr;
    ld_channel->next_meta_ptr = meta_ptr + sizeof(LDChannel);
    ld_channel->data_ptr = data_ptr;
    ld_channel->data_len = channel->message_count;
    ld_channel->dtype = DTYPE_FLOAT32;
    ld_channel->freq = (int)channel_avg_frequency(channel);
    ld_channel->shift = 0;
    ld_channel->mul = 1;
    ld_channel->scale = 1;
    ld_channel->dec = 0;
    strncpy(ld_channel->name, channel->name, sizeof(ld_channel->name)-1);
    strncpy(ld_channel->unit, channel->units, sizeof(ld_channel->unit)-1);
    
    ld_channel->data = malloc(channel->message_count * sizeof(float));
    if (!ld_channel->data) {
        free(ld_channel);
        return -1;
    }
    
    for (int i = 0; i < channel->message_count; i++) {
        ((float*)ld_channel->data)[i] = (float)channel->messages[i].value;
    }
    
    log->channels[log->channel_count++] = ld_channel;
    return 0;
}

int motec_log_add_all_channels(LDData* log, DataLog* data_log) {
    if (!log || !data_log) return -1;
    
    for (int i = 0; i < data_log->channel_count; i++) { // maybe error handling issue?
        if (motec_log_add_channel(log, data_log->channels[i]) != 0) {
            return -1;
        }
    }
    return 0;
}

int motec_log_write(LDData* log, const char* filename) {
    if (!log || !filename) return -1;
    
    FILE* f = fopen(filename, "wb");
    if (!f) return -1;
    
    if (log->channel_count > 0) {
        log->channels[log->channel_count-1]->next_meta_ptr = 0;
        
        write_ld_header(log->head, f, log->channel_count);
        
        for (int i = 0; i < log->channel_count; i++) {
            LDChannel* chan = log->channels[i];
            fseek(f, chan->meta_ptr, SEEK_SET);
            write_ld_channel(chan, f, i);
            
            fseek(f, chan->data_ptr, SEEK_SET);
            fwrite(chan->data, sizeof(float), chan->data_len, f);
        }
    } else {
        write_ld_header(log->head, f, 0);
    }
    
    fclose(f);
    return 0;
}

void write_ld_channel(LDChannel* channel, FILE* f, int channel_index) {

    fwrite(&channel->prev_meta_ptr, sizeof(int), 1, f);
    fwrite(&channel->next_meta_ptr, sizeof(int), 1, f);
    fwrite(&channel->data_ptr, sizeof(int), 1, f);
    fwrite(&channel->data_len, sizeof(int), 1, f);
    
    uint16_t dtype_a = (channel->dtype == DTYPE_FLOAT32 || channel->dtype == DTYPE_FLOAT16) ? 0x07 : 0x00;
    uint16_t dtype = (channel->dtype == DTYPE_FLOAT16 || channel->dtype == DTYPE_INT16) ? 2 : 4;
    fwrite(&dtype_a, sizeof(uint16_t), 1, f);
    fwrite(&dtype, sizeof(uint16_t), 1, f);
    
    fwrite(&channel->freq, sizeof(int16_t), 1, f);
    fwrite(&channel->shift, sizeof(int16_t), 1, f);
    fwrite(&channel->mul, sizeof(int16_t), 1, f);
    fwrite(&channel->scale, sizeof(int16_t), 1, f);
    fwrite(&channel->dec, sizeof(int16_t), 1, f);
    
    fwrite(channel->name, sizeof(char), 32, f);
    fwrite(channel->short_name, sizeof(char), 8, f);
    fwrite(channel->unit, sizeof(char), 12, f);
}

void motec_log_set_metadata(LDData* log,
                           const char* driver,
                           const char* vehicle_id, 
                           const char* venue_name,
                           const char* event_name,
                           const char* event_session,
                           const char* short_comment) {
                            
    if (driver) strncpy(log->head->driver, driver, sizeof(log->head->driver)-1);
    if (vehicle_id) strncpy(log->head->vehicle_id, vehicle_id, sizeof(log->head->vehicle_id)-1);
    if (venue_name) strncpy(log->head->venue, venue_name, sizeof(log->head->venue)-1);
    if (event_name) strncpy(log->head->event, event_name, sizeof(log->head->event)-1);
    if (event_session) strncpy(log->head->session, event_session, sizeof(log->head->session)-1);
    if (short_comment) strncpy(log->head->short_comment, short_comment, sizeof(log->head->short_comment)-1);
    log->head->data_ptr = META_PTR + (log->channel_capacity * log->head->num_channels);
}

void write_ld_header(LDHeader* header, FILE* f, int channel_count){
    uint32_t constants[3] = {0x40,0x00,META_PTR};
    fwrite(constants,4,3,f);
    fwrite(header->data_ptr,4,1,f);
    uint32_t constants[12] = {0x00,0x00,0x00,0x00,0x00,0x1FF4,0x00,0x00,0x00,0x00,0x00,0x00};
    fwrite(constants,4,12,f);
    uint16_t constants[3] = {0x01,0x4240,0x0F};
    fwrite(constants,2,3,f);
    uint32_t constants[6] = {0x1F44,0x4C4441,0x00,0xADB001A4,(uint32_t)channel_count,0x00};
    fwrite(constants,4,1,f);

    time_t curTime = time(NULL); //NEED TO DO MANUALLY
    struct tm *info = localtime(&curTime); //DATE FORMAT SHOULD BE M/D/Y and H/M/S
    char dest[11];

    time_t now;
    struct tm *tm_struct;

    time(&now);
    tm_struct = localtime(&now);

    strftime(dest, 11, "%D", tm_struct);
    fwrite(dest, 1, 10, f);

    uint16_t constants[3] = {0x00,0x00,0x00};
    fwrite(constants,2,3,f);

    uint32_t constants[4] = {0x00,0x00,0x00,0x00};
    fwrite(constants,4,4,f);

    fprintf(f,"%d:%d:%d",tm_struct->tm_hour,tm_struct->tm_min,tm_struct->tm_sec);

    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00};        
    fwrite(constants,4,6,f);


    //REPLACE WITH DRIVER
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }

    //REPLACE WITH VEHICLE_ID
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }

    //NULL BYTES
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }

    //REPLACE WITH VENUE
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }


    for(int i = 0; i < 272; i++){
        fwrite(constants,4,1,f);
    }

    uint32_t constants[1] = {0x0C81A4};        
    fwrite(constants,4,1,f);

    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }
    
    uint16_t constants[3] = {0x00,0x00,0x00};
    fwrite(constants,2,1,f);


    //REPLACE WITH COMMENT
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }

    uint16_t constants[3] = {0x00,0x00,0x00};
    fwrite(constants,2,1,f);


    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 31; i++){
        fwrite(constants,4,1,f);
    }


    //REPLACE WITH EVENT
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }


    //REPLACE WITH SESSION
    uint32_t constants[6] = {0x00,0x00,0x00,0x00,0x00,0x00}; 

    for(int i = 0; i < 16; i++){
        fwrite(constants,4,1,f);
    }
}