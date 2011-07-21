#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "device.h"
#include "audio.h"
#include "bm.h" /* xbm image */

static int terminated = 0;

void handle_sig(int sig) {
  terminated = 1;
}

/* echo back the input with some crude (but hilarious) pitch-shifting */
void process_audio(int16_t *inbuf, int16_t *outbuf, int n) {
  int i, j;
  for (i=0; i < n/500; ++i)
    for (j=0; j < 500; ++j)
      if (i*500 + 2*j < n)
        outbuf[i*500 + j] = inbuf[i*500 + 2*j];
      else
        outbuf[i*500 + j] = outbuf[(i-1)*500 + j];
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

  if (!err) audio_set_default_levels();
  /* start the audio thread running the pitch shifter */
  if (!err) err = audio_start(process_audio);

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

  audio_close();
  device_close();
  exit(0);
}

