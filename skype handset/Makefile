CFLAGS += -Wall -g -pthread
LDFLAGS += -lusb-1.0 -lasound -pthread

all: test

test: device.o test.o audio.o

clean:
	@- rm test *.o
