#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共通ユーティリティクラス
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from config import config


class Logger:
    """ログ管理クラス"""

    @staticmethod
    def setup_logger(name: str, level: str = None) -> logging.Logger:
        """ロガーを設定"""
        logger = logging.getLogger(name)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(config.LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.setLevel(getattr(logging, level or config.LOG_LEVEL))
        return logger


class FileUtils:
    """ファイル操作ユーティリティ"""

    @staticmethod
    def ensure_directory(path: str) -> None:
        """ディレクトリが存在することを確認"""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def safe_write_json(data: Dict[str, Any], filepath: str) -> bool:
        """JSONファイルを安全に書き込み"""
        try:
            FileUtils.ensure_directory(os.path.dirname(filepath))
            with open(filepath, 'w', encoding='utf-8') as f:
                import json
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"JSON書き込みエラー: {e}")
            return False

    @staticmethod
    def safe_read_json(filepath: str) -> Optional[Dict[str, Any]]:
        """JSONファイルを安全に読み込み"""
        try:
            if not os.path.exists(filepath):
                return None
            with open(filepath, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        except Exception as e:
            logging.error(f"JSON読み込みエラー: {e}")
            return None


class HttpUtils:
    """HTTP操作ユーティリティ"""

    @staticmethod
    def create_session() -> 'requests.Session':
        """HTTPセッションを作成"""
        import requests

        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        session.headers.update(headers)
        return session

    @staticmethod
    def safe_request(session: 'requests.Session', url: str,
                    max_retries: int = None, timeout: int = None) -> Optional['requests.Response']:
        """安全なHTTPリクエスト"""
        import requests

        max_retries = max_retries or config.MAX_RETRIES
        timeout = timeout or config.REQUEST_TIMEOUT

        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=timeout)
                return response
            except requests.RequestException as e:
                logging.warning(f"リクエストエラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(config.RETRY_DELAY)

        logging.error(f"リクエスト失敗: {url}")
        return None


class DataUtils:
    """データ処理ユーティリティ"""

    @staticmethod
    def clean_text(text: str) -> str:
        """テキストをクリーンアップ"""
        if not text:
            return ""
        return text.strip()

    @staticmethod
    def extract_field_value(soup: 'BeautifulSoup', field_name: str) -> Optional[str]:
        """HTMLからフィールド値を抽出"""
        elem = soup.find('dt', string=field_name)
        if elem and elem.find_next_sibling('dd'):
            text = elem.find_next_sibling('dd').get_text(strip=True)
            return DataUtils.clean_text(text) if text != '未登録' else None
        return None

    @staticmethod
    def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """辞書を統合（dict2の値で上書き）"""
        result = dict1.copy()
        for key, value in dict2.items():
            if value and (key not in result or not result[key]):
                result[key] = value
        return result


class ValidationUtils:
    """バリデーション用ユーティリティ"""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """URLが有効かチェック"""
        if not url or not isinstance(url, str):
            return False
        return url.strip() != "" and not url.isspace()

    @staticmethod
    def is_valid_profile_data(data: Dict[str, Any]) -> bool:
        """プロフィールデータが有効かチェック"""
        if not data or not isinstance(data, dict):
            return False
        return len(data) > 2  # URLとextracted_at以外のデータがあるか