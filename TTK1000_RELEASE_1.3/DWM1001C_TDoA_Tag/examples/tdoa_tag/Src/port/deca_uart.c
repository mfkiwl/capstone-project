/*
 * @file       deca_uart.c
 *
 * @brief      HW specific definitions and functions for UART Interface
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
 *             All rights reserved.
 *
 * @modified   2018 PathPartner
 */

#include "boards.h"
#include "port_platform.h"
#include "nrf_uart.h"
#include "app_uart.h"
#include "app_fifo.h"
#include "nrf_drv_clock.h"
#include "twi.h"

/******************************************************************************
 *
 *                              APP global variables
 *
 ******************************************************************************/
static uint8_t rx_buf[RX_BUF_SIZE];              
static app_fifo_t m_rx_fifo; 
static bool uart_rx_data_ready = false;

/******************************************************************************
 *
 *                              Uart Configuration
 *
 ******************************************************************************/

/* @fn  peripherals_init
 *
 * @param[in] void
 * */
void peripherals_init(void)
{
    ret_code_t err_code = NRF_SUCCESS;

    err_code = nrf_drv_clock_init();

     /* configure systick to 1ms */
    SystemCoreClockUpdate ();
    SysTick_Config(SystemCoreClock/1000);

     /* Setup DW1000 IRQ pin */
    nrf_gpio_cfg_input(DW1000_IRQ, NRF_GPIO_PIN_NOPULL);     //irq

    nrf_gpio_cfg_input(RX_PIN_NUMBER, NRF_GPIO_PIN_PULLUP);

    nrf_gpio_cfg_input(READY_PIN, NRF_GPIO_PIN_NOPULL);

    // Start LF 32k crystal
    nrf_drv_clock_lfclk_request(NULL);

     /* Function for initializing the UART module. */
    deca_uart_init();

    // TWI interface to accelerometer
    vTWI_Init();

}

/* @fn  uart_error_handle
 *
 * @param[in] void
 * */

bool deca_uart_rx_data_ready()
{
    return uart_rx_data_ready;
}

void deca_uart_event_handle(app_uart_evt_t * p_event)
{
    if (p_event->evt_type == APP_UART_COMMUNICATION_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_communication);
    }
    if (p_event->evt_type == APP_UART_FIFO_ERROR)
    {
        APP_ERROR_HANDLER(p_event->data.error_code);
    }
    if (p_event->evt_type == APP_UART_DATA)
    {
        // echoing symbol
        uint32_t error = app_uart_put( p_event->data.value );

        RestartUART_timer();

        if ( !uart_rx_data_ready  ) {
            if ( p_event->data.value == '\r' ) {
                uart_rx_data_ready = true;
                app_uart_put( 0 );
            }else{
                error = app_fifo_put(&m_rx_fifo, p_event->data.value );
                if ( error == NRF_ERROR_NO_MEM ) { 
                    // buffer full, lets signal app to proceed it
                    uart_rx_data_ready = true;
                }
            }
        }
    }
}

/* @fn  deca_uart_init
 *
 * @brief Function for initializing the UART module.
 *
 * @param[in] void
 * */
void deca_uart_init(void)
{
    uint32_t err_code;
    const app_uart_comm_params_t comm_params =
    {
        RX_PIN_NUMBER,
        TX_PIN_NUMBER,
        RTS_PIN_NUMBER,
        CTS_PIN_NUMBER,
        APP_UART_FLOW_CONTROL_DISABLED,
        false,
        UART_BAUDRATE_BAUDRATE_Baud115200
    };
    err_code = app_fifo_init(&m_rx_fifo, rx_buf, sizeof (rx_buf));
    APP_ERROR_CHECK(err_code);

    APP_UART_INIT(&comm_params,
                    deca_uart_event_handle,
                    APP_IRQ_PRIORITY_LOW,
                    err_code);
    APP_ERROR_CHECK(err_code);

    RestartUART_timer();
}

void port_tx_msg(char *ptr, int len)
{
    for(int i=0; i<len; ++i)
    {
        while(app_uart_put(ptr[i]) != NRF_SUCCESS);
    }
}

/* @fn  deca_uart_transmit
 *
 * @brief Function for transmitting data on UART
 *
 * @param[in] ptr Pointer is contain base address of data.
 * */
void deca_uart_transmit(char *ptr)
{
    uint32_t bit=0;
    for(bit=0;ptr[bit] != '\0';bit++)
    {
        while(app_uart_put(ptr[bit]) != NRF_SUCCESS);
    }
    while(app_uart_put('\n') != NRF_SUCCESS);
    while(app_uart_put('\r') != NRF_SUCCESS);
}
/* @fn  deca_uart_receive
 *
 * @brief Function for receive data from UART buffer and store into rx_buf - either full or null-terminated if partial
 *        
 * @param[in] address to buffer, max buffer size
 * @param[out] actual number of bytes in buffer
 * */
uint32_t deca_uart_receive(char * buffer, size_t size)
{
    uint32_t count = 0;
    uint32_t err_code;
    do {
        err_code = app_fifo_get( &m_rx_fifo, buffer);
        buffer++;
        count++;
    } while ( err_code == NRF_SUCCESS && count < size );
    if ( count == size ) {
        *--buffer = 0;
    }else{
        *buffer = 0;
    }
    err_code = app_uart_put( '\n' );
    app_fifo_flush( &m_rx_fifo );
    uart_rx_data_ready = false;
    return count;
}

/****************************************************************************//**
 *
 *                          End of UART Configuration
 *
 *******************************************************************************/
