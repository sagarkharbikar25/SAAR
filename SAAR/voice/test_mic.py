import sounddevice as sd

print("Available input devices:\n")
for i, dev in enumerate(sd.query_devices()):
    if dev["max_input_channels"] > 0:
        print(f"{i}: {dev['name']}")
