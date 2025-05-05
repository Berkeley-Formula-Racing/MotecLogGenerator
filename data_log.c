#include "data_log.h"

#define INITIAL_CAPACITY 10

// Message functions implementation
Message* message_create(double timestamp, double value) {
    Message* msg = (Message*)malloc(sizeof(Message));
    if (msg) {
        msg->timestamp = timestamp;
        msg->value = value;
    }
    return msg;
}

void message_destroy(Message* message) {
    free(message);
}

// Channel functions implementation
Channel* channel_create(const char* name, const char* units, 
                       int data_type, int decimals, Message* initial_message) {
    Channel* channel = (Channel*)malloc(sizeof(Channel));
    if (!channel) return NULL;

    channel->name = strdup(name);
    channel->units = strdup(units);
    channel->data_type = data_type;
    channel->decimals = decimals;
    channel->messages_count = 0;
    channel->messages_capacity = INITIAL_CAPACITY;
    
    channel->messages = (Message*)malloc(sizeof(Message) * channel->messages_capacity);
    if (!channel->messages) {
        free(channel->name);
        free(channel->units);
        free(channel);
        return NULL;
    }

    if (initial_message) {
        channel->messages[0] = *initial_message;
        channel->messages_count = 1;
    }

    return channel;
}

void channel_destroy(Channel* channel) {
    if (channel) {
        free(channel->name);
        free(channel->units);
        free(channel->messages);
        free(channel);
    }
}

double channel_start(const Channel* channel) {
    if (channel && channel->messages_count > 0) {
        return channel->messages[0].timestamp;
    }
    return 0.0;
}

double channel_end(const Channel* channel) {
    if (channel && channel->messages_count > 0) {
        return channel->messages[channel->messages_count - 1].timestamp;
    }
    return 0.0;
}

double channel_avg_frequency(const Channel* channel) {
    if (channel && channel->messages_count >= 2) {
        double dt = channel_end(channel) - channel_start(channel);
        return channel->messages_count / dt;
    }
    return 0.0;
}

// DataLog functions implementation
DataLog* data_log_create(const char* name) {
    DataLog* log = (DataLog*)malloc(sizeof(DataLog));
    if (!log) return NULL;

    log->name = strdup(name);
    log->channels_count = 0;
    log->channels_capacity = INITIAL_CAPACITY;
    
    log->channels = (Channel**)malloc(sizeof(Channel*) * log->channels_capacity);
    log->channel_names = (char**)malloc(sizeof(char*) * log->channels_capacity);
    
    if (!log->channels || !log->channel_names) {
        free(log->channels);
        free(log->channel_names);
        free(log->name);
        free(log);
        return NULL;
    }

    return log;
}

void data_log_destroy(DataLog* log) {
    if (log) {
        for (size_t i = 0; i < log->channels_count; i++) {
            channel_destroy(log->channels[i]);
            free(log->channel_names[i]);
        }
        free(log->channels);
        free(log->channel_names);
        free(log->name);
        free(log);
    }
}

void data_log_clear(DataLog* log) {
    if (log) {
        for (size_t i = 0; i < log->channels_count; i++) {
            channel_destroy(log->channels[i]);
            free(log->channel_names[i]);
        }
        log->channels_count = 0;
    }
}

void data_log_add_channel(DataLog* log, const char* name, const char* units, 
                         int data_type, int decimals, Message* initial_message) {
    if (!log) return;

    // Resize if needed
    if (log->channels_count >= log->channels_capacity) {
        size_t new_capacity = log->channels_capacity * 2;
        Channel** new_channels = (Channel**)realloc(log->channels, 
                                                  sizeof(Channel*) * new_capacity);
        char** new_names = (char**)realloc(log->channel_names, 
                                         sizeof(char*) * new_capacity);
        
        if (!new_channels || !new_names) return;

        log->channels = new_channels;
        log->channel_names = new_names;
        log->channels_capacity = new_capacity;
    }

    Channel* channel = channel_create(name, units, data_type, decimals, initial_message);
    if (channel) {
        log->channels[log->channels_count] = channel;
        log->channel_names[log->channels_count] = strdup(name);
        log->channels_count++;
    }
}

double data_log_start(DataLog* log) {
    if (!log || log->channels_count == 0) return 0.0;

    double t = DBL_MAX;
    for (size_t i = 0; i < log->channels_count; i++) {
        double start = channel_start(log->channels[i]);
        if (start < t) t = start;
    }

    return t == DBL_MAX ? 0.0 : t;
}

double data_log_end(DataLog* log) {
    if (!log || log->channels_count == 0) return 0.0;

    double end = 0.0;
    for (size_t i = 0; i < log->channels_count; i++) {
        double channel_end_time = channel_end(log->channels[i]);
        if (channel_end_time > end) end = channel_end_time;
    }

    return end;
}

double data_log_duration(DataLog* log) {
    return data_log_end(log) - data_log_start(log);
}

void data_log_add_message(DataLog* log, const char* channel_name, Message* message) {
    if (!log || !channel_name || !message) return;
    
    // Find the channel
    for (size_t i = 0; i < log->channels_count; i++) {
        Channel* channel = log->channels[i];
        if (strcmp(channel->name, channel_name) == 0) {
            // Resize messages array if needed
            if (channel->messages_count >= channel->messages_capacity) {
                size_t new_capacity = channel->messages_capacity * 2;
                Message* new_messages = (Message*)realloc(channel->messages, 
                                                        sizeof(Message) * new_capacity);
                if (!new_messages) return;
                
                channel->messages = new_messages;
                channel->messages_capacity = new_capacity;
            }
            
            // Add the message
            channel->messages[channel->messages_count] = *message;
            channel->messages_count++;
            return;
        }
    }
}