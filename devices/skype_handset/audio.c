#include <stdio.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>
#include <pthread.h>
#include "audio.h"

#define DEFAULT_MIC_VOL 128
#define DEFAULT_SPKR_VOL 20
#define ALSA_DEVICE "hw:CARD=free2"
#define SAMPLE_RATE 16000

/* exact powers of two tend to give xruns for some reason */
#define BUFFER_SIZE 8000
#define PERIOD_SIZE 2000


static snd_pcm_t *capture_handle;
static snd_pcm_t *playback_handle;
static pthread_t audio_thread;
static volatile int audio_thread_running;


static int audio_configure(snd_pcm_t *device) {
  snd_pcm_hw_params_t *hw_params;
  int err;
  unsigned int sr = SAMPLE_RATE;

  err = snd_pcm_hw_params_malloc(&hw_params);
  if (err) {
    fprintf(stderr, "can't allocate hw_params: %s\n", snd_strerror(err));
    return err;
  }

  err = snd_pcm_hw_params_any(device, hw_params);
  if (err) {
    fprintf(stderr, "can't initialize hw_params: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params_set_access(device, hw_params, SND_PCM_ACCESS_RW_INTERLEAVED);
  if (err) {
    fprintf(stderr, "can't set access mode: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params_set_format(device, hw_params, SND_PCM_FORMAT_S16_LE);
  if (err) {
    fprintf(stderr, "can't set format: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params_set_rate_near(device, hw_params, &sr, 0);
  if (err) {
    fprintf(stderr, "can't set samplerate: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params_set_channels(device, hw_params, 1);
  if (err) {
    fprintf(stderr, "can't set channels: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }
  
  err = snd_pcm_hw_params_set_buffer_size(device, hw_params, BUFFER_SIZE);
  if (err) {
    fprintf(stderr, "can't set buffer size: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params_set_period_size(device, hw_params, PERIOD_SIZE, 0);
  if (err) {
    fprintf(stderr, "can't set period size: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  err = snd_pcm_hw_params(device, hw_params);
  if (err) {
    fprintf(stderr, "can't set hw params: %s\n", snd_strerror(err));
    snd_pcm_hw_params_free(hw_params);
    return err;
  }

  snd_pcm_hw_params_free(hw_params);
  return 0;
}



void audio_set_default_levels() {
  int err;
  snd_ctl_t *ctl;
  snd_ctl_elem_value_t *val;

  snd_ctl_elem_value_alloca(&val);

  if (snd_ctl_open(&ctl, ALSA_DEVICE, 0)) {
    fprintf(stderr, "can't open audio device");
    return;
  }

  /* unmute microphone */
  snd_ctl_elem_value_set_interface(val, SND_CTL_ELEM_IFACE_MIXER);
  snd_ctl_elem_value_set_name(val, "Mic Capture Switch");
  snd_ctl_elem_value_set_integer(val, 0, 1);
  err = snd_ctl_elem_write(ctl, val);
  if (err)
    fprintf(stderr, "can't unmute microphone: %s\n", snd_strerror(err));

  /* unmute speaker */
  snd_ctl_elem_value_clear(val);
  snd_ctl_elem_value_set_interface(val, SND_CTL_ELEM_IFACE_MIXER);
  snd_ctl_elem_value_set_name(val, "Speaker Playback Switch");
  snd_ctl_elem_value_set_integer(val, 0, 1);
  err = snd_ctl_elem_write(ctl, val);
  if (err)
    fprintf(stderr, "can't unmute speaker: %s\n", snd_strerror(err));

  /* set mic volume */
  snd_ctl_elem_value_clear(val);
  snd_ctl_elem_value_set_interface(val, SND_CTL_ELEM_IFACE_MIXER);
  snd_ctl_elem_value_set_name(val, "Mic Capture Volume");
  snd_ctl_elem_value_set_integer(val, 0, DEFAULT_MIC_VOL);
  err = snd_ctl_elem_write(ctl, val);
  if (err)
    fprintf(stderr, "can't set microphone volume: %s\n", snd_strerror(err));

  /* set speaker volume */
  snd_ctl_elem_value_clear(val);
  snd_ctl_elem_value_set_interface(val, SND_CTL_ELEM_IFACE_MIXER);
  snd_ctl_elem_value_set_name(val, "Speaker Playback Volume");
  snd_ctl_elem_value_set_integer(val, 0, DEFAULT_SPKR_VOL);
  snd_ctl_elem_value_set_integer(val, 1, DEFAULT_SPKR_VOL);
  err = snd_ctl_elem_write(ctl, val);
  if (err)
    fprintf(stderr, "can't set speaker volume: %s\n", snd_strerror(err));

  /* set capture source */
  snd_ctl_elem_value_clear(val);
  snd_ctl_elem_value_set_interface(val, SND_CTL_ELEM_IFACE_MIXER);
  snd_ctl_elem_value_set_name(val, "PCM Capture Source");
  snd_ctl_elem_value_set_integer(val, 0, 0);
  err = snd_ctl_elem_write(ctl, val);
  if (err)
    fprintf(stderr, "can't set capture source: %s\n", snd_strerror(err));

  snd_ctl_close(ctl);
}



static void * audio_thread_f(void *V) {
  int16_t inbuf[BUFFER_SIZE], outbuf[BUFFER_SIZE];
  int frames;
  audio_callback_t callback = (audio_callback_t) V;

  while (audio_thread_running) {
    frames = snd_pcm_readi(capture_handle, inbuf, BUFFER_SIZE);
    if (frames < 0)
      snd_pcm_recover(capture_handle, frames, 0);
    else if (frames != BUFFER_SIZE)
      fprintf(stderr, "read %d/%d frames\n", frames, BUFFER_SIZE);

    callback(inbuf, outbuf, BUFFER_SIZE);

    frames = snd_pcm_writei(playback_handle, outbuf, BUFFER_SIZE);
    if (frames < 0) {
      snd_pcm_recover(playback_handle, frames, 0);
    } else if (frames != BUFFER_SIZE)
      fprintf(stderr, "wrote %d/%d frames\n", frames, BUFFER_SIZE);
  }

  snd_pcm_drop(playback_handle);
  snd_pcm_close(playback_handle);
  snd_pcm_drop(capture_handle);
  snd_pcm_close(capture_handle);
  return NULL;
}



int audio_start(audio_callback_t callback) {
  int err;

  err = snd_pcm_open(&capture_handle, ALSA_DEVICE, SND_PCM_STREAM_CAPTURE, 0);
  if (err) {
    fprintf(stderr, "can't open capture device: %s\n", snd_strerror(err));
    return err;
  }

  err = audio_configure(capture_handle);
  if (err) 
    return err;

  err = snd_pcm_open(&playback_handle, ALSA_DEVICE, SND_PCM_STREAM_PLAYBACK, 0);
  if (err) {
    fprintf(stderr, "can't open playback device: %s\n", snd_strerror(err));
    return err;
  }

  err = audio_configure(playback_handle);
  if (err)
    return err;

  audio_thread_running = 1;

  err = pthread_create(&audio_thread, NULL, audio_thread_f, callback);
  if (err)
    fprintf(stderr, "can't spawn audio thread\n");
  return err;
}


void audio_close() {
  audio_thread_running = 0;
  if (audio_thread) {
    pthread_join(audio_thread, NULL);
    audio_thread = (pthread_t) NULL;
  }
}

