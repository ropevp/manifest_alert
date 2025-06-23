import pyttsx3

# Check available voices
engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("Available voices:")
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name} - {voice.id}")
    print(f"   Age: {voice.age}, Gender: {voice.gender}")
    print(f"   Languages: {voice.languages}")
    print()

engine.stop()
