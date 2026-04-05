import pyautogui
import time
import threading
import os
from datetime import datetime
import keyboard

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

running = False
interval = 360  # 6 minutes

# Create log folder
log_folder = "autolog"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

def send_loop():
    global running
    while True:
        if running:
            try:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)

                pyautogui.press('delete')
                time.sleep(0.2)

                pyautogui.write(message)
                time.sleep(0.2)

                pyautogui.press('enter')

                # Screenshot + log
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                screenshot_path = os.path.join(log_folder, f"{timestamp}.png")
                log_path = os.path.join(log_folder, "log.txt")

                pyautogui.screenshot(screenshot_path)

                with open(log_path, "a") as f:
                    f.write(f"[{timestamp}] Message sent | Screenshot: {screenshot_path}\n")

                print(f"[LOG] Sent at {timestamp}")

                time.sleep(interval)

            except Exception as e:
                print(f"[ERROR] {e}")
                time.sleep(2)
        else:
            time.sleep(0.5)

def toggle():
    global running
    running = not running
    print("STARTED" if running else "STOPPED")

# Hotkey (press F8 to toggle)
keyboard.add_hotkey("F8", toggle)

print("Press F8 to START/STOP")
print("Switch to Discord before starting...")

threading.Thread(target=send_loop, daemon=True).start()

keyboard.wait()