TARGET=blosc.so
SOURCE=blosc.c blosclz.c shuffle.c
FLAGS= -O3 -fPIC -shared -lpthread -msse2 
CC=gcc

all:
	$(CC) $(FLAGS) $(SOURCE) -o $(TARGET)

clean:
	-rm $(TARGET)
