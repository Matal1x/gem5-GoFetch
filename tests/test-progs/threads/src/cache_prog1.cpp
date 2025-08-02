#include <stdio.h>
#include <cstdlib>

int main() {
    int array[1024];
    for (int i = 0; i < 1024; i++) {
        array[i] = i * 2;
    }
    printf("\tprog1 done writing array\n");
    return 0;
}