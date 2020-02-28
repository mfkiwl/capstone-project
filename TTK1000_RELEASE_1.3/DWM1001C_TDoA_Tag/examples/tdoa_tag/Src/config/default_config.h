/*
 * @file       default_config.h
 *
 * @brief      Default config fie for NVM initialization
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
 *             All rights reserved.
 *
 */
#ifndef DEFAULT_CONFIG_H_
#define DEFAULT_CONFIG_H_

#ifdef __cplusplus
 extern "C" {
#endif

#include <stdint.h>
#include "deca_device_api.h"
#include "deca_version.h"

/*channel*/
#define DEFAULT_CHANNEL                         2
#define DEFAULT_PRF                             DWT_PRF_64M
#define DEFAULT_TXPREAMBLENGTH                  DWT_PLEN_128
#define DEFAULT_RXPAC                           DWT_PAC8
#define DEFAULT_TXCODE                          9
#define DEFAULT_RXCODE                          9
#define DEFAULT_NSSFD                           0
#define DEFAULT_DATARATE                        DWT_BR_6M8
#define DEFAULT_PHRMODE                         DWT_PHRMODE_STD
#define DEFAULT_SFDTO                           DWT_SFDTOC_DEF
#define DEFAULT_SMARTPOWEREN                    1

/* blink settings, pause in ms */
#define DEFAULT_BLINKINTERVAL_FAST_MS     100
#define DEFAULT_BLINKINTERVAL_SLOW_MS     5000

/* blink randomness, 10 % */
#define DEFAULT_RAND                            10

/* NO IMU by default */
#define DEFAULT_DWP                             (0)
/*#define DEFAULT_DWP                           (IMU_DWP_TMP | IMU_DWP_BAT | \
                                                IMU_DWP_GPIO | IMU_DWP_MAG | \
                                                IMU_DWP_ACC | IMU_DWP_GYR |
                                                IMU_DWP_APS | IMU_DWP_ATMP)*/


/* */
#define DEFAULT_CONFIG { \
                            .dwt_config.chan= DEFAULT_CHANNEL, \
                            .dwt_config.prf = DEFAULT_PRF, \
                            .dwt_config.txPreambLength = DEFAULT_TXPREAMBLENGTH, \
                            .dwt_config.rxPAC = DEFAULT_RXPAC, \
                            .dwt_config.txCode = DEFAULT_TXCODE, \
                            .dwt_config.rxCode = DEFAULT_RXCODE, \
                            .dwt_config.nsSFD = DEFAULT_NSSFD, \
                            .dwt_config.dataRate = DEFAULT_DATARATE, \
                            .dwt_config.phrMode = DEFAULT_PHRMODE, \
                            .dwt_config.sfdTO = DEFAULT_SFDTO, \
                            .blink.interval_in_ms = DEFAULT_BLINKINTERVAL_FAST_MS, \
                            .blink.interval_slow_in_ms = DEFAULT_BLINKINTERVAL_SLOW_MS, \
                            .blink.randomness = DEFAULT_RAND,\
                            .smartPowerEn = DEFAULT_SMARTPOWEREN, \
                            .tagID = {0,0,0,0,0,0,0,0},\
                            .tagIDset = 0,\
                            .version = {DW1000_DEVICE_DRIVER_VER_STRING}, \
}

/* Application FCONFIG size */
#define NRF52_FLASH_PAGE_SIZE        0x100
#define FCONFIG_SIZE                 NRF52_FLASH_PAGE_SIZE

typedef struct {
    uint32_t    interval_in_ms;
    uint32_t    interval_slow_in_ms;
    uint8_t     randomness;
}tblink_t;

#pragma pack(push,1)
/* pointers inside this structure not allowed */
typedef struct param_block{
    dwt_config_t    dwt_config;
    tblink_t        blink;
    uint16_t        smartPowerEn;
    uint8_t         tagID[8];
    uint8_t         tagIDset;
    char            version[64];
    uint8_t         free[FCONFIG_SIZE -sizeof(tblink_t) - sizeof(dwt_config_t) -11 -64];
}param_block_t;
#pragma pack(pop)

#ifdef __cplusplus
}
#endif

#endif /* DEFAULT_CONFIG_H_ */
