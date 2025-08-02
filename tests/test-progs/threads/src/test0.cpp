#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <iostream>

#define CACHE_SIZE (32 * 1024) // 32 KB
#define BLOCK_SIZE 64

int main() {
    char* buf = (char*)malloc(CACHE_SIZE);  // buffer as big as your cache
    for (int i = 0; i < CACHE_SIZE; i += BLOCK_SIZE){
        volatile char x = buf[i];   // force a load
        std::cout << i << std::endl;
    }
    return 0;
}