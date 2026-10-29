import json
import os
from dataclasses import dataclass, asdict

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

@dataclass
class PomodoroConfig:
    work_duration_min: int = 25
    short_break_min: int = 5
    long_break_min: int = 15
    cycles_before_long_break: int = 4
    
    # Visual blur settings
    blur_radius: int = 10         # 6: Suave, 10: Normal, 18: Intenso
    dim_factor: float = 0.50      # 0.3 (escuro) a 0.8 (claro)
    
    # Behavior
    enable_sound: bool = True
    auto_start_break: bool = True
    auto_start_work: bool = False
    allow_esc_skip: bool = True
    
    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    @classmethod
    def load(cls) -> "PomodoroConfig":
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}, usando padrões.")
        config = cls()
        config.save()
        return config
