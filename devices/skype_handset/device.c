#include <stdio.h>
#include <libusb-1.0/libusb.h>
#include "device.h"

#define VEND_ID 0x1778
#define PROD_ID 0x0406
#define IFACE 3
#define CONFIG 1


static libusb_device_handle *handle;
static int detached_kernel_driver;

static unsigned char disp_buffer[96][64];
static unsigned char disp_dirty[12][4];
static unsigned char disp_cmd[16];

void error(int err);



int device_init() {
  int err, config;

  err = libusb_init(NULL);
  if (err) return err;

  handle = libusb_open_device_with_vid_pid(NULL, VEND_ID, PROD_ID);
  if (!handle) {
    err = LIBUSB_ERROR_NO_DEVICE;
    goto abort;
  }

  err = libusb_kernel_driver_active(handle, IFACE);
  if (err == 1) {
    err = libusb_detach_kernel_driver(handle, IFACE);
    if (err) goto abort;
    detached_kernel_driver = 1;
  } else if (err) goto abort;
  
  err = libusb_get_configuration(handle, &config);
  if (err) goto abort;

  if (config != CONFIG) {
    err = libusb_set_configuration(handle, CONFIG);
    if (err) goto abort;
  }

  err = libusb_claim_interface(handle, IFACE);
  if (err) goto abort;

  return 0;

abort:
  device_close();
  error(err);
  return err;
}


void device_close() {
  if (handle) {
    libusb_release_interface(handle, IFACE);
    if (detached_kernel_driver)
      libusb_attach_kernel_driver(handle, IFACE);
    libusb_close(handle);
  }
  handle = 0;
  detached_kernel_driver = 0;
  libusb_exit(NULL);
}





static int send_display_command() {
  int err;
  err = libusb_control_transfer(handle, 0x21, 0x9, 0x200, 0x3, disp_cmd, 16, 5000);
  return err==16? 0: err;
}

/* waits for, and ignores, an interupt request */
static int interrupt() {
  unsigned char packet[16];
  int transferred;
  int timeout = 5000;
  return libusb_interrupt_transfer(handle, 0x83, packet, 16, &transferred, timeout);
}


/* waits for an interrupt acknowledging the last display command
 * this currently throws away keypresses made during drawing commands --
 * it might be worth buffering these
 */
static int get_ack() {
  unsigned char packet[16];
  int transferred;
  int err = 0;
  int timeout = 5000; 
  packet[9] = 0;
  while (!err && packet[9] != disp_cmd[15])
    err = libusb_interrupt_transfer(handle, 0x83, packet, 16, &transferred, timeout);
  return err;
}

/* draws the data in bitmap to the cell at col,row */
static int drawcell(int col, int row, unsigned char *bitmap) {
  int i;
  int err;
  int pos = ((3-row)<<6) | col;
  int checksum = pos;

  for (i=0; i<16; ++i)
    checksum ^= bitmap[i];

  /* bump the sequence bits and put 0xd in the top half of byte 15 */
  disp_cmd[3] ^= 0x01;
  disp_cmd[15] = 0xd0 | (((disp_cmd[15] & 0x0f) + 1) % 10);

  disp_cmd[2]  = pos;
  disp_cmd[7]  = bitmap[0];
  disp_cmd[8]  = bitmap[1];
  disp_cmd[9]  = bitmap[2];
  disp_cmd[10] = bitmap[3];
  disp_cmd[11] = bitmap[4];
  disp_cmd[12] = bitmap[5];
  disp_cmd[13] = bitmap[6];
  disp_cmd[14] = bitmap[7];

  err = send_display_command();
  if (err)
    return err;
  /* read and discard an interrupt before sending the second packet
   * it's possible that an unfortunately-timed key press would break this
   * code -- it might be better to wait for an interrupt whose byte 0
   * corresponds to disp_cmd's byte 3
   */
  err = interrupt();
  if (err)
    return err;

  /* bump the sequence bits and put 0xa in the top half of byte 15 */
  disp_cmd[3] ^= 0x01;
  disp_cmd[15] = 0xa0 | (((disp_cmd[15] & 0x0f) + 1) % 10);

  disp_cmd[2]  = bitmap[8];
  disp_cmd[7]  = bitmap[9];
  disp_cmd[8]  = bitmap[10];
  disp_cmd[9]  = bitmap[11];
  disp_cmd[10] = bitmap[12];
  disp_cmd[11] = bitmap[13];
  disp_cmd[12] = bitmap[14];
  disp_cmd[13] = bitmap[15];
  disp_cmd[14] = checksum;

  err = send_display_command();
  if (err)
    return err;

  return get_ack();
}

