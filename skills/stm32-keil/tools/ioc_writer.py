#!/usr/bin/env python3
"""Generate a STM32CubeMX .ioc file from a structured config dict."""

from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any

# ── Fixed pin mappings (no user input needed) ────────────────────────────────
PIN_MAP: dict[str, str] = {
    "TIM1_CH1": "PA8", "TIM1_CH2": "PA9", "TIM1_CH3": "PA10", "TIM1_CH4": "PA11",
    "TIM2_CH1": "PA0", "TIM2_CH2": "PA1",
    "TIM3_CH1": "PA6", "TIM3_CH2": "PA7",
    "TIM4_CH1": "PB6", "TIM4_CH2": "PB7", "TIM4_CH3": "PB8", "TIM4_CH4": "PB9",
    "I2C1_SCL": "PB6", "I2C1_SDA": "PB7",
    "I2C2_SCL": "PB10", "I2C2_SDA": "PB11",
    "USART1_TX": "PA9", "USART1_RX": "PA10",
    "USART2_TX": "PA2", "USART2_RX": "PA3",
    "USART3_TX": "PB10", "USART3_RX": "PB11",
    "ADC1_IN0": "PA0",  "ADC1_IN1": "PA1",  "ADC1_IN2": "PA2",  "ADC1_IN3": "PA3",
    "ADC1_IN4": "PA4",  "ADC1_IN5": "PA5",  "ADC1_IN6": "PA6",  "ADC1_IN7": "PA7",
    "ADC1_IN8": "PB0",  "ADC1_IN9": "PB1",
    "ADC1_IN10": "PC0", "ADC1_IN11": "PC1", "ADC1_IN12": "PC2", "ADC1_IN13": "PC3",
    "ADC1_IN14": "PC4", "ADC1_IN15": "PC5",
}

# PA0 special .ioc name
IOC_PIN_NAME: dict[str, str] = {"PA0": "PA0-WKUP", "PD0": "PD0-OSC_IN", "PD1": "PD1-OSC_OUT"}
# Signal name remapping for .ioc format
IOC_SIGNAL: dict[str, str] = {
    "TIM2_CH1": "S_TIM2_CH1_ETR", "TIM2_CH2": "S_TIM2_CH2",
    "TIM3_CH1": "S_TIM3_CH1",     "TIM3_CH2": "S_TIM3_CH2",
    "TIM1_CH1": "S_TIM1_CH1",     "TIM1_CH2": "S_TIM1_CH2",
    "TIM1_CH3": "S_TIM1_CH3",     "TIM1_CH4": "S_TIM1_CH4",
    "TIM4_CH1": "S_TIM4_CH1",     "TIM4_CH2": "S_TIM4_CH2",
    "TIM4_CH3": "S_TIM4_CH3",     "TIM4_CH4": "S_TIM4_CH4",
}
ENCODER_TIMERS = {"TIM2", "TIM3"}
HIGH_SPEED_SIGNALS = {
    "TIM1_CH1","TIM1_CH2","TIM1_CH3","TIM1_CH4",
    "USART1_TX","USART2_TX","USART3_TX",
    "I2C1_SCL","I2C1_SDA","I2C2_SCL","I2C2_SDA",
}


def _ioc_pin(pin: str) -> str:
    return IOC_PIN_NAME.get(pin, pin)


def _pwm_params(freq_hz: int, sysclk: int = 72_000_000) -> tuple[int, int]:
    """Return (prescaler, period) for given PWM freq."""
    for psc in range(0, 65536):
        period = round(sysclk / ((psc + 1) * freq_hz)) - 1
        if 0 <= period <= 65535:
            return psc, period
    return 0, sysclk // freq_hz - 1


