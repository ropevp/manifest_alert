import os
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

def play_alert_sound():
    sound_path = os.path.join(os.path.dirname(__file__), 'resources', 'alert.wav')
    if os.path.exists(sound_path):
        sound = QSoundEffect()
        sound.setSource(QUrl.fromLocalFile(sound_path))
        sound.play()
