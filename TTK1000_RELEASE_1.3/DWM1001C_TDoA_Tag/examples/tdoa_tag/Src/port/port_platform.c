/*
 * @file       port_platform.c
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

#include "sdk_config.h"
#include "port_platform.h"
#include "deca_device_api.h"
#include "nrf.h"


#include "bsp.h"
#include "nrf_drv_clock.h"
#include "app_fifo.h"
#include "nrfx_rtc.h"
#include "nrf_drv_spi.h"
#include "nrf_drv_uart.h"
#include "nrf_gpio.h"
#include "LIS2DH12.h"

#ifdef TDoA_APP
#include "nrf.h"
#include "nrf_drv_timer.h"
#endif

/******************************************************************************
 *
 *                              APP global variables
 *
 ******************************************************************************/


/******************************************************************************
 *
 *                  Port private variables and function prototypes
 *
 ******************************************************************************/
static volatile uint32_t signalResetDone;
uint32_t time32_incr = 0;
static volatile uint32_t timer_val = 0;
static volatile uint32_t timer_tick_val = 0;
static uint32_t timer_tick_inc = 1;
static app_wakeup_check_hook_t app_wakeup_check_hook = NULL;
static acc_interrupt_hook_t accInterruptHandler = NULL;
static uint32_t old_ready_pin = 1;
static bool power_down_peripherals_in_sleep = false;
static uint32_t UART_timeout;
static uint8_t spi_init = 0;
/******************************************************************************
 *
 *                              Time section
 *
 ******************************************************************************/

/* @fn    portGetTickCnt
 * @brief wrapper for to read a SysTickTimer, which is incremented with
 *        CLOCKS_PER_SEC frequency.
 *        The resolution of time32_incr is usually 1/1000 sec.
 * */
__INLINE uint32_t
portGetTickCount(void)
{
    return time32_incr;
}

/**@brief Systick handler
 *
 * @param[in] void
 */
void SysTick_Handler (void) {
        time32_incr++;
}


/* @fn    GetLPtimerTickCount
 * @brief wrapper for to read a timer_tick_val, which is incremented by the RTC ISR
 *        The resolution of timer_tick_val is roughly 1/1000 sec.
 * */
__STATIC_INLINE uint32_t GetLPtimerTickCount(void)
{
    return timer_tick_val;
}

/**
 * @brief Renew current timestamp
 * @param [out] p_timestamp - poiner to timestamp instance
 */
void start_timer(uint32_t *p_timestamp)
{
  *p_timestamp = GetLPtimerTickCount();
}

/**
 * @brief Check if timeout is expired
 * @param [in] timestamp -instance
 * @param [in] time - timeout to check
 * @return true - timeout is expired
 * false - timeout is not yet expired
 */
bool check_timer(uint32_t timestamp, uint32_t time)
{
  bool res = false;

  uint32_t temp_tick_time = GetLPtimerTickCount();

  uint32_t time_passing;
  if (temp_tick_time >= timestamp)
  {
    time_passing = temp_tick_time - timestamp;
  }
  else
  {
    time_passing = 0xffffffff - timestamp + temp_tick_time;
  }
  if (time_passing >= time)
  {
    res = true;
  }
  return res;
}

/* @fn    Sleep
 * @brief wrapper for standart delsay func
 * @param [in] delay in milliseconds
 * */
void Sleep(uint32_t delay)
{
    nrf_delay_ms(delay);
}

/******************************************************************************
 *
 *                              END OF Time section
 *
 ******************************************************************************/

/******************************************************************************
 *
 *                              Configuration section
 *
 ******************************************************************************/

/******************************************************************************
 *
 *                          End of configuration section
 *
 ******************************************************************************/


__STATIC_INLINE void nrf_gpio_cfg_input_sense_low(uint32_t pin_number, nrf_gpio_pin_pull_t pull_config)
{
    nrf_gpio_cfg(
        pin_number,
        NRF_GPIO_PIN_DIR_INPUT,
        NRF_GPIO_PIN_INPUT_CONNECT,
        pull_config,
        NRF_GPIO_PIN_S0S1,
        NRF_GPIO_PIN_SENSE_LOW);
}


