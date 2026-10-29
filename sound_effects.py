import threading
import sys

class SoundEngine:
    """Motor de efeitos sonoros leve e nativo para Windows."""
    
    @staticmethod
    def _play_break_chime():
        try:
            import winsound
            # Melodia suave ascendente estilo zen: C5 (523Hz), E5 (659Hz), G5 (784Hz), C6 (1046Hz)
            notes = [(523, 120), (659, 120), (784, 140), (1046, 350)]
            for freq, dur in notes:
                winsound.Beep(freq, dur)
        except Exception:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    @staticmethod
    def _play_work_chime():
        try:
            import winsound
            # Melodia de foco: G5 (784Hz), E5 (659Hz), C5 (523Hz)
            notes = [(784, 100), (659, 100), (523, 300)]
            for freq, dur in notes:
                winsound.Beep(freq, dur)
        except Exception:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

    @classmethod
    def play_break_sound(cls):
        threading.Thread(target=cls._play_break_chime, daemon=True).start()

    @classmethod
    def play_work_sound(cls):
        threading.Thread(target=cls._play_work_chime, daemon=True).start()
