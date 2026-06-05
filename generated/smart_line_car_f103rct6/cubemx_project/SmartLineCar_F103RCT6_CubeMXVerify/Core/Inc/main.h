/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LINE_ADC_2_Pin GPIO_PIN_0
#define LINE_ADC_2_GPIO_Port GPIOC
#define LINE_ADC_3_Pin GPIO_PIN_1
#define LINE_ADC_3_GPIO_Port GPIOC
#define LINE_ADC_4_Pin GPIO_PIN_2
#define LINE_ADC_4_GPIO_Port GPIOC
#define LINE_ADC_5_Pin GPIO_PIN_3
#define LINE_ADC_5_GPIO_Port GPIOC
#define ENC_L_A_Pin GPIO_PIN_0
#define ENC_L_A_GPIO_Port GPIOA
#define ENC_L_B_Pin GPIO_PIN_1
#define ENC_L_B_GPIO_Port GPIOA
#define ENC_R_A_Pin GPIO_PIN_6
#define ENC_R_A_GPIO_Port GPIOA
#define ENC_R_B_Pin GPIO_PIN_7
#define ENC_R_B_GPIO_Port GPIOA
#define LINE_ADC_6_Pin GPIO_PIN_4
#define LINE_ADC_6_GPIO_Port GPIOC
#define LINE_ADC_7_Pin GPIO_PIN_5
#define LINE_ADC_7_GPIO_Port GPIOC
#define LINE_ADC_0_Pin GPIO_PIN_0
#define LINE_ADC_0_GPIO_Port GPIOB
#define LINE_ADC_1_Pin GPIO_PIN_1
#define LINE_ADC_1_GPIO_Port GPIOB
#define DEBUG_TX_Pin GPIO_PIN_10
#define DEBUG_TX_GPIO_Port GPIOB
#define DEBUG_RX_Pin GPIO_PIN_11
#define DEBUG_RX_GPIO_Port GPIOB
#define BUZZER_Pin GPIO_PIN_12
#define BUZZER_GPIO_Port GPIOB
#define STATUS_LED_Pin GPIO_PIN_13
#define STATUS_LED_GPIO_Port GPIOB
#define BIN1_Pin GPIO_PIN_14
#define BIN1_GPIO_Port GPIOB
#define BIN2_Pin GPIO_PIN_15
#define BIN2_GPIO_Port GPIOB
#define AIN1_Pin GPIO_PIN_6
#define AIN1_GPIO_Port GPIOC
#define AIN2_Pin GPIO_PIN_7
#define AIN2_GPIO_Port GPIOC
#define BUTTON_START_Pin GPIO_PIN_8
#define BUTTON_START_GPIO_Port GPIOC
#define BUTTON_MODE_Pin GPIO_PIN_9
#define BUTTON_MODE_GPIO_Port GPIOC
#define MOTOR_L_PWM_Pin GPIO_PIN_8
#define MOTOR_L_PWM_GPIO_Port GPIOA
#define MOTOR_R_PWM_Pin GPIO_PIN_9
#define MOTOR_R_PWM_GPIO_Port GPIOA
#define TB6612_STBY_Pin GPIO_PIN_10
#define TB6612_STBY_GPIO_Port GPIOC
#define I2C1_SCL_IMU_OLED_Pin GPIO_PIN_6
#define I2C1_SCL_IMU_OLED_GPIO_Port GPIOB
#define I2C1_SDA_IMU_OLED_Pin GPIO_PIN_7
#define I2C1_SDA_IMU_OLED_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
