/*
 * @file       tvc.c
 *
 * @brief      temperature and voltage compensation utilities
 *
 * @author     Decawave Software
 *
 * @attention  Copyright 2019 (c) DecaWave Ltd.
 *             All rights reserved.
 */

#include "port_platform.h"
#include "deca_device_api.h"
#include "deca_regs.h"
#include "deca_types.h"
#include "deca_param_types.h"
#include "tvc.h"

uint32 tvc_calcpowertempvbatadj(uint8 channel, uint32 ref_powerreg, int delta_temp, uint8 raw_voltage);
extern uint32 _dwt_computetxpowersetting(uint32 ref_powerreg, int32 power_adj);

/* Use "Golden values" when the DW1000 device is not calibrated during production */
/* Depends on channel. TxPower/ PGdelay values in OTP are valid only for channel 5 for DWM1001 */ 
static ref_values_t ref_goldenval[6] = {
    // Place holder
    { 
        0x0,
        0x0,
        0x0,
        0x0,
    },
    // Place holder
    { 
        0x0,
        0x0,
        0x0,
        0x0,
    },
    // Channel 2 
    {    
         0xc2,           /* PG_DELAY */
         0x07274767,     /* Power */
         0x81,           /* Temp */
         0x369           /* PG_COUNT */
    },
    // Place holder
    { 
        0x0,
        0x0,
        0x0,
        0x0,
    },
    // Place holder
    { 
        0x0,
        0x0,
        0x0,
        0x0,
    },
    // Channel 5
    {    
         0xb5,           /* PG_DELAY */
         0x25456585,     /* Power */
         0x81,           /* Temp */
         0x369           /* PG_COUNT */
    }
};

static const uint8 ref_vbat_goldenval = 0x7e;

/* Local parameter to store OTP vbat value*/
static uint8 ref_vbat;

/**
 * Read the tx configuration reference values from OTP.
 *
 * @param[in] ref_values_t pointer to the reference structure
 * @param[out] ref values
 * @return none
 */
void tvc_otp_read_txcfgref(ref_values_t* ref, uint8 chan)
{
  /* OTP reading: transmission parameters */
  uint32 val[4];

  if(chan == 5)
  {
      /* OTP reading: from reference registers, should be calibrated during production test */
      dwt_otpread(OTP_TXPWR_CH5_PRF64_ADDRESS, val, 1);
      dwt_otpread(OTP_PGCNT_ADDRESS, val+1, 1);
      dwt_otpread(OTP_XTRIM_ADDRESS, val+2, 1);
      dwt_otpread(OTP_VBAT_ADDRESS,  val+3, 1);

      if (OTP_VALID(val[0]) && OTP_VALID(val[1]) && OTP_VALID(val[2]) && OTP_VALID(val[3])) {
          ref->power = val[0];
          ref->pgcnt = (val[1] >> 16) & 0xffff;
          ref->temp  = val[1] & 0xffff;
          ref->pgdly = (val[2] >> 16) & 0xff;
          ref_vbat  = val[3];
      } else {
          /*OTP values are not valid. Use golden values instead. */
          ref->power = ref_goldenval[chan].power;
          ref->pgcnt = ref_goldenval[chan].pgcnt;
          ref->temp  = ref_goldenval[chan].temp;
          ref->pgdly = ref_goldenval[chan].pgdly;    
          ref_vbat  = ref_vbat_goldenval;
      }
  } else if (chan == 2) {
      ref->power = ref_goldenval[chan].power;
      ref->pgcnt = ref_goldenval[chan].pgcnt;
      ref->temp  = ref_goldenval[chan].temp;
      ref->pgdly = ref_goldenval[chan].pgdly;    
      ref_vbat  = ref_vbat_goldenval;
  } else {
      // Error channel must be either 2 or 5 with DWM1001 TDoA Tag project
  }
}

/**
 * Run bandwidth and TX power compensation
 *
 * @return none
 */