__STATIC_INLINE void nrf_gpio_cfg_input_sense_high(uint32_t pin_number, nrf_gpio_pin_pull_t pull_config)
{
    nrf_gpio_cfg(
        pin_number,
        NRF_GPIO_PIN_DIR_INPUT,
        NRF_GPIO_PIN_INPUT_CONNECT,
        pull_config,
        NRF_GPIO_PIN_S0S1,
        NRF_GPIO_PIN_SENSE_HIGH);
}

__STATIC_INLINE void nrf_gpio_cfg_input_sense_none(uint32_t pin_number, nrf_gpio_pin_pull_t pull_config)
{
    nrf_gpio_cfg(
        pin_number,
        NRF_GPIO_PIN_DIR_INPUT,
        NRF_GPIO_PIN_INPUT_CONNECT,
        pull_config,
        NRF_GPIO_PIN_S0S1,
        NRF_GPIO_PIN_NOSENSE);
}
/******************************************************************************
 *
 *                          DW1000 port section
 *
 ******************************************************************************/

/* @fn      port_wakeup_dw1000
 * @brief   "slow" waking up of DW1000 using DW_CS only
 * */
void port_wakeup_dw1000(void)
{
    nrf_gpio_pin_clear(SPI_CS_PIN);
    nrf_delay_ms(1);
    nrf_gpio_pin_set(SPI_CS_PIN);
    nrf_delay_ms(7);
}

/**
 * @brief SPI user event handler.
 * @param event
 */
void spi_event_handler(nrf_drv_spi_evt_t const * p_event, void * p_context)
{
    spi_xfer_done = true;
}


void RestartUART_timer()
{
    start_timer( &UART_timeout );
}

//==============================================================================
/* @fn  port_set_app_wakeup_check_hook
 * @brief Set hook function for polling if wake-up condition is occured
 *
 * @param[in] ptr to function
 */
void portSetInterruptHook(acc_interrupt_hook_t ptr)
{
    accInterruptHandler = ptr;
}
//==============================================================================
/* @fn  port_set_app_wakeup_check_hook
 * @brief Set hook function for polling if wake-up condition is occured
 *
 * @param[in] ptr to function
 */
void port_set_app_wakeup_check_hook(app_wakeup_check_hook_t ptr)
{
    app_wakeup_check_hook = ptr;
}

int readfromspi(uint16 headerLength,
                const uint8 *headerBuffer,
                uint32 readlength,
                uint8 *readBuffer)
{
    uint8 idatabuf[DATALEN1]={0};
    uint8 itempbuf[DATALEN1]={0};

    uint8 * p1;
    uint32 idatalength=0;

    memset(idatabuf, 0, DATALEN1);
    memset(itempbuf, 0, DATALEN1);

    p1=idatabuf;
    memcpy(p1,headerBuffer, headerLength);

    p1 += headerLength;
    memset(p1,0x00,readlength);

    idatalength= headerLength + readlength;

    spi_xfer_done = false;
    nrf_drv_spi_transfer(&spi, idatabuf, idatalength, itempbuf, idatalength);
    while(!spi_xfer_done);
    p1=itempbuf + headerLength;
    memcpy(readBuffer, p1, readlength);

    return 0;
}


int writetospi( uint16 headerLength,
                const uint8 *headerBuffer,
                uint32 bodylength,
                const uint8 *bodyBuffer)
{
    uint8 idatabuf[DATALEN1]={0};
    uint8 itempbuf[DATALEN1]={0};

    uint8 * p1;
    uint32 idatalength=0;

    memset(idatabuf, 0, DATALEN1);
    memset(itempbuf, 0, DATALEN1);

    p1=idatabuf;
    memcpy(p1,headerBuffer, headerLength);
    p1 += headerLength;
    memcpy(p1,bodyBuffer,bodylength);

    idatalength= headerLength + bodylength;

    spi_xfer_done = false;
    nrf_drv_spi_transfer(&spi, idatabuf, idatalength, itempbuf, idatalength);
    while(!spi_xfer_done);

    return 0;
}

