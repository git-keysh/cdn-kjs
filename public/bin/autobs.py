import pyautogui
import time

message = """**🐝 Fuzzy Alt Services Available 🐝**

Offering **fuzzy alt services for any hive.** 
-# Flexible and reliable.

💸 **Payments:** Accepting *any* form of payment
🛠️ **Services:** Wide range available (just ask)

__📩 **DM <@1456334115371487284>** to get added to the **Fuzzy Service GC** for full details__

✨ **Current Hive:**
> * Level 20 Fuzzy Hive
> * Supports **Guiding Star** in **Pepper Field**
"""

time.sleep(5)

while True:
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    
    pyautogui.press('delete')
    time.sleep(0.2)
    
    pyautogui.write(message)
    time.sleep(0.2)
    
    pyautogui.press('enter')
    
    time.sleep(360)