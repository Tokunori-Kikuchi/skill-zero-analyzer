#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-Zero Analyzer - Configuration
設定管理クラス
"""

import os
from typing import Dict, Any


class Config:
    """設定管理クラス"""

    # ファイルパス設定
    CSV_FILE_PATH = "spreadsheet_data - form_answer.csv"
    PROCESSED_DATA_FILE = "output/processed_data.json"
    OUTPUT_DIR = "output"
    DATA_DIR = "data"

    # ログ設定
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # データ処理設定
    MIN_PROFILE_SIZE = 1000
    MAX_RETRY_COUNT = 3
    REQUEST_TIMEOUT = 30

    # プロフィール抽出設定
    PROFILE_SECTIONS = {
        'bio': '自己紹介',
        'location': '出身地',
        'job': '職種・職業',
        'family': '家族構成',
        'libecity_meeting': 'リベ大との出会い',
        'challenges': '挑戦、実践していること、これからやりたいことなど',
        'hobbies': '趣味・特技',
        'likes': '好きな〇〇',
        'skills': '経歴・スキル'
    }

    # CSV列名マッピング
    CSV_COLUMNS = {
        'timestamp': 'タイムスタンプ',
        'email': 'メールアドレス',
        'nickname': 'ニックネーム\nリベシティで使用している名前）',
        'profile_url': 'リベシティの\nプロフィールURL',
        'profile_data': 'プロフィールデータ',
        'experience': '今までやってきたこと （仕事／プライベート）',
        'strengths': '得意と言われたこと／好きなこと',
        'appreciation': '人に感謝されたこと／頼まれたこと',
        'not_bad_at': '苦手じゃないこと／つい引き受けてしまうこと',
        'weaknesses': '「これは苦手...」と思うこと'
    }

    @classmethod
    def get_csv_column(cls, key: str) -> str:
        """CSV列名を取得"""
        return cls.CSV_COLUMNS.get(key, key)

    @classmethod
    def validate_paths(cls) -> bool:
        """必要なパスが存在するかチェック"""
        required_paths = [
            cls.CSV_FILE_PATH,
            cls.DATA_DIR
        ]

        missing_paths = []
        for path in required_paths:
            if not os.path.exists(path):
                missing_paths.append(path)

        if missing_paths:
            print(f"エラー: 以下のファイル/ディレクトリが見つかりません: {missing_paths}")
            return False

        return True

    @classmethod
    def get_output_path(cls, filename: str) -> str:
        """出力ファイルのパスを生成"""
        return os.path.join(cls.OUTPUT_DIR, filename)

    @classmethod
    def get_data_path(cls, filename: str) -> str:
        """データファイルのパスを生成"""
        return os.path.join(cls.DATA_DIR, filename)


# 設定インスタンス
config = Config()