//------------------------------other---------------------------

#define NRF_DRV_SPI_DEFAULT_CONFIG_2M(id)                    \
{                                                            \
    .sck_pin      = CONCAT_3(SPI, id, _CONFIG_SCK_PIN),      \
    .mosi_pin     = CONCAT_3(SPI, id, _CONFIG_MOSI_PIN),     \
    .miso_pin     = CONCAT_3(SPI, id, _CONFIG_MISO_PIN),     \
    .ss_pin       = NRF_DRV_SPI_PIN_NOT_USED,                \
    .irq_priority = CONCAT_3(SPI, id, _CONFIG_IRQ_PRIORITY), \
    .orc          = 0xFF,                                    \
    .frequency    = NRF_DRV_SPI_FREQ_2M,                     \
    .mode         = NRF_DRV_SPI_MODE_0,                      \
    .bit_order    = NRF_DRV_SPI_BIT_ORDER_MSB_FIRST,         \
}


#define NRF_DRV_SPI_DEFAULT_CONFIG_8M(id)                    \
{                                                            \
    .sck_pin      = CONCAT_3(SPI, id, _CONFIG_SCK_PIN),      \
    .mosi_pin     = CONCAT_3(SPI, id, _CONFIG_MOSI_PIN),     \
    .miso_pin     = CONCAT_3(SPI, id, _CONFIG_MISO_PIN),     \
    .ss_pin       = NRF_DRV_SPI_PIN_NOT_USED,                \
    .irq_priority = CONCAT_3(SPI, id, _CONFIG_IRQ_PRIORITY), \
    .orc          = 0xFF,                                    \
    .frequency    = NRF_DRV_SPI_FREQ_8M,                     \
    .mode         = NRF_DRV_SPI_MODE_0,                      \
    .bit_order    = NRF_DRV_SPI_BIT_ORDER_MSB_FIRST,         \
}

// this is modified function from SDK. TODO - check if it could be replaced by normal SDK function
__STATIC_INLINE void nrf_gpio_cfg_output2(uint32_t pin_number)
{
    nrf_gpio_cfg(
            pin_number,
            NRF_GPIO_PIN_DIR_OUTPUT,
            NRF_GPIO_PIN_INPUT_DISCONNECT,
            NRF_GPIO_PIN_PULLUP,
            NRF_GPIO_PIN_S0S1,
            NRF_GPIO_PIN_NOSENSE);
}

/* @fn      reset_DW1000
 * @brief   DW_RESET pin on DW1000 has 2 functions
 *          In general it is output, but it also can be used to reset the
 *          digital part of DW1000 by driving this pin low.
 *          Note, the DW_RESET pin should not be driven high externally.
 * */
void reset_DW1000(void)
{
    nrf_gpio_cfg_output2(DW1000_RST);
    nrf_gpio_pin_clear(DW1000_RST);
    nrf_delay_ms(200);
    nrf_gpio_pin_set(DW1000_RST);
    nrf_delay_ms(50);
    nrf_gpio_cfg_input(DW1000_RST, NRF_GPIO_PIN_NOPULL);
    nrf_delay_ms(2);
}

/* @fn      port_set_dw1000_slowrate
 * @brief   Function is used for re-initialize the SPI freq as 2MHz which does
 *          init state check
 * */
void port_set_dw1000_slowrate(void)
{
    if(spi_init != 0){
        nrf_drv_spi_uninit(&spi);
        spi_init = 0;
    }

    nrf_drv_spi_config_t  spi_config = \
           NRF_DRV_SPI_DEFAULT_CONFIG_2M(SPI_INSTANCE);
    spi_config.ss_pin = SPI_CS_PIN;
    APP_ERROR_CHECK( nrf_drv_spi_init(&spi, &spi_config, spi_event_handler, NULL) );
    spi_init = 1;
    nrf_delay_ms(2);
}

