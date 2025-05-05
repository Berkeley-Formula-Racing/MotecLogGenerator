CC=gcc
CFLAGS=-fPIC -Wall -Wextra -O2
LDFLAGS=-shared

all: libdatalog.so

libdatalog.so: data_log.o
	$(CC) $(LDFLAGS) -o $@ $^

data_log.o: data_log.c data_log.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f *.o *.so