def generate(config: dict[str, Any], out_path: Path) -> None:
    """
    config keys:
      mcu: dict  (user_name, cpn, cubemx_name, package)
      project: dict  (name, toolchain="MDK-ARM V5.32", stack=0x800, heap=0x400)
      peripherals: list of peripheral dicts (see below)
      gpio: list of {pin, label, direction, pull?}  — free GPIO
      assumptions: list[str]  — written as comments

    Peripheral dict examples:
      {"type":"pwm",  "timer":"TIM1", "channels":[1,2], "freq_hz":20000}
      {"type":"encoder", "timer":"TIM2"}
      {"type":"scheduler", "timer":"TIM4", "period_ms":1}
      {"type":"adc", "channels":[8,9,10,11,12,13,14,15], "dma":true}
      {"type":"i2c", "bus":"I2C1", "speed_hz":100000}
      {"type":"uart", "instance":"USART3", "baudrate":115200}
    """
    lines: list[str] = []
    mcu = config["mcu"]
    proj = config.get("project", {})
    peripherals = config.get("peripherals", [])
    free_gpio = config.get("gpio", [])
    assumptions = config.get("assumptions", [])

    # ── collect all pin assignments ──────────────────────────────────────────
    pin_signals: dict[str, dict] = {}  # ioc_pin_name → {signal, label, mode, speed}

    def add_pin(signal: str, label: str, mode: str = "", speed: bool = False) -> None:
        pin = PIN_MAP.get(signal, "")
        if not pin:
            raise ValueError(f"No pin mapping for signal: {signal}")
        ioc_name = _ioc_pin(pin)
        if ioc_name in pin_signals:
            existing = pin_signals[ioc_name]["label"]
            raise ValueError(f"Pin conflict on {pin}: {existing} vs {label}")
        pin_signals[ioc_name] = {
            "signal": IOC_SIGNAL.get(signal, signal),
            "label": label,
            "mode": mode,
            "speed": speed or (signal in HIGH_SPEED_SIGNALS),
        }

    # OSC
    pin_signals["PD0-OSC_IN"]  = {"signal": "RCC_OSC_IN",  "label": "", "mode": "HSE-External-Oscillator", "speed": False}
    pin_signals["PD1-OSC_OUT"] = {"signal": "RCC_OSC_OUT", "label": "", "mode": "HSE-External-Oscillator", "speed": False}

    # ── process peripherals ──────────────────────────────────────────────────
    ips = ["NVIC", "RCC", "SYS"]
    tim_configs: dict[str, dict] = {}
    adc_channels: list[int] = []
    use_dma_adc = False
    uart_configs: dict[str, dict] = {}
    i2c_configs: dict[str, dict] = {}
    scheduler_tims: list[str] = []

    for peri in peripherals:
        t = peri["type"]

        if t == "pwm":
            tim = peri["timer"]
            freq = peri.get("freq_hz", 20000)
            psc, period = _pwm_params(freq)
            channels = peri["channels"]
            labels = peri.get("labels", [f"{tim}_CH{ch}_PWM" for ch in channels])
            if tim not in ips: ips.append(tim)
            tim_configs[tim] = {"mode": "pwm", "psc": psc, "period": period, "channels": channels}
            for i, ch in enumerate(channels):
                add_pin(f"{tim}_CH{ch}", labels[i] if i < len(labels) else f"{tim}_CH{ch}_PWM")

        elif t == "encoder":
            tim = peri["timer"]
            if tim not in ENCODER_TIMERS:
                raise ValueError(f"{tim} does not support encoder mode (use TIM2 or TIM3)")
            if tim not in ips: ips.append(tim)
            tim_configs[tim] = {"mode": "encoder"}
            add_pin(f"{tim}_CH1", peri.get("label_a", f"ENC_{tim[-1]}_A"))
            add_pin(f"{tim}_CH2", peri.get("label_b", f"ENC_{tim[-1]}_B"))

        elif t == "scheduler":
            tim = peri["timer"]
            period_ms = peri.get("period_ms", 1)
            psc = 71
            period = round(72_000_000 / ((psc + 1) * (1000 / period_ms))) - 1
            if tim not in ips: ips.append(tim)
            tim_configs[tim] = {"mode": "scheduler", "psc": psc, "period": period}
            scheduler_tims.append(tim)

        elif t == "adc":
            adc_channels = peri["channels"]
            use_dma_adc = peri.get("dma", True)
            if "ADC1" not in ips: ips.insert(0, "ADC1")
            if use_dma_adc and "DMA" not in ips: ips.insert(1, "DMA")
            for ch in adc_channels:
                add_pin(f"ADC1_IN{ch}", f"LINE_ADC_{adc_channels.index(ch)}")

        elif t == "i2c":
            bus = peri["bus"]
            speed = peri.get("speed_hz", 100000)
            labels = peri.get("labels", [f"{bus}_SCL", f"{bus}_SDA"])
            if bus not in ips: ips.append(bus)
            i2c_configs[bus] = {"speed": speed}
            add_pin(f"{bus}_SCL", labels[0], mode="I2C")
            add_pin(f"{bus}_SDA", labels[1] if len(labels) > 1 else f"{bus}_SDA", mode="I2C")

        elif t == "uart":
            inst = peri["instance"]
            baud = peri.get("baudrate", 115200)
            labels = peri.get("labels", [f"{inst}_TX", f"{inst}_RX"])
            if inst not in ips: ips.append(inst)
            uart_configs[inst] = {"baudrate": baud}
            add_pin(f"{inst}_TX", labels[0], mode="Asynchronous")
            add_pin(f"{inst}_RX", labels[1] if len(labels) > 1 else f"{inst}_RX", mode="Asynchronous")

    # free GPIO
    for g in free_gpio:
        ioc_name = _ioc_pin(g["pin"])
        sig = "GPIO_Output" if g["direction"] == "output" else "GPIO_Input"
        pin_signals[ioc_name] = {
            "signal": sig,
            "label": g["label"],
            "mode": "",
            "speed": False,
            "pull": g.get("pull", "GPIO_PULLUP") if sig == "GPIO_Input" else "",
        }

    # virtual pins
    vp_pins = ["VP_SYS_VS_Systick"]
    for tim in scheduler_tims:
        vp_pins.append(f"VP_{tim}_VS_ClockSourceINT")

    all_pin_names = list(pin_signals.keys()) + vp_pins

    # ── write .ioc ───────────────────────────────────────────────────────────
    def w(*args: str) -> None:
        lines.extend(args)

    w("#MicroXplorer Configuration settings - do not modify")
    if assumptions:
        for a in assumptions:
            w(f"# ASSUMPTION: {a}")

    # ADC
    if adc_channels:
        sorted_ch = sorted(adc_channels)
        iparams = []
        for i, ch in enumerate(sorted_ch):
            iparams += [f"Rank-{i}\\#ChannelRegularConversion",
                        f"Channel-{i}\\#ChannelRegularConversion",
                        f"SamplingTime-{i}\\#ChannelRegularConversion"]
        iparams += ["NbrOfConversionFlag","NbrOfConversion","ContinuousConvMode",
                    "ExternalTrigConv","DMAContinuousRequests","master"]
        for i, ch in enumerate(sorted_ch):
            w(f"ADC1.Channel-{i}\\#ChannelRegularConversion=ADC_CHANNEL_{ch}")
        w("ADC1.ContinuousConvMode=ENABLE",
          "ADC1.DMAContinuousRequests=ENABLE",
          "ADC1.ExternalTrigConv=ADC_SOFTWARE_START",
          f"ADC1.IPParameters={','.join(iparams)}",
          f"ADC1.NbrOfConversion={len(sorted_ch)}",
          "ADC1.NbrOfConversionFlag=1")
        for i, ch in enumerate(sorted_ch):
            w(f"ADC1.Rank-{i}\\#ChannelRegularConversion={i+1}")
        for i in range(len(sorted_ch)):
            w(f"ADC1.SamplingTime-{i}\\#ChannelRegularConversion=ADC_SAMPLETIME_71CYCLES_5")
        w("ADC1.master=1")

    w("CAD.formats=", "CAD.pinconfig=", "CAD.provider=")

    # DMA
    if use_dma_adc:
        w("Dma.ADC1.0.Direction=DMA_PERIPH_TO_MEMORY",
          "Dma.ADC1.0.Instance=DMA1_Channel1",
          "Dma.ADC1.0.MemDataAlignment=DMA_MDATAALIGN_HALFWORD",
          "Dma.ADC1.0.MemInc=DMA_MINC_ENABLE",
          "Dma.ADC1.0.Mode=DMA_CIRCULAR",
          "Dma.ADC1.0.PeriphDataAlignment=DMA_PDATAALIGN_HALFWORD",
          "Dma.ADC1.0.PeriphInc=DMA_PINC_DISABLE",
          "Dma.ADC1.0.Priority=DMA_PRIORITY_HIGH",
          "Dma.ADC1.0.RequestParameters=Instance,Direction,PeriphInc,MemInc,PeriphDataAlignment,MemDataAlignment,Mode,Priority",
          "Dma.Request0=ADC1",
          "Dma.RequestsNb=1")

    w("File.Version=6", "GPIO.groupedBy=Group By Peripherals")

    # I2C
    for bus, cfg in i2c_configs.items():
        w(f"{bus}.ClockSpeed={cfg['speed']}", f"{bus}.IPParameters=ClockSpeed")

    w("KeepUserPlacement=false")

    # MCU info
    w(f"Mcu.CPN={mcu.get('cpn', mcu['user_name'])}",
      "Mcu.Family=STM32F1")
    for i, ip in enumerate(ips):
        w(f"Mcu.IP{i}={ip}")
    w(f"Mcu.IPNb={len(ips)}",
      f"Mcu.Name={mcu.get('cubemx_name', mcu['user_name'])}",
      f"Mcu.Package={mcu.get('package','LQFP64')}",
      f"Mcu.PinsNb={len(all_pin_names)}")
    for i, pname in enumerate(all_pin_names):
        w(f"Mcu.Pin{i}={pname}")
    w("Mcu.ThirdPartyNb=0",
      "Mcu.UserConstants=",
      "Mcu.UserDefines=",
      f"Mcu.UserName={mcu['user_name']}",
      "MxCube.Version=6.17.0",
      "MxDb.Version=DB.6.0.170")

    # NVIC
    w("NVIC.BusFault_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.DebugMonitor_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.HardFault_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.MemoryManagement_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.NonMaskableInt_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.PendSV_IRQn=true\\:15\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.PriorityGroup=NVIC_PRIORITYGROUP_4",
      "NVIC.SVCall_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false",
      "NVIC.SysTick_IRQn=true\\:15\\:0\\:false\\:false\\:true\\:false\\:true\\:false",
      "NVIC.UsageFault_IRQn=true\\:0\\:0\\:false\\:false\\:true\\:false\\:false\\:false")
    if use_dma_adc:
        w("NVIC.DMA1_Channel1_IRQn=true\\:2\\:0\\:false\\:false\\:true\\:true\\:true\\:true",
          "NVIC.ForceEnableDMAVector=true")
    for tim in scheduler_tims:
        w(f"NVIC.{tim}_IRQn=true\\:1\\:0\\:false\\:false\\:true\\:true\\:true\\:true")

    # ProjectManager
    pname = proj.get("name", "project")
    toolchain = proj.get("toolchain", "MDK-ARM V5.32")
    fn_order = ["SystemClock_Config-RCC", "MX_GPIO_Init-GPIO"]
    if use_dma_adc: fn_order.append("MX_DMA_Init-DMA")
    for ip in ["ADC1","I2C1","I2C2","TIM1","TIM2","TIM3","TIM4","USART1","USART2","USART3"]:
        if ip in ips: fn_order.append(f"MX_{ip}_Init-{ip}")
    fn_sort = ",".join(f"{i+1}-{item}-false-HAL-true" for i, item in enumerate(fn_order))
    w("ProjectManager.AskForMigrate=true",
      "ProjectManager.BackupPrevious=false",
      "ProjectManager.CompilerOptimize=6",
      "ProjectManager.ComputerToolchain=false",
      "ProjectManager.CoupleFile=false",
      "ProjectManager.CustomerFirmwarePackage=",
      f"ProjectManager.DeviceId={mcu['user_name']}",
      "ProjectManager.FirmwarePackage=STM32Cube FW_F1 V1.8.7",
      "ProjectManager.FreePins=false",
      "ProjectManager.HalAssertFull=false",
      f"ProjectManager.HeapSize={proj.get('heap','0x400')}",
      "ProjectManager.KeepUserCode=true",
      "ProjectManager.LastFirmware=true",
      "ProjectManager.LibraryCopy=0",
      "ProjectManager.MainLocation=Core/Src",
      "ProjectManager.NoMain=false",
      f"ProjectManager.ProjectFileName={pname}.ioc",
      f"ProjectManager.ProjectName={pname}",
      "ProjectManager.RegisterCallBack=",
      f"ProjectManager.StackSize={proj.get('stack','0x800')}",
      f"ProjectManager.TargetToolchain={toolchain}",
      "ProjectManager.ToolChainLocation=",
      "ProjectManager.UnderRoot=false",
      f"ProjectManager.functionlistsort={fn_sort}")

    # RCC
    w("RCC.ADCFreqValue=12000000",
      "RCC.ADCPresc=RCC_ADCPCLK2_DIV6",
      "RCC.AHBFreq_Value=72000000",
      "RCC.APB1CLKDivider=RCC_HCLK_DIV2",
      "RCC.APB1Freq_Value=36000000",
      "RCC.APB1TimFreq_Value=72000000",
      "RCC.APB2Freq_Value=72000000",
      "RCC.APB2TimFreq_Value=72000000",
      "RCC.FCLKCortexFreq_Value=72000000",
      "RCC.FamilyName=M",
      "RCC.HCLKFreq_Value=72000000",
      "RCC.HSE_VALUE=8000000",
      "RCC.HSE_VALUE_DIGITAL=8000000",
      "RCC.HSE_VALUE_DISPLAY=8000000",
      "RCC.HSE_VALUE_INPUT=8000000",
      "RCC.HSE_VALUE_REAL=8000000",
      "RCC.HSE_VALUE_TOOLTIP=8 MHz",
      "RCC.HSI_VALUE=8000000",
      "RCC.IPParameters=ADCFreqValue,ADCPresc,AHBFreq_Value,APB1CLKDivider,APB1Freq_Value,"
      "APB1TimFreq_Value,APB2Freq_Value,APB2TimFreq_Value,FCLKCortexFreq_Value,FamilyName,"
      "HCLKFreq_Value,HSE_VALUE,HSE_VALUE_DIGITAL,HSE_VALUE_DISPLAY,HSE_VALUE_INPUT,"
      "HSE_VALUE_REAL,HSE_VALUE_TOOLTIP,HSI_VALUE,PLLCLKFreq_Value,PLLMUL,PLLSourceVirtual,"
      "SYSCLKFreq_VALUE,SYSCLKSource,TimSysFreq_Value,USBFreq_Value,VCOOutput2Freq_Value",
      "RCC.PLLCLKFreq_Value=72000000",
      "RCC.PLLMUL=RCC_PLL_MUL9",
      "RCC.PLLSourceVirtual=RCC_PLLSOURCE_HSE",
      "RCC.SYSCLKFreq_VALUE=72000000",
      "RCC.SYSCLKSource=RCC_SYSCLKSOURCE_PLLCLK",
      "RCC.TimSysFreq_Value=72000000",
      "RCC.USBFreq_Value=72000000",
      "RCC.VCOOutput2Freq_Value=8000000")

    # SH shared signal blocks
    for ch in sorted(adc_channels):
        w(f"SH.ADCx_IN{ch}.0=ADC1_IN{ch},IN{ch}", f"SH.ADCx_IN{ch}.ConfNb=1")
    sh_map = {
        "TIM1_CH1": "TIM1_CH1,PWM Generation1 CH1",
        "TIM1_CH2": "TIM1_CH2,PWM Generation2 CH2",
        "TIM1_CH3": "TIM1_CH3,PWM Generation3 CH3",
        "TIM1_CH4": "TIM1_CH4,PWM Generation4 CH4",
        "TIM2_CH1": "TIM2_CH1,Encoder_Interface",
        "TIM2_CH2": "TIM2_CH2,Encoder_Interface",
        "TIM3_CH1": "TIM3_CH1,Encoder_Interface",
        "TIM3_CH2": "TIM3_CH2,Encoder_Interface",
        "TIM4_CH3": "TIM4_CH3,PWM Generation3 CH3",
        "TIM4_CH4": "TIM4_CH4,PWM Generation4 CH4",
    }
    used_signals = {info["signal"] for info in pin_signals.values()}
    for sig, sh_val in sh_map.items():
        ioc_sig = IOC_SIGNAL.get(sig, sig)
        if ioc_sig in used_signals:
            w(f"SH.{ioc_sig}.0={sh_val}", f"SH.{ioc_sig}.ConfNb=1")

    # TIM configs
    for tim, cfg in tim_configs.items():
        mode = cfg["mode"]
        if mode == "encoder":
            w(f"{tim}.AutoReloadPreload=TIM_AUTORELOAD_PRELOAD_DISABLE",
              f"{tim}.ClockDivision=TIM_CLOCKDIVISION_DIV1",
              f"{tim}.CounterMode=TIM_COUNTERMODE_UP",
              f"{tim}.EncoderMode=TIM_ENCODERMODE_TI12",
              f"{tim}.IC1Filter=6",
              f"{tim}.IC1Polarity=TIM_ICPOLARITY_RISING",
              f"{tim}.IC1Prescaler=TIM_ICPSC_DIV1",
              f"{tim}.IC1Selection=TIM_ICSELECTION_DIRECTTI",
              f"{tim}.IC2Filter=6",
              f"{tim}.IC2Polarity=TIM_ICPOLARITY_RISING",
              f"{tim}.IC2Prescaler=TIM_ICPSC_DIV1",
              f"{tim}.IC2Selection=TIM_ICSELECTION_DIRECTTI",
              f"{tim}.IPParameters=Prescaler,CounterMode,Period,ClockDivision,AutoReloadPreload,"
              f"EncoderMode,IC1Polarity,IC1Selection,IC1Prescaler,IC1Filter,IC2Polarity,"
              f"IC2Selection,IC2Prescaler,IC2Filter",
              f"{tim}.Period=65535",
              f"{tim}.Prescaler=0")

        elif mode == "pwm":
            chs = cfg["channels"]
            ch_params = []
            for ch in chs:
                ch_key = f"PWM\\ Generation{ch}\\ CH{ch}"
                ch_params += [f"OCMode_{ch}", f"Pulse_{ch}", f"OCPolarity_{ch}",
                              f"OCFastMode_{ch}", f"Channel-PWM Generation{ch} CH{ch}"]
            ip_params = f"Prescaler,CounterMode,Period,ClockDivision,AutoReloadPreload"
            if tim == "TIM1": ip_params += ",RepetitionCounter"
            for ch in chs:
                ch_key = f"Channel-PWM\\ Generation{ch}\\ CH{ch}"
                w(f"{tim}.{ch_key}=TIM_CHANNEL_{ch}")
            w(f"{tim}.AutoReloadPreload=TIM_AUTORELOAD_PRELOAD_DISABLE",
              f"{tim}.ClockDivision=TIM_CLOCKDIVISION_DIV1",
              f"{tim}.CounterMode=TIM_COUNTERMODE_UP",
              f"{tim}.IPParameters={ip_params}")
            for ch in chs:
                w(f"{tim}.OCFastMode_{ch}=TIM_OCFAST_DISABLE",
                  f"{tim}.OCMode_{ch}=TIM_OCMODE_PWM1",
                  f"{tim}.OCPolarity_{ch}=TIM_OCPOLARITY_HIGH",
                  f"{tim}.Pulse_{ch}=0")
            w(f"{tim}.Period={cfg['period']}", f"{tim}.Prescaler={cfg['psc']}")
            if tim == "TIM1":
                w(f"{tim}.RepetitionCounter=0")

        elif mode == "scheduler":
            w(f"{tim}.AutoReloadPreload=TIM_AUTORELOAD_PRELOAD_DISABLE",
              f"{tim}.ClockDivision=TIM_CLOCKDIVISION_DIV1",
              f"{tim}.CounterMode=TIM_COUNTERMODE_UP",
              f"{tim}.IPParameters=Prescaler,CounterMode,Period,ClockDivision,AutoReloadPreload",
              f"{tim}.Period={cfg['period']}",
              f"{tim}.Prescaler={cfg['psc']}")

    # UART configs
    for inst, cfg in uart_configs.items():
        w(f"{inst}.BaudRate={cfg['baudrate']}",
          f"{inst}.IPParameters=VirtualMode,BaudRate",
          f"{inst}.VirtualMode=VM_ASYNC")

    # Pin lines
    for pname, info in pin_signals.items():
        signal = info["signal"]
        label = info["label"]
        mode = info["mode"]
        speed = info["speed"]
        pull = info.get("pull", "")

        if signal in ("RCC_OSC_IN", "RCC_OSC_OUT"):
            w(f"{pname}.Mode={mode}", f"{pname}.Signal={signal}")
            continue

        if signal.startswith("ADCx_IN"):
            w(f"{pname}.GPIOParameters=GPIO_Label",
              f"{pname}.GPIO_Label={label}",
              f"{pname}.Locked=true",
              f"{pname}.Signal={signal}")
            continue

        gpio_params = []
        extra = []
        if signal == "GPIO_Input" and pull:
            gpio_params.append("GPIO_PuPd")
            extra.append(f"{pname}.GPIO_PuPd={pull}")
        if speed:
            gpio_params.append("GPIO_Speed")
            extra.append(f"{pname}.GPIO_Speed=GPIO_SPEED_FREQ_HIGH")
        gpio_params.append("GPIO_Label")

        if mode in ("Asynchronous", "I2C", "Serial_Wire"):
            w(f"{pname}.Mode={mode}")
        w(f"{pname}.GPIOParameters={','.join(gpio_params)}")
        w(f"{pname}.GPIO_Label={label}")
        w(*extra)
        w(f"{pname}.Locked=true", f"{pname}.Signal={signal}")

    # Virtual pins
    w("VP_SYS_VS_Systick.Mode=SysTick",
      "VP_SYS_VS_Systick.Signal=SYS_VS_Systick")
    for tim in scheduler_tims:
        w(f"VP_{tim}_VS_ClockSourceINT.Mode=Internal",
          f"VP_{tim}_VS_ClockSourceINT.Signal={tim}_VS_ClockSourceINT")

    w("board=custom", "isbadioc=false")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path, help="JSON config file")
    p.add_argument("out",    type=Path, help="Output .ioc file path")
    args = p.parse_args()
    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
        generate(cfg, args.out)
        print(f"Generated: {args.out}")
    except (ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