/* marks each cell as dirty and sends a display initialization command */
int display_init() {
  int i,j;
  int err;
  for (i=0; i<12; ++i)
    for (j=0; j<4; ++j)
      disp_dirty[i][j]=1;

  disp_cmd[2]  = 0x86;
  disp_cmd[3]  = 0x51;
  disp_cmd[7]  = 0xea;
  disp_cmd[8]  = 0xee;
  disp_cmd[9]  = 0x0a;
  disp_cmd[10] = 0x19;
  disp_cmd[11] = 0x28;
  disp_cmd[15] = 0x01;
  err = send_display_command();
  if (err)
    error(err);
  return err;
}

/* writes a pixel value to the screen buffer
 * the pixel won't get drawn to the device until the next display_redraw()
 * call
 */
void display_putpixel(int x, int y, int val) {
  if (x < 0 || x > 95 || y < 0 || y > 63)
    return;
  val = !!val;
  if (val != disp_buffer[x][y]) {
    disp_dirty[x/12][y/4] = 1;
    disp_buffer[x][y] = val;
  }
}

/* returns a pixel value from the screen buffer
 * this may not correspond to the displayed pixel if display_redraw()
 * hasn't been called since initialization.
 */
unsigned char display_getpixel(int x, int y) {
  if (x < 0 || x > 95 || y < 0 || y > 63)
    return 0;
  return disp_buffer[x][y];
}



int display_redraw() {
  int col,row;    /* counts cells */
  int byte,bit;   /* counts bits within a cell */
  int x,y;        /* in pixels */
  int err;
  unsigned char bytes[16];

  for (col=0; col<12; ++col) {
    for (row=0; row<4; ++row) {
      if (!disp_dirty[col][row])
        continue;
      for (byte=0; byte<16; ++byte) {
        bytes[byte] = 0;
        x = col*8 + byte/2;
        y = row*16;
        if (byte%2 == 0)
          y += 8;
        for (bit=0; bit<8; ++bit)
          bytes[byte] = (bytes[byte] << 1) | !disp_buffer[x][y+bit];
      }
      disp_dirty[col][row] = 0;
      err = drawcell(col, row, bytes);
      if (err) {
        error(err);
        return err;
      }
    }
  }
  return 0;
}

int display_backlight(int on) {
  int err;
  /* bump the sequence bits, put 0 in the top half of byte 15 */
  disp_cmd[3] ^= 0x01;
  disp_cmd[15] = (((disp_cmd[15] & 0x0f) + 1) % 10);

  disp_cmd[2]  = 0x95 + !on;
  disp_cmd[7]  = 0;
  disp_cmd[8]  = 0;
  disp_cmd[9]  = 0;
  disp_cmd[10] = 0;
  disp_cmd[11] = 0;
  disp_cmd[12] = 0;
  disp_cmd[13] = 0;
  disp_cmd[14] = 0;

  err = send_display_command();
  if (err) {
    error(err);
    return err;
  }
  err = get_ack();
  if (err)
    error(err);
  return err;
}






int keypad_read(unsigned char *key, unsigned int timeout) {
  unsigned char packet[16];
  packet[14] = 0;
  int transferred, err;

  err = libusb_interrupt_transfer(handle, 0x83, packet, 16, &transferred, timeout);
  if (err && err != LIBUSB_ERROR_TIMEOUT) {
    error(err);
    return err;
  }

  *key = packet[14];
  return 0; 
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
      fprintf(stderr, "Unknown error\n");
      break;
    default:
      fprintf(stderr, "%d\n", err);
      break;
  }
}

