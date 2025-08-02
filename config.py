import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """アプリケーション設定クラス"""

    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"

    # ファイルパス設定
    PROMPTS_FILE: str = "data/prompts.md"
    CSV_FILE: str = "spreadsheet_data - form_answer.csv"
    OUTPUT_DIR: str = "output"
    PROCESSED_DATA_FILE: str = "output/processed_data.json"
    DEBUG_FILE: str = "output/debug_summary.txt"

    # HTTP設定
    REQUEST_TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    # プロフィール抽出設定
    MIN_PROFILE_SIZE: int = 10000
    PROFILE_INDICATORS: list = None

    # 環境変数
    LIBECITY_EMAIL: Optional[str] = None
    LIBECITY_PASSWORD: Optional[str] = None

    def __post_init__(self):
        """初期化後の処理"""
        if self.PROFILE_INDICATORS is None:
            self.PROFILE_INDICATORS = ['プロフィール', 'content_title', '自己紹介']

        # 環境変数から認証情報を取得
        self.LIBECITY_EMAIL = os.getenv('LIBECITY_EMAIL')
        self.LIBECITY_PASSWORD = os.getenv('LIBECITY_PASSWORD')

    @classmethod
    def from_env(cls) -> 'Config':
        """環境変数から設定を読み込み"""
        return cls()


# グローバル設定インスタンス
config = Config.from_env()