CC=gcc
CFLAGS=-fPIC -shared
LIBS=-lm

build: libxcorr.c
	gcc $(LIBS) -o libxcorr.so libxcorr.c $(CFLAGS)

.PHONY: clean

clean:
	rm -v *.so