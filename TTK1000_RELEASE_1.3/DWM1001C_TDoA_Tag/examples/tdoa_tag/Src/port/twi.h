/*!
*   Component name: TWI
*
*   File name: TWI.h
*
* Description: Two Wire Interface (I2C) public interface declarations.
*
*  Copyright 2018 (c) DecaWave Ltd, Dublin, Ireland.
*
*  All rights reserved.
*
*  Author: Decawave, 2018
*/
#include <stdint.h>

void vTWI_Init  (void);
void vTWI_Write (uint8_t u8address, uint8_t   u8data);
void vTWI_Read  (uint8_t u8subAdd,  uint8_t *pu8data);
