#include <stdio.h>
#include <cstdlib>

volatile int shared = 42;

int main() {
    for (int i = 0; i < 100000; i++) {
        shared++;
    }
    printf("\t\t\tprog3 final shared: %d\n", shared);
    return 0;
}