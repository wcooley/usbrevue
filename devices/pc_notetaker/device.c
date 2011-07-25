#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <libusb-1.0/libusb.h>

#define VEND_ID 0xe20
#define PROD_ID 0x100
#define IFACE 0
#define CONFIG 1

void error(int err);

static int terminated = 0;

void handle_sig(int sig) {
  terminated = 1;
}

int main(int argc, char **argv) {
  libusb_device_handle *handle = NULL;
  int detached_kernel_driver = 0;
  int err;

  fprintf(stderr, "Initializing: ");
  err = libusb_init(NULL);
  error(err);

  fprintf(stderr, "Looking for device\n");
  handle = libusb_open_device_with_vid_pid(NULL, VEND_ID, PROD_ID);
  if (!handle) {
    fprintf(stderr, "Device not found\n");
    libusb_exit(NULL);
    exit(1);
  }

  fprintf(stderr, "Checking for active kernel driver: ");
  err = libusb_kernel_driver_active(handle, IFACE);
  if (err == 1) {
    fprintf(stderr, "Detaching kernel driver: ");
    err = libusb_detach_kernel_driver(handle, IFACE);
    detached_kernel_driver = 1;
  }
  error(err);

  fprintf(stderr, "Setting configuration: ");
  err = libusb_set_configuration(handle, CONFIG);
  error(err);

  fprintf(stderr, "Claiming interface: ");
  err = libusb_claim_interface(handle, IFACE);
  error(err);

  signal(SIGINT, handle_sig);
  signal(SIGTERM, handle_sig);

  unsigned char packet[8], prev_byte=0;
  int i, transferred;
  int lift_detected;

  while (!err && !terminated) {
    err = libusb_interrupt_transfer(handle, 0x81, packet, 8, &transferred, 50);

    if (!err) {
      lift_detected = 0;
      for (i=0; i<transferred; ++i) {
        /* everything lines up nicely if bytes >= 0x80 go on new lines */
        if (packet[i] & 0x80) {
          /* 0x80b3 seems to mean pen is lifted - defer newline to end of
           * packet for bonus readability */
          if (packet[i] == 0xb3 && prev_byte == 0x80)
            lift_detected = 1;
          else
            printf("\n");
        }
        printf("%02x ", packet[i]);
        prev_byte = packet[i];
      }
      if (lift_detected)
        printf("\n");
    }
    fflush(stdout);
    /* don't break the loop if we only timed out */
    if (err == LIBUSB_ERROR_TIMEOUT)
      err = 0;
  }

  if (!terminated)
    error(err);

  fprintf(stderr, "Releasing interface: ");
  err = libusb_release_interface(handle, IFACE);
  error(err);

  if (detached_kernel_driver) {
    fprintf(stderr, "Reattaching kernel driver: ");
    err = libusb_attach_kernel_driver(handle, IFACE);
    error(err);
  }

  libusb_close(handle);
  libusb_exit(NULL);
  exit(0);
}

void error(int err) {
  switch (err) {
    case LIBUSB_SUCCESS:
      fprintf(stderr, "Success\n");
      break;
    case LIBUSB_ERROR_IO:
      fprintf(stderr, "I/O error\n");
      break;
    case LIBUSB_ERROR_INVALID_PARAM:
      fprintf(stderr, "Invalid param\n");
      break;
    case LIBUSB_ERROR_ACCESS:
      fprintf(stderr, "Access error\n");
      break;
    case LIBUSB_ERROR_NO_DEVICE:
      fprintf(stderr, "No device\n");
      break;
    case LIBUSB_ERROR_NOT_FOUND:
      fprintf(stderr, "Not found\n");
      break;
    case LIBUSB_ERROR_BUSY:
      fprintf(stderr, "Busy\n");
      break;
    case LIBUSB_ERROR_TIMEOUT:
      fprintf(stderr, "Timeout\n");
      break;
    case LIBUSB_ERROR_OVERFLOW:
      fprintf(stderr, "Overflow\n");
      break;
    case LIBUSB_ERROR_PIPE:
      fprintf(stderr, "Pipe error\n");
      break;
    case LIBUSB_ERROR_INTERRUPTED:
      fprintf(stderr, "Interrupted\n");
      break;
    case LIBUSB_ERROR_NO_MEM:
      fprintf(stderr, "No memory\n");
      break;
    case LIBUSB_ERROR_NOT_SUPPORTED:
      fprintf(stderr, "Not supported\n");
      break;
    case LIBUSB_ERROR_OTHER:
    default:
      fprintf(stderr, "Unknown error\n");
      break;
  }
}

