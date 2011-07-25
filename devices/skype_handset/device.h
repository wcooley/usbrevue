#ifndef DEVICE_H
#define DEVICE_H

#define KEY_0             0xb0
#define KEY_1             0xb1
#define KEY_2             0xb2
#define KEY_3             0xb3
#define KEY_4             0xb4
#define KEY_5             0xb5
#define KEY_6             0xb6
#define KEY_7             0xb7
#define KEY_8             0xb8
#define KEY_9             0xb9
#define KEY_STAR          0xba
#define KEY_POUND         0xbb
#define KEY_LEFT_CONTEXT  0x1a
#define KEY_RIGHT_CONTEXT 0x1b
#define KEY_SKYPE         0x1c
#define KEY_UP            0x1d
#define KEY_DOWN          0x1e
#define KEY_YES           0x1f
#define KEY_TALK          0x1f
#define KEY_NO            0x20
#define KEY_END           0x20
#define KEY_LIST          0x21
#define KEY_MUTE          0x2f
#define KEY_VOLUME_UP     0x32
#define KEY_VOLUME_DOWN   0x33
#define KEY_RECORD        0x34
#define KEY_OUT           0xc3


int device_init();
void device_close();

int display_init();
void display_putpixel(int x, int y, int val);
unsigned char display_getpixel(int x, int y);
int display_redraw();
int display_backlight(int on);

int keypad_read(unsigned char *key, unsigned int timeout);

#endif

