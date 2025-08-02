#include <stdio.h>
#include <cstdlib>

int main() {
    volatile int sum = 0;
    for (int i = 0; i < 10000; i++) {
        sum += i;
    }
    printf("prog0 sum: %d\n", sum);
    return 0;
}