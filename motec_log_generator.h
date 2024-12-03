#ifndef MOTEC_LOG_GENERATOR_H
#define MOTEC_LOG_GENERATOR_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_log.h"
#include "motec_log.h"

typedef enum {
    LOG_TYPE_CAN,
    LOG_TYPE_CSV,
    LOG_TYPE_ACCESSPORT
} LogType;

typedef struct {
    char* log_path;
    LogType log_type;
    char* output_path;
    float frequency;
    char* dbc_path;
    
    char* driver;
    char* vehicle_id;
    int vehicle_weight;
    char* vehicle_type;
    char* vehicle_comment;
    char* venue_name;
    char* event_name;
    char* event_session;
    char* long_comment;
    char* short_comment;
} GeneratorArgs;

int parse_arguments(int argc, char** argv, GeneratorArgs* args);
char* get_output_filename(const char* input_path, const char* output_path);
int process_log_file(const GeneratorArgs* args);
void print_usage(void);
void free_arguments(GeneratorArgs* args);

#endif