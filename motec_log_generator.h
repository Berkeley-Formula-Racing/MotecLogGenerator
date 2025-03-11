#ifndef MOTEC_LOG_GENERATOR_H
#define MOTEC_LOG_GENERATOR_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_log.h"
#include "motec_log.h"
#include <stdint.h>
#include <libgen.h>


typedef struct {
    char* log_path;
    char* output_path;
    float frequency;
    
    char* driver;
    char* vehicle_id;
    char* venue_name;
    char* event_name;
    char* event_session;
    char* short_comment;
} GeneratorArgs;

int parse_arguments(int argc, char** argv, GeneratorArgs* args);
char* get_output_filename(const char* input_path, const char* output_path);
int process_log_file(GeneratorArgs* args);
void print_usage(void);
void free_arguments(GeneratorArgs* args);

#endif