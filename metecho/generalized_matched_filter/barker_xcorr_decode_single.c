#include <stdio.h>
#include <stdbool.h>
#define decode_single(ipp, raw_data, ...) decode_single_base(ipp, raw_data, (struct input_data){.channel_decode = false, __VA_ARGS__ })

struct input_data {
    bool channel_decode;
};

void decode_single_base(char *ipp, char *raw_data, struct input_data data){
    printf("%s\n%s\n%s\n-----------\n", ipp, raw_data, data.channel_decode ? "true" : "false");
}

int main() {
    decode_single("testar", "skriva");
    decode_single("testar", "inte", .channel_decode=true);
    return 0;
}