/* @fn      port_set_dw1000_fastrate
 * @brief   set 8MHz
 *
 * */
void port_set_dw1000_fastrate(void)
{
    if(spi_init != 0){
        nrf_drv_spi_uninit(&spi);
        spi_init = 0;
    }

    nrf_drv_spi_config_t  spi_config = \
        NRF_DRV_SPI_DEFAULT_CONFIG_8M(SPI_INSTANCE);
    spi_config.ss_pin = SPI_CS_PIN;
    // TODO check the behavior of nrf_drv_spi_init2 in previous project
    // nrf_drv_spi_init returns error when SPI is already inited, so deinit it first
    //nrf_drv_spi_uninit(&spi);
    APP_ERROR_CHECK( nrf_drv_spi_init(&spi, &spi_config, spi_event_handler, NULL) );
    spi_init = 1;
    nrf_delay_ms(2);
}

void deca_sleep(unsigned int time_ms)
{
    nrf_delay_ms(time_ms);
}

#ifdef TDoA_APP

const nrfx_rtc_t rtc = NRFX_RTC_INSTANCE(0); /**< Declaring an instance of nrf_drv_rtc for RTC0. */

/** @brief: Function for handling the RTC0 interrupts.
 * Triggered on TICK and COMPARE0 match.
 */
static void rtc_handler(nrfx_rtc_int_type_t int_type)
{
    if (int_type == NRFX_RTC_INT_COMPARE0)
    {
        timer_val++;
    }
    else if (int_type == NRFX_RTC_INT_TICK)
    {
        timer_tick_val += timer_tick_inc;
        nrf_rtc_event_clear(rtc.p_reg, NRF_RTC_EVENT_TICK);
        uint32_t ready_pin = nrf_gpio_pin_read( READY_PIN ); 
        if ( old_ready_pin == 0 && ready_pin == 1 ) {
            if ( accInterruptHandler != NULL ) {
                accInterruptHandler();
            }
        }
        old_ready_pin = ready_pin;    
        if ( nrf_gpio_pin_latch_get(RX_PIN_NUMBER) ) {
            nrf_gpio_cfg_input_sense_none(RX_PIN_NUMBER, NRF_GPIO_PIN_NOPULL);
            power_down_peripherals_in_sleep = false;
            RestartUART_timer(0);
            nrf_gpio_pin_latch_clear(RX_PIN_NUMBER);
            // waking up from sleep in order to reenable UART
            timer_val++;
        }
    }
}

/** @brief Function starting the internal LFCLK XTAL oscillator.
 */
static void lfclk_config(void)
{
    ret_code_t err_code = nrf_drv_clock_init();
    APP_ERROR_CHECK(err_code);

    nrf_drv_clock_lfclk_request(NULL);
}

/** @brief Function initialization and configuration of RTC driver instance.
 */
static void rtc_config(void)
{
    uint32_t err_code;

    //Initialize RTC instance
    nrfx_rtc_config_t config = NRFX_RTC_DEFAULT_CONFIG;
    config.prescaler = 4095;
    err_code = nrfx_rtc_init(&rtc, &config, rtc_handler);
    APP_ERROR_CHECK(err_code);

    //Enable tick event & interrupt
    nrfx_rtc_tick_enable(&rtc,true);

    //Set compare channel to trigger interrupt after COMPARE_COUNTERTIME seconds
    err_code = nrfx_rtc_cc_set(&rtc,0,5 * 8,true);
    APP_ERROR_CHECK(err_code);

    //Power on RTC instance
    nrfx_rtc_enable(&rtc);
}

void eternal_sleep()
{
    do { __WFE(); } while(1);
}

