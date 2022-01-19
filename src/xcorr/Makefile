CC=gcc
CFLAGS=-fPIC -shared
LIBS=-lm

build: xcorr.c
	gcc $(LIBS) -o xcorr.so xcorr.c $(CFLAGS)

.PHONY: clean

clean:
	rm -v *.so