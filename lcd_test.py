import I2C_LCD_driver
from time import sleep

# Initialize the I2C LCD
lcd = I2C_LCD_driver.lcd()

try:
    # Clear the display
    lcd.lcd_clear()

    # Display text on the LCD
    lcd.lcd_display_string("Hello, World!", 1)
    lcd.lcd_display_string("Raspberry Pi Test", 2)

    # Keep the text displayed until the script is interrupted
    while True:
        sleep(1)

except KeyboardInterrupt:
    # Clear the display and exit
    lcd.lcd_clear()