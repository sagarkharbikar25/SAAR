from voice.record import record
import numpy as np

audio = record(5)

print("Audio length:", len(audio))
print("Mean level:", np.abs(audio).mean())

if len(audio) == 0:
    print("❌ No audio")
elif np.abs(audio).mean() < 0.0001:
    print("❌ Audio too quiet")
else:
    print("✅ Audio OK")