void low_power(int delay)
{
    uint32_t time_ticks;
    ret_code_t err_code = NRF_SUCCESS;

    nrf_drv_spi_t spi = NRF_DRV_SPI_INSTANCE(0);
    nrf_drv_spi_uninit(&spi);
    spi_init = 0;

    if ( !power_down_peripherals_in_sleep ) {
        if ( check_timer( UART_timeout, UART_INACTIVITY_TIMEOUT ) ) {
            power_down_peripherals_in_sleep = true;
        }
    }
    
    bool need_to_wakeup_after_sleep = false;
    if ( power_down_peripherals_in_sleep ) {
        need_to_wakeup_after_sleep = true;
        // disabling UART - may be a bug in the Nordic chip but the 500uA in sleep is unexpectedly large current
        app_uart_close();

        // RX_PIN_NUMBER is now latched 
        nrf_gpio_cfg_input_sense_low(RX_PIN_NUMBER, NRF_GPIO_PIN_NOPULL);
    }

    //Initialize RTC instance
    nrfx_rtc_config_t config = NRFX_RTC_DEFAULT_CONFIG;
    // rougly one tick per millisecond for small delays and 64ms for large ones in order to minimize power waste in ISR
    if ( delay > 1000 ) {
        config.prescaler = 2111;
        delay >>= 6;
        timer_tick_inc = 1<<6;
    }else{
        config.prescaler = 32;
        timer_tick_inc = 1;
    }
    err_code = nrfx_rtc_init(&rtc, &config, rtc_handler);
    APP_ERROR_CHECK(err_code);

    //Enable tick event & interrupt
    nrfx_rtc_tick_enable(&rtc,true);

    //Set compare channel to trigger interrupt after COMPARE_COUNTERTIME seconds
    err_code = nrfx_rtc_cc_set( &rtc, 0, delay, true );
    APP_ERROR_CHECK(err_code);
    // clear the counter - the only way to do it, because enable/disable, init/uninit events do not clear this register
    nrfx_rtc_counter_clear( &rtc );

    timer_val = 0;
    //Power on RTC instance
    nrfx_rtc_enable(&rtc);

    while( timer_val == 0 ) {
        __WFI();
        if ( app_wakeup_check_hook != NULL ) {
            if ( app_wakeup_check_hook() ) {
                break;
            }
        }
    }

    if ( need_to_wakeup_after_sleep ) {
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
        APP_UART_INIT(&comm_params,
                    deca_uart_event_handle,
                    APP_IRQ_PRIORITY_LOW,
                    err_code);
    }

    timer_val=0;

    // Enable SysTick Interrupt
    SysTick->CTRL |= SysTick_CTRL_TICKINT_Msk;

    // Disable Timer.
    nrfx_rtc_tick_disable(&rtc);
    nrfx_rtc_uninit(&rtc);
//    nrf_drv_timer_disable(&TIMER_Wakeup);
}
#endif
//
/******************************************************************************
 *
 *                          End APP port section
 *
 ******************************************************************************/



/******************************************************************************
 *
 *                              IRQ section
 *
 ******************************************************************************/
/*! ----------------------------------------------------------------------------
 * Function: decamutexon()
 *
 * Description: This function should disable interrupts.
 *
 *
 * input parameters: void
 *
 * output parameters: uint16
 * returns the state of the DW1000 interrupt
 */

decaIrqStatus_t decamutexon(void)
{
    uint32_t s = NVIC_GetPendingIRQ((IRQn_Type)DW1000_IRQ);
    if(s)
    {
        NVIC_DisableIRQ((IRQn_Type)DW1000_IRQ);
    }
    return 0;
}
///*! ----------------------------------------------------------------------------
// * Function: decamutexoff()
// *
// * Description: This function should re-enable interrupts, or at least restore
// *              their state as returned(&saved) by decamutexon
// * This is called at the end of a critical section
// *
// * input parameters:
// * @param s - the state of the DW1000 interrupt as returned by decamutexon
// *
// * output parameters
// *
// * returns the state of the DW1000 interrupt
// */
void decamutexoff(decaIrqStatus_t j)
{
    if(j)
    {
        NVIC_EnableIRQ((IRQn_Type)DW1000_IRQ);
    }
}

/******************************************************************************
 *
 ******************************************************************************/

