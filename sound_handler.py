import os
from PyQt5.QtMultimedia import QSound

def play_alert_sound():
    sound_path = os.path.join(os.path.dirname(__file__), 'resources', 'alert.wav')
    if os.path.exists(sound_path):
        QSound.play(sound_path)
