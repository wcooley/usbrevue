#ifndef AUDIO_H
#define AUDIO_H

#include <stdint.h>

/* callback function for audio thread - called with n samples of input in
 * inbuf, expecting n samples of output to be put in outbuf */
typedef void (*audio_callback_t)(int16_t *inbuf, int16_t *outbuf, int n);

/* sets playback/recording levels to reasonable defaults */
void audio_set_default_levels();

/* spawns audio thread with the given callback */
int audio_start(audio_callback_t callback);

/* terminates audio thread */
void audio_close();

#endif

