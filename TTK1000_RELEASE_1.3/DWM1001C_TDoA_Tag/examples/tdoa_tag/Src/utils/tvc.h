/*
 * @file       tvc.h
 *
 * @brief      temperature and voltage compensation utilities
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2019 (c) DecaWave Ltd.
 *             All rights reserved.
 */


#ifndef _TVC_H_
#define _TVC_H_ 1

#include "deca_device_api.h"

#ifdef __cplusplus
 extern "C" {
#endif


/* definitions for OTP */
#define OTP_VBAT_ADDRESS            (0x08)
#define OTP_TXPWR_CH5_PRF64_ADDRESS (0x19)
#define OTP_PGCNT_ADDRESS           (0x1D)
#define OTP_XTRIM_ADDRESS           (0x1E)
#define OTP_VALID(x)                (((x) != 0) && ((x) != 0xffffffff))

//#define VBAT_COMP_FACTOR      (-2.92)
//New value tested for 2.2V to 3.6V range
#define VBAT_COMP_FACTOR      (-6.76)

/* definitions for temp / vbat calibration */
#define DW_BW_TXPWR_MAX_TEMP_DIFF   2     // 2 deg / SAR_TEMP_TO_CELCIUS_CONV
#define DW_BW_TXPWR_MAX_VBAT_DIFF   17    // 0.1v * MVOLT_TO_SAR_VBAT_CONV 
#define DW_VBAT_MIN                 2200  // 2200 millivolts, i.e. 2.2V
#ifndef ABS
#define ABS(x)  (((x) < 0) ? (-(x)) : (x))
#endif

/* define structure for DW1000 device reference values */
struct ref_values {
    uint8   pgdly;
    uint32  power;
    int16   temp;
    uint16  pgcnt;
};

typedef struct ref_values ref_values_t;


/**
 * Read the tx configuration reference values from OTP.
 *
 * @param[in] ref_values_t pointer to the reference structure
 *            uint8 chan : current channel
 * @param[out] ref values
 * @return none
 */
void tvc_otp_read_txcfgref(ref_values_t* ref, uint8 chan);

/**
 * Run bandwidth and TX power compensation
 *
 * @param[in] reference structure
 * @param[out] tx_cfg values
 *
 * @return none
 */
void tvc_comp(dwt_txconfig_t* tx_cfg, ref_values_t ref, uint8 channel);


#ifdef __cplusplus
}
#endif

#endif /* _TVC_H_ */