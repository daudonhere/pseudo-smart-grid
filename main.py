from machine import Pin, SPI, PWM, ADC
import time
import ujson
from umqtt.simple import MQTTClient
import network
import nokia5110

WIFI_SSID = "Wokwi-GUEST"
WIFI_PASS = ""

MQTT_CLIENT_ID = "esp32-energy-monitor"
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_TOPIC = "wokwi/energy"

POWER_LIMIT = 1000.0

adc_voltage = ADC(Pin(34))
adc_current = ADC(Pin(35))
adc_voltage.atten(ADC.ATTN_11DB)
adc_current.atten(ADC.ATTN_11DB)

led_ok = Pin(26, Pin.OUT)
led_over = Pin(27, Pin.OUT)
buzzer = PWM(Pin(25))
buzzer.duty(0)

spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
lcd = nokia5110.NokiaLCD(spi, dc=Pin(17), cs=Pin(5), rst=Pin(16))
lcd.contrast(50)
lcd.clear()
lcd.show()

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(WIFI_SSID, WIFI_PASS)
while not sta.isconnected():
    time.sleep(0.2)

client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
client.connect()

energy_kwh = 0.0
last_time = time.ticks_ms()

while True:
    raw_v = adc_voltage.read()
    raw_i = adc_current.read()
    voltage = (raw_v / 4095) * 240.0
    current = (raw_i / 4095) * 10.0
    power = voltage * current
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last_time) / 1000
    last_time = now
    energy_kwh += (power * dt) / 3600000

    if power >= POWER_LIMIT:
        status = "OVERLOAD"
        led_over.on()
        led_ok.off()
        buzzer.freq(2000)
        buzzer.duty(512)
    else:
        status = "NORMAL"
        led_ok.on()
        led_over.off()
        buzzer.duty(0)

    payload = ujson.dumps({
        "voltage": round(voltage,1),
        "ampere": round(current,2),
        "watt": round(power,1),
        "kwh": round(energy_kwh,4),
        "status": status
    })
    client.publish(MQTT_TOPIC, payload)
    print(payload)

    lcd.clear()
    lcd.text("{:.0f} W".format(power),0,0)
    lcd.text("{:.1f} V".format(voltage),0,20)
    lcd.text("{:.2f} A".format(current),0,30)
    lcd.text("{:.3f} Kwh".format(energy_kwh),0,10)
    lcd.text("{}".format(status),0,40)
    lcd.show()

    time.sleep(1)
