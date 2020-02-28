/*
 * @file       config.c
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
 *             All rights reserved.
 *
 */
#include <string.h>
#include "instance.h"
#include "nrf_nvmc.h"
#include "default_config.h"

/* The location of FConfig and defaultConfig are defined in Linker script file and project configuration options */

/* Changeble block of parameters in the NVM */
const param_block_t FConfig __attribute__((section(".fConfig"))) \
                                   __attribute__((aligned(NRF52_FLASH_PAGE_SIZE))) = DEFAULT_CONFIG;

/* Application default constant parameters block in the NVM. Never changes. Used for Restore command ONLY. */
const param_block_t defaultFConfig __attribute__((section(".default_config"))) \
                                   __attribute__((aligned(NRF52_FLASH_PAGE_SIZE))) = DEFAULT_CONFIG;

/* Run-Time config parameters. */
static param_block_t tmpConfig __attribute__((aligned(NRF52_FLASH_PAGE_SIZE)));


/* IMPLEMENTATION */
/* Exported functions  */

void load_bssConfig(void)
{
    memcpy(&tmpConfig, &FConfig, sizeof(tmpConfig));

    app.pConfig = &tmpConfig;
}


param_block_t *get_pbssConfig(void)
{
  return app.pConfig;
}


/* @brief    Writes buffer to the nonvolatile config location &FConfig
 * assumes data fold to page
 *
 */
void save_bssConfig(param_block_t * pbuf)
{
    __disable_irq();
    nrf_nvmc_page_erase((uint32_t)&FConfig);

    nrf_nvmc_write_bytes((uint32_t)&FConfig, (uint8_t*)pbuf, FCONFIG_SIZE);

    __enable_irq();
}


/* @fn       restore_nvm_fconfig
 * @brief    init main program run-time configuration parameters from NVM
 *           assumes that memory model .text and .bss the same
 * */
void restore_nvm_fconfig(void)
{    
    __disable_irq();

    nrf_nvmc_page_erase((uint32_t)&FConfig);
    nrf_nvmc_write_bytes((uint32_t)&FConfig,  (const uint8_t *)&defaultFConfig, FCONFIG_SIZE);

    load_bssConfig();

    __enable_irq();

}
/* end of config.c */
