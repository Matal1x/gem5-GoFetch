#include <stdio.h>
#include <cstdlib>

#define SIZE 32768  // Try to exceed L1 D-cache size

int main() {
    int data[SIZE];
    for (int i = 0; i < SIZE; i++) {
        data[i] = i;
    }
    long sum = 0;
    for (int i = 0; i < SIZE; i++) {
        sum += data[i];
    }
    printf("\t\tprog2 large sum: %ld\n", sum);
    return 0;
}