"""Agent configuration — loaded from agent.env or environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent.parent / "agent.env"
load_dotenv(_env_file)


class AgentConfig:
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8000")
    access_token: str = os.getenv("ACCESS_TOKEN", "")
    refresh_token: str = os.getenv("REFRESH_TOKEN", "")
    contract_id: str = os.getenv("CONTRACT_ID", "")
    screenshot_interval_min: int = int(os.getenv("SCREENSHOT_INTERVAL_MIN", "10"))
    idle_timeout_min: int = int(os.getenv("IDLE_TIMEOUT_MIN", "5"))
    idle_autopause_sec: int = int(os.getenv("IDLE_AUTOPAUSE_SEC", "120"))
    spool_dir: str = os.getenv("SPOOL_DIR", str(Path(__file__).parent.parent / "spool"))

    # Phase 3: capture all monitors (True) or primary only (False)
    capture_all_monitors: bool = os.getenv("CAPTURE_ALL_MONITORS", "true").lower() == "true"

    # Activity level formula constant: score = min(10, (keystrokes + clicks*5) / SCALE)
    activity_scale_factor: int = int(os.getenv("ACTIVITY_SCALE_FACTOR", "150"))

    def save(self) -> None:
        lines = [
            f"SERVER_URL={self.server_url}",
            f"ACCESS_TOKEN={self.access_token}",
            f"REFRESH_TOKEN={self.refresh_token}",
            f"CONTRACT_ID={self.contract_id}",
            f"SCREENSHOT_INTERVAL_MIN={self.screenshot_interval_min}",
            f"IDLE_TIMEOUT_MIN={self.idle_timeout_min}",
            f"SPOOL_DIR={self.spool_dir}",
            f"ACTIVITY_SCALE_FACTOR={self.activity_scale_factor}",
            f"CAPTURE_ALL_MONITORS={str(self.capture_all_monitors).lower()}",
        ]
        _env_file.write_text("\n".join(lines) + "\n")


config = AgentConfig()
