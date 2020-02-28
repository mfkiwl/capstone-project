/*
 * @file       port_platform.h
 *
 * @brief      HW specific definitions and functions for portability
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
 *             All rights reserved.
 *
 * @modified   2018 PathPartner
 */

#ifndef PORT_PLATFORM_H_
#define PORT_PLATFORM_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <string.h>
//#include "compiler.h"

#include "deca_types.h"
#include "nrf_drv_spi.h"
#include "app_util_platform.h"
#include "nrf_gpio.h"
#include "nrf_delay.h"
#include "nrf_log.h"
#include "boards.h"
#include "app_error.h"
#include "app_uart.h"

#include "TWI.h"

#ifdef TDoA_APP
#include "nrf_drv_timer.h"
#endif

/*

Note: Antenna Delay Values
The sum of the values is the TX to RX antenna delay, this should be
experimentally determined by a calibration process. Here we use a hard coded
value (expected to be a little low so a positive error will be seen on the
resultant distance estimate. For a real production application, each
device should have its own antenna delay properly calibrated to get good
precision when performing range measurements.
*/

/**< max number of test bytes to be used for tx and rx. */
#define MAX_TEST_DATA_BYTES     (15U)
#define UART_TX_BUF_SIZE         256          /**< UART TX buffer size. */
#define UART_RX_BUF_SIZE          1           /**< UART RX buffer size. */

/* Default antenna delay values for 64 MHz PRF.*/
#define TX_ANT_DLY 16456
#define RX_ANT_DLY 16456

 // must be power of 2 to create fifo succesfully
#define RX_BUF_SIZE 256

#define DATALEN1 200

// inactivity time to send UART peripheral to sleep in ticks
#define UART_INACTIVITY_TIMEOUT   (30000)

int readfromspi(uint16 headerLength,
                const uint8 *headerBuffer,
                uint32 readlength,
                uint8 *readBuffer);

int writetospi( uint16 headerLength,
                const uint8 *headerBuffer,
                uint32 bodylength,
                const uint8 *bodyBuffer);

//uint16 decamutexon(void);
//void decamutexoff(uint16 j);

//#if defined(BOARD_PCA10040)
//#define SPI_CS_PIN   17 /**< SPI CS Pin.*/
//#else
//#error "Example is not supported on that board."
//#endif

#define SPI_INSTANCE  0 /**< SPI instance index. */
///**< SPI instance. */
static const nrf_drv_spi_t spi = NRF_DRV_SPI_INSTANCE(SPI_INSTANCE);
///**< Flag used to indicate that SPI instance completed the transfer. */
static volatile bool spi_xfer_done;

/**
 * @brief SPI user event handler.
 * @param event
 */
void spi_event_handler(nrf_drv_spi_evt_t const * p_event, void * p_context);

/******************************************************************************/

 /*****************************************************************************
  *
  *                                 Types definitions
  *
  *****************************************************************************/
typedef uint64_t        uint64 ;

typedef int64_t         int64 ;

typedef bool (* app_wakeup_check_hook_t) (void);
typedef void (* acc_interrupt_hook_t) (void);

#ifndef FALSE
#define FALSE               0
#endif

#ifndef TRUE
#define TRUE                1
#endif

typedef enum {
    STAND_ALONE,
    UART_COMMAND
}application_mode_e;


/******************************************************************************
 *
 *                              port function prototypes
 *
 ******************************************************************************/

void Sleep(uint32_t Delay);
uint32_t portGetTickCount(void);

void port_wakeup_dw1000(void);

/* Function is used for initialize the SPI freq as 2MHz
 * port_set_dw1000_slowrate initialize the SPI freq as 2MHz which does init
 * state check
 */
void port_set_dw1000_slowrate(void);
void port_set_dw1000_fastrate(void);

void process_dwRSTn_irq(void);
void process_deca_irq(void);

void reset_DW1000(void);

int inittestapplication(void);
void peripherals_init(void);
void deca_uart_init(void);
uint32_t deca_uart_receive(char * buffer, size_t size);
void deca_uart_error_handle(app_uart_evt_t * p_event);
void deca_uart_transmit(char *ptr);
bool deca_uart_rx_data_ready();
void low_power(int);
void deca_uart_event_handle(app_uart_evt_t * p_event);
void RestartUART_timer();
void port_set_app_wakeup_check_hook(app_wakeup_check_hook_t);
void portSetInterruptHook(acc_interrupt_hook_t);
#ifdef TDoA_APP
void timer_event_handler(nrf_timer_event_t , void*);
#endif

#ifdef __cplusplus
}
#endif

#endif /* PORT_PLATFORM_H_ */
/*
 * Taken from the Linux Kernel
 *
 */

#ifndef _LINUX_CIRC_BUF_H
#define _LINUX_CIRC_BUF_H 1

struct circ_buf {
    char *buf;
    int head;
    int tail;
};

/* Return count in buffer.  */
#define CIRC_CNT(head,tail,size) (((head) - (tail)) & ((size)-1))

/* Return space available, 0..size-1.  We always leave one free char
   as a completely full buffer has head == tail, which is the same as
   empty.  */
#define CIRC_SPACE(head,tail,size) CIRC_CNT((tail),((head)+1),(size))

/* Return count up to the end of the buffer.  Carefully avoid
   accessing head and tail more than once, so they can change
   underneath us without returning inconsistent results.  */
#define CIRC_CNT_TO_END(head,tail,size) \
    ({int end = (size) - (tail); \
      int n = ((head) + end) & ((size)-1); \
      n < end ? n : end;})

/* Return space available up to the end of the buffer.  */
#define CIRC_SPACE_TO_END(head,tail,size) \
    ({int end = (size) - 1 - (head); \
      int n = (end + (tail)) & ((size)-1); \
      n <= end ? n : end+1;})


#endif /* _LINUX_CIRC_BUF_H  */

