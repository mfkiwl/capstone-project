/*!
*   Component name: LIS2DH12
*
*   File name: LIS2DH12.h
*
*  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
*
*  All rights reserved.
*
*  Author: Decawave, 2018
*/

// To set test mode to FIFO, include this define,
// otherwise test mode is motion detect
//#define   USE_MOTION_DETECT_FIFO_MODE

#include "nrf_drv_gpiote.h"

// Public interface functions
void vLIS2_Init(void);
uint8_t u8LIS2_TestRead(void);
void vLIS2_Task(void);
void vLIS2_PowerDown(void);
void vLIS2_EnableWakeUpDetect(void);
void vLIS2_EnableInactivityDetect(void);
void vLIS2_EnableFifoSampling(void);
bool boLIS2_InterruptOccurred(void);
void boLIS2_InterruptClear (void);
uint8_t u8LIS2_EventStatus(void);
void vInterruptHandler(void);

// Threshold event status bits
#define XLIE            0x01
#define XHIE            0x02
#define YLIE            0x04
#define YHIE            0x08
#define ZLIE            0x10
#define ZHIE            0x20

