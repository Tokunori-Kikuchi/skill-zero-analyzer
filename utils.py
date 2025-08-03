#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-Zero Analyzer - Utilities
共通ユーティリティクラス
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from config import config


class Logger:
    """ログ管理クラス"""

    @staticmethod
    def setup_logger(name: str) -> logging.Logger:
        """ロガーを設定"""
        logger = logging.getLogger(name)

        if not logger.handlers:
            logger.setLevel(getattr(logging, config.LOG_LEVEL))

            # コンソールハンドラー
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, config.LOG_LEVEL))

            # フォーマッター
            formatter = logging.Formatter(config.LOG_FORMAT)
            console_handler.setFormatter(formatter)

            logger.addHandler(console_handler)

        return logger


class FileUtils:
    """ファイル操作ユーティリティ"""

    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """ディレクトリが存在しない場合は作成"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"ディレクトリ作成エラー ({directory}): {e}")
            return False

    @staticmethod
    def safe_read_json(filepath: str) -> Optional[Dict[str, Any]]:
        """JSONファイルを安全に読み込み"""
        try:
            if not os.path.exists(filepath):
                logging.error(f"ファイルが見つかりません: {filepath}")
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logging.error(f"JSON読み込みエラー ({filepath}): {e}")
            return None

    @staticmethod
    def safe_write_json(filepath: str, data: Dict[str, Any]) -> bool:
        """JSONファイルを安全に書き込み"""
        try:
            # ディレクトリを作成
            directory = os.path.dirname(filepath)
            if directory:
                FileUtils.ensure_directory(directory)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logging.error(f"JSON書き込みエラー ({filepath}): {e}")
            return False


class DataUtils:
    """データ処理ユーティリティ"""

    @staticmethod
    def clean_text(text: str) -> str:
        """テキストをクリーニング"""
        if not text:
            return ""

        # 改行と空白を正規化
        cleaned = text.strip()
        cleaned = ' '.join(cleaned.split())

        return cleaned

    @staticmethod
    def extract_list_from_text(text: str, keywords: List[str]) -> List[str]:
        """テキストからキーワードを含む行を抽出"""
        if not text:
            return []

        lines = text.split('\n')
        extracted = []

        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in keywords):
                extracted.append(line)

        return extracted

    @staticmethod
    def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """辞書を統合（updateの値を優先）"""
        result = base.copy()
        result.update(update)
        return result


class ValidationUtils:
    """バリデーションユーティリティ"""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """URLが有効かチェック"""
        if not url or not isinstance(url, str):
            return False

        # 基本的なURL形式チェック
        return url.startswith(('http://', 'https://'))

    @staticmethod
    def is_valid_profile_data(profile_info: Dict[str, Any]) -> bool:
        """プロフィールデータが有効かチェック"""
        if not profile_info or not isinstance(profile_info, dict):
            return False

        # 最低限の情報があるかチェック
        required_fields = ['username']
        return any(field in profile_info for field in required_fields)

    @staticmethod
    def is_valid_csv_data(df) -> bool:
        """CSVデータが有効かチェック"""
        if df is None or df.empty:
            return False

        # 必要な列が存在するかチェック
        required_columns = [
            config.get_csv_column('nickname'),
            config.get_csv_column('profile_data')
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logging.warning(f"必要な列が見つかりません: {missing_columns}")
            return False

        return True