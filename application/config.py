import os

class Settings:
    APP_NAME: str = "The Solver Race - Clearing Gateway"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "clearing-sov-mesh-session-key-8891")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/solver_race.db" if os.getenv("VERCEL") else "sqlite:///./solver_race.db"
    )
    
    # Settlement & Liquidity Parameters
    INITIAL_POOL_RESERVE: float = 1500.00
    STATUTORY_SOLVENCY_FLOOR: float = 500.00
    FLAG: str = os.getenv("FLAG", "CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}")

settings = Settings()
