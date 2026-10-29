from enum import Enum
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from config import PomodoroConfig

class SessionType(Enum):
    WORK = "Trabalho"
    SHORT_BREAK = "Pausa Curta"
    LONG_BREAK = "Pausa Longa"

class TimerStatus(Enum):
    IDLE = "Parado"
    RUNNING = "Em Execução"
    PAUSED = "Pausado"

class PomodoroEngine(QObject):
    # Sinais emitidos pelo motor
    tick = pyqtSignal(int, int, str)               # remaining_secs, total_secs, mm:ss
    state_changed = pyqtSignal(SessionType, int)    # current_session, cycle_count
    status_changed = pyqtSignal(TimerStatus)       # running/paused/idle
    break_started = pyqtSignal(SessionType, int, int) # session_type, total_secs, cycle_count
    work_started = pyqtSignal(int)                 # cycle_count

    def __init__(self, config: PomodoroConfig):
        super().__init__()
        self.config = config
        self.session_type = SessionType.WORK
        self.status = TimerStatus.IDLE
        self.cycle_count = 1  # 1 até config.cycles_before_long_break
        
        self.total_seconds = self.config.work_duration_min * 60
        self.remaining_seconds = self.total_seconds
        
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    def set_config(self, new_config: PomodoroConfig):
        self.config = new_config
        if self.status == TimerStatus.IDLE:
            self.reset()

    @property
    def is_in_break(self) -> bool:
        return self.session_type in (SessionType.SHORT_BREAK, SessionType.LONG_BREAK)

    @property
    def current_total_seconds(self) -> int:
        return self.total_seconds

    def format_time(self, seconds: int) -> str:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def start(self):
        if self.status == TimerStatus.IDLE:
            self.total_seconds = self._get_duration_for_current_session()
            self.remaining_seconds = self.total_seconds
            self.status = TimerStatus.RUNNING
            self._timer.start()
            self.status_changed.emit(self.status)
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            if self.is_in_break:
                self.break_started.emit(self.session_type, self.total_seconds, self.cycle_count)
            else:
                self.work_started.emit(self.cycle_count)
        elif self.status == TimerStatus.PAUSED:
            self.status = TimerStatus.RUNNING
            self._timer.start()
            self.status_changed.emit(self.status)

    def pause(self):
        if self.status == TimerStatus.RUNNING:
            self._timer.stop()
            self.status = TimerStatus.PAUSED
            self.status_changed.emit(self.status)

    def toggle_play_pause(self):
        if self.status == TimerStatus.RUNNING:
            self.pause()
        else:
            self.start()

    def reset(self):
        self._timer.stop()
        self.status = TimerStatus.IDLE
        self.total_seconds = self._get_duration_for_current_session()
        self.remaining_seconds = self.total_seconds
        self.status_changed.emit(self.status)
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))

    def extend_time(self, seconds: int = 120):
        """Adiciona mais tempo à sessão atual (ex: +2 minutos de pausa)."""
        self.remaining_seconds += seconds
        self.total_seconds += seconds
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))

    def skip(self):
        """Pula para a próxima fase imediatamente."""
        self._timer.stop()
        self._advance_to_next_phase()

    def set_session_manually(self, session_type: SessionType):
        self._timer.stop()
        self.session_type = session_type
        self.status = TimerStatus.IDLE
        self.total_seconds = self._get_duration_for_current_session()
        self.remaining_seconds = self.total_seconds
        self.state_changed.emit(self.session_type, self.cycle_count)
        self.status_changed.emit(self.status)
        self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))

    def _get_duration_for_current_session(self) -> int:
        if self.session_type == SessionType.WORK:
            return self.config.work_duration_min * 60
        elif self.session_type == SessionType.SHORT_BREAK:
            return self.config.short_break_min * 60
        else:
            return self.config.long_break_min * 60

    def _on_tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            if self.remaining_seconds == 0:
                self._on_session_completed()

    def _on_session_completed(self):
        self._timer.stop()
        self.status = TimerStatus.IDLE
        self.status_changed.emit(self.status)
        self._advance_to_next_phase()

    def _advance_to_next_phase(self):
        if self.session_type == SessionType.WORK:
            # Foco concluído, avançar para pausa
            if self.cycle_count >= self.config.cycles_before_long_break:
                self.session_type = SessionType.LONG_BREAK
            else:
                self.session_type = SessionType.SHORT_BREAK
            
            self.total_seconds = self._get_duration_for_current_session()
            self.remaining_seconds = self.total_seconds
            self.state_changed.emit(self.session_type, self.cycle_count)
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            
            # Emitir sinal de início de pausa
            self.break_started.emit(self.session_type, self.total_seconds, self.cycle_count)
            
            if self.config.auto_start_break:
                self.status = TimerStatus.RUNNING
                self._timer.start()
                self.status_changed.emit(self.status)
        else:
            # Pausa concluída, avançar para trabalho
            if self.session_type == SessionType.LONG_BREAK:
                self.cycle_count = 1
            else:
                self.cycle_count += 1
                
            self.session_type = SessionType.WORK
            self.total_seconds = self._get_duration_for_current_session()
            self.remaining_seconds = self.total_seconds
            self.state_changed.emit(self.session_type, self.cycle_count)
            self.tick.emit(self.remaining_seconds, self.total_seconds, self.format_time(self.remaining_seconds))
            
            self.work_started.emit(self.cycle_count)
            
            if self.config.auto_start_work:
                self.status = TimerStatus.RUNNING
                self._timer.start()
                self.status_changed.emit(self.status)
