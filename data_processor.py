#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-Zero Analyzer - Data Processor
スプレッドシートデータとプロフィールテキストから参加者データを統合するスクリプト
"""

import pandas as pd
import json
import time
import re
import os
from typing import Dict, List, Optional, Any
from config import config
from utils import Logger, FileUtils, DataUtils, ValidationUtils


class ProfileTextExtractor:
    """プロフィールテキストデータから情報を抽出するクラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)

    def extract_from_text(self, profile_text: str) -> Optional[Dict[str, Any]]:
        """プロフィールテキストから情報を抽出"""
        if not profile_text or profile_text.strip() == "":
            return None

        try:
            profile_info = {
                'username': '',
                'bio': '',
                'location': '',
                'job': '',
                'family': '',
                'libecity_meeting': '',
                'challenges': '',
                'hobbies': '',
                'likes': '',
                'skills': '',
                'duration': '',
                'register_date': '',
                'work_history': [],
                'strengths': [],
                'likes_list': []
            }

            # ユーザー名を抽出
            username_match = re.search(r'(.+?)さんのプロフィール', profile_text)
            if username_match:
                profile_info['username'] = username_match.group(1)

            # 各セクションを抽出
            sections = {
                'bio': r'自己紹介\n(.+?)(?=\n出身地|\n職種・職業|\n家族構成|\nリベ大との出会い|\n挑戦|\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'location': r'出身地\n(.+?)(?=\n職種・職業|\n家族構成|\nリベ大との出会い|\n挑戦|\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'job': r'職種・職業\n(.+?)(?=\n家族構成|\nリベ大との出会い|\n挑戦|\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'family': r'家族構成\n(.+?)(?=\nリベ大との出会い|\n挑戦|\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'libecity_meeting': r'リベ大との出会い\n(.+?)(?=\n挑戦|\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'challenges': r'挑戦、実践していること、これからやりたいことなど\n(.+?)(?=\n趣味・特技|\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'hobbies': r'趣味・特技\n(.+?)(?=\n好きな〇〇|\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'likes': r'好きな〇〇\n(.+?)(?=\nイチオシ|\n価値観マップ|\nアルバム|\nその他|\n各種SNS|\nスキル・ポートフォリオ|\n経歴・スキル|\nポートフォリオ|\n掲載中の関連サービス)',
                'skills': r'経歴・スキル\n(.+?)(?=\nポートフォリオ|\n掲載中の関連サービス)'
            }

            # 各セクションを抽出
            for key, pattern in sections.items():
                match = re.search(pattern, profile_text, re.DOTALL)
                if match:
                    profile_info[key] = match.group(1).strip()

            # 自己紹介から経歴を抽出
            if profile_info['bio']:
                self._extract_work_history_from_bio(profile_info['bio'], profile_info)

            # 好きなことリストを作成
            if profile_info['likes']:
                profile_info['likes_list'] = [profile_info['likes']]

            self.logger.info(f"プロフィールテキストから情報を抽出しました: {profile_info['username']}")
            return profile_info

        except Exception as e:
            self.logger.error(f"プロフィールテキスト抽出エラー: {e}")
            return None

    def _extract_work_history_from_bio(self, bio_text: str, profile_info: Dict[str, Any]) -> None:
        """自己紹介から経歴を抽出"""
        try:
            work_keywords = ['勤務', '転職', '就職', '仕事', '職歴', '経験', '働い', '務め', '在籍']
            work_history = []

            lines = bio_text.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line for keyword in work_keywords):
                    work_history.append(line)

            if work_history:
                profile_info['work_history'] = work_history
        except Exception as e:
            self.logger.error(f"経歴抽出エラー: {e}")


class DataMerger:
    """データ統合クラス"""

    @staticmethod
    def merge_duplicate_participants(participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複する参加者データを統合"""
        unique_participants = []

        for participant in participants:
            nickname = participant.get('nickname', '')
            existing_index = DataMerger._find_existing_participant(unique_participants, nickname)

            if existing_index is not None:
                # 既存のデータと統合
                unique_participants[existing_index] = DataMerger._merge_participant_data(
                    unique_participants[existing_index], participant
                )
            else:
                # 新しい参加者として追加
                unique_participants.append(participant)

        return unique_participants

    @staticmethod
    def _find_existing_participant(participants: List[Dict[str, Any]], nickname: str) -> Optional[int]:
        """既存の参加者を検索"""
        for i, participant in enumerate(participants):
            if participant.get('nickname', '') == nickname:
                return i
        return None

    @staticmethod
    def _merge_participant_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """参加者データを統合"""
        merged = existing.copy()

        # プロフィール情報を統合（新しいデータを優先）
        if new.get('profile_info'):
            merged['profile_info'] = new['profile_info']

        # フォームデータを統合
        if new.get('form_data'):
            if 'form_data' not in merged:
                merged['form_data'] = {}
            merged['form_data'].update(new['form_data'])

        return merged


class DataProcessor:
    """データ処理メインクラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)
        self.text_extractor = ProfileTextExtractor()

    def load_csv_data(self) -> Optional[pd.DataFrame]:
        """CSVデータを読み込み"""
        try:
            csv_file = config.CSV_FILE_PATH
            if not os.path.exists(csv_file):
                self.logger.error(f"CSVファイルが見つかりません: {csv_file}")
                return None

            df = pd.read_csv(csv_file)
            self.logger.info(f"CSVファイルを読み込みました: {len(df)}件のデータ")
            return df

        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            return None

    def process_participant_data(self, row: pd.Series) -> Dict[str, Any]:
        """参加者データを処理"""
        try:
            # 基本情報を抽出
            participant_data = {
                'timestamp': row.get('タイムスタンプ', ''),
                'email': row.get('メールアドレス', ''),
                'nickname': row.get('ニックネーム\nリベシティで使用している名前）', ''),
                'profile_url': row.get('リベシティの\nプロフィールURL', ''),
                'form_data': {
                    'experience': row.get('今までやってきたこと （仕事／プライベート）', ''),
                    'strengths': row.get('得意と言われたこと／好きなこと', ''),
                    'appreciation': row.get('人に感謝されたこと／頼まれたこと', ''),
                    'not_bad_at': row.get('苦手じゃないこと／つい引き受けてしまうこと', ''),
                    'weaknesses': row.get('「これは苦手...」と思うこと', '')
                },
                'submitted': True,
                'profile_info': {
                    'url': row.get('リベシティの\nプロフィールURL', ''),
                    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }

            # J列のプロフィールデータがある場合は情報を取得
            if row.get('プロフィールデータ'):
                profile_info_from_text = self.text_extractor.extract_from_text(row['プロフィールデータ'])
                if profile_info_from_text:
                    participant_data['profile_info'] = profile_info_from_text

            self.logger.info(f"参加者データを処理しました: {participant_data['nickname']}")
            return participant_data

        except Exception as e:
            self.logger.error(f"参加者データ処理エラー: {e}")
            return {}

    def save_processed_data(self, participants: List[Dict[str, Any]]) -> None:
        """処理済みデータを保存"""
        try:
            output_data = {
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_participants': len(participants),
                'participants': participants
            }

            # 出力ディレクトリを作成
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)

            # JSONファイルに保存
            with open(config.PROCESSED_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"処理済みデータを保存しました: {config.PROCESSED_DATA_FILE}")
            self.logger.info(f"参加者数: {len(participants)}人")

        except Exception as e:
            self.logger.error(f"データ保存エラー: {e}")

    def run(self) -> None:
        """データ処理を実行"""
        try:
            self.logger.info("=== Skill-Zero Analyzer - Data Processor ===")
            self.logger.info("データ処理を開始します...")

            # CSVデータを読み込み
            df = self.load_csv_data()
            if df is None:
                return

            # 参加者データを処理
            participants = []
            for _, row in df.iterrows():
                participant_data = self.process_participant_data(row)
                if participant_data:
                    participants.append(participant_data)

            # 重複データを統合
            self.logger.info("重複データの統合を開始...")
            original_count = len(participants)
            participants = DataMerger.merge_duplicate_participants(participants)
            merged_count = len(participants)
            self.logger.info(f"統合前: {original_count}人 → 統合後: {merged_count}人")

            # 処理済みデータを保存
            self.save_processed_data(participants)

            self.logger.info("=== データ処理完了 ===")
            self.logger.info(f"処理された参加者数: {len(participants)}人")
            self.logger.info(f"出力ファイル: {config.PROCESSED_DATA_FILE}")

        except Exception as e:
            self.logger.error(f"データ処理エラー: {e}")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()