#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "device.h"
#include "bm.h" /* xbm image */

static int terminated = 0;

void handle_sig(int sig) {
  terminated = 1;
}

int main(int argc, char **argv) {
  int i;
  unsigned char key;
  int val;
  int err;

  signal(SIGINT, handle_sig);
  signal(SIGTERM, handle_sig);

  if (device_init()) {
    printf("Couldn't initialize the handset, exiting\n");
    exit(1);
  }
  
  err = display_init();
  if (!err) err = display_backlight(1);

  /* draw the xbm */
  for (i=0; i<bm_width*bm_height; ++i) {
    val = (bm_bits[i/8] & (1 << (i % 8))) >> (i % 8);
    display_putpixel(i%bm_width, i/bm_width, val);
  }
  if (!err) err = display_redraw();

  /* collect some key presses */
  while (!terminated && !err) {
    key = 0;
    err = keypad_read(&key, 200);
    if (key) {
      printf("%02x ", key);
      fflush(stdout);
    }
  }
  printf("\n");

  if (!err) display_backlight(0);

  device_close();
  exit(0);
}