void tvc_comp(dwt_txconfig_t* tx_cfg, ref_values_t ref, uint8 channel)
{
  uint8 curr_temp;
  uint8 curr_vbat;
  int32_t delta_temp;
  uint8 pgdly;
  uint16_t tempvbat;
  uint32_t power;

  /* Only do compensation when the reference registers are set during production */
  if ((ref.power) && (ref.pgcnt) && (ref.temp)) 
  {
    /* Set SPI clock to 2MHz */
    port_set_dw1000_slowrate();         

    /* Read DW1000 IC temperature and supply volgate for compensation procedure. */
    tempvbat = dwt_readtempvbat(0);    
    curr_vbat = tempvbat & 0xff;
    curr_temp = (tempvbat >> 8) & 0xff;

    /* Calculate temperature difference in raw value unit */
    delta_temp = (int32_t)((dwt_convertrawtemperature(curr_temp) - (float)(ref.temp)) / SAR_TEMP_TO_CELCIUS_CONV);

    /* Calculate the corrected bandwidth setting */
    pgdly = dwt_calcbandwidthtempadj(ref.pgcnt);

    /* Calculate the corrected tx power setting */
    power = tvc_calcpowertempvbatadj(channel, ref.power, delta_temp, curr_vbat);

    /* Adjust the tx power register to suit the latest temp & vbat */
    tx_cfg->PGdly = pgdly;
    tx_cfg->power = power;    
    //dwt_configuretxrf(tx_cfg);

    /* Set SPI clock to 8MHz */
    port_set_dw1000_fastrate();
  }
}


/*! ------------------------------------------------------------------------------------------------------------------
 * @fn tvc_calcpowertempadj()
 *
 * @brief this function determines the corrected power setting (TX_POWER setting) for the
 * DW1000 which changes over temperature.
 *
 * Note: only ch2 or ch5 are supported, if other channel is used - the COMP factor should be calculated and adjusted
 *
 * input parameters:
 * @param channel - uint8 - the channel at which compensation of power level will be applied: 2 or 5
 * @param delta_temp - int - the difference between current ambient temperature (raw value units)
 *                                  and the temperature at which reference measurements were made (raw value units)

 * output parameters: None
 *
 * returns: (uint32) The corrected TX_POWER register value
 */
int8 tvc_calcpowertempadj(uint8 channel, int delta_temp)
{
    int8 delta_power;
    int negative = 0;

    if(delta_temp < 0)
    {
        negative = 1;
        delta_temp = -delta_temp; //make (-)ve into (+)ve number
    }

    // Calculate the expected power differential at the current temperature
    if(channel == 5)
    {
        delta_power = ((delta_temp * TEMP_COMP_FACTOR_CH5) >> 12); //>>12 is same as /4096
    }
    else if(channel == 2)
    {
        delta_power = ((delta_temp * TEMP_COMP_FACTOR_CH2) >> 12); //>>12 is same as /4096
    }
    else
    {
        delta_power = 0;
    }

    if(negative == 1)
    {
        delta_power = -delta_power; //restore the sign
    }
    return delta_power;
}

/*! ------------------------------------------------------------------------------------------------------------------
 * @fn tvc_calcpowervbatadj()
 *
 * @brief this function determines the power change for the DW1000 which changes over voltage.
 *
 * input parameters:
 * @param raw_voltage   - uint8   - the current supply voltage (raw value units)

 * output parameters: None
 *
 * returns: (int8) The TX_POWER need to change (in 0.5dB steps)
 */

 int8 tvc_calcpowervbatadj(uint8 raw_voltage)
{
    int8 delta_power;
    
    delta_power = (int8)((float)(raw_voltage - ref_vbat) * SAR_VBAT_TO_VOLT_CONV * VBAT_COMP_FACTOR) ;
    
    return delta_power;
}


/*! ------------------------------------------------------------------------------------------------------------------
 * @fn dwt_calcpowertempvbatadj()
 *
 * @brief this function determines the corrected power setting (TX_POWER setting) for the
 * DW1000 which changes over temperature and voltage.
 *
 * Note: only ch2 or ch5 are supported, if other channel is used - the COMP factor should be calculated and adjusted
 *
 * input parameters:
 * @param channel       - uint8   - the channel at which compensation of power level will be applied: 2 or 5
 * @param ref_powerreg  - uint32  - the TX_POWER register value recorded when reference measurements were made
 * @param delta_temp    - int     - the difference between current ambient temperature (raw value units)
 *                                  and the temperature at which reference measurements were made (raw value units)
 * @param raw_voltage   - uint8   - the current supply voltage (raw value units)
 * output parameters: None
 *
 * returns: (uint32) The corrected TX_POWER register value
 */
 uint32 tvc_calcpowertempvbatadj(uint8 channel, uint32 ref_powerreg, int delta_temp, uint8 raw_voltage)
{
    int8 delta_power;

    delta_power =  tvc_calcpowervbatadj(raw_voltage);
    delta_power += tvc_calcpowertempadj(channel, delta_temp);

    if(delta_power == 0)
    {
        return ref_powerreg ; //no change to power register
    }

    // Adjust the TX_POWER register value
    return _dwt_computetxpowersetting(ref_powerreg, delta_power);
}