#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-Zero Analyzer - AI Analyzer
統合されたデータからAI分析用プロンプトを生成するスクリプト
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from config import config
from utils import Logger, FileUtils, ValidationUtils


class PromptGenerator:
    """プロンプト生成クラス"""

    @staticmethod
    def create_profile_summary(name: str, profile_info: Dict[str, Any]) -> str:
        """プロフィール情報のサマリーを作成"""
        if not ValidationUtils.is_valid_profile_data(profile_info):
            return ""

        return f"""
## プロフィール情報
**名前**: {name}

**職種・職業**: {profile_info.get('occupation', '未登録')}

**自己紹介**: {profile_info.get('bio', '未登録')}

**家族構成**: {profile_info.get('family', '未登録')}

**リベ大との出会い**: {profile_info.get('libecity_encounter', '未登録')}

**挑戦・実践**: {profile_info.get('challenges', '未登録')}

**趣味・特技**: {profile_info.get('hobbies', '未登録')}

**好きなこと**: {profile_info.get('likes', '未登録')}

**好きな国**: {profile_info.get('favorite_country', '未登録')}

**スキル・資格**: {profile_info.get('skills', '未登録')}

**詳細プロフィール**:
{profile_info.get('work_history', '')}
"""

    @staticmethod
    def create_form_summary(form_data: Dict[str, Any]) -> str:
        """フォーム回答データのサマリーを作成"""
        return f"""
## フォーム回答データ
**今までやってきたこと （仕事／プライベート）**: {form_data.get('experience', '未回答')}

**得意と言われたこと／好きなこと**: {form_data.get('strengths', '未回答')}

**人に感謝されたこと／頼まれたこと**: {form_data.get('appreciation', '未回答')}

**苦手じゃないこと／つい引き受けてしまうこと**: {form_data.get('not_bad_at', '未回答')}

**「これは苦手...」と思うこと**: {form_data.get('weaknesses', '未回答')}
"""

    @staticmethod
    def create_offline_meeting_info() -> str:
        """オフ会情報を作成"""
        return """
## オフ会情報
【スキルゼロでもOK！】"自分の得意"が見つかる♪はじめの一歩オフ会
～ スキルゼロでもOK！一歩目を応援する気づきの場 ～

**開催概要**:
- 日時：7月13日（◯）10:00〜12:00
- 場所：新橋オフィス（参加無料）
- 定員：５名ほど（先着順・初参加歓迎！）

**対象となる方**:
・スキルや強みがまだ見えていない方
・何か始めたいけど、何からすればいいか迷っている方
・仲間やヒントを見つけたい方
・副業・スモールビジネスに興味がある方

**当日の内容**:
・かんたんな自己紹介（無理に話さなくてもOK）
・"できることの種"を見つけるワーク
・プチ相談＆体験談シェア
・先輩メンバーのリアルな話
・1人じゃ気づけなかった"自分の強み"と出会える時間

**参加特典**:
・初心者向け「スキルの棚卸しシート」配布
・ロクナナさんの"リアル副業ストーリー"トークあり
"""

    @staticmethod
    def create_full_prompt(prompts_content: str, profile_summary: str,
                          form_summary: str, offline_meeting_info: str) -> str:
        """完全なプロンプトを作成"""
        # プロフィール情報が空の場合は、プロフィールセクションを除外
        if not profile_summary.strip():
            return f"""
{prompts_content}

{form_summary}

{offline_meeting_info}

完了
"""

        return f"""
{prompts_content}

{profile_summary}

{form_summary}

{offline_meeting_info}

完了
"""


class FileManager:
    """ファイル管理クラス"""

    @staticmethod
    def save_analysis_prompt(name: str, prompt: str) -> str:
        """分析用プロンプトをファイルに保存"""
        FileUtils.ensure_directory(config.OUTPUT_DIR)
        filename = os.path.join(config.OUTPUT_DIR, f"{name}_analysis_prompt.txt")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            return filename
        except Exception as e:
            logging.error(f"プロンプト保存でエラー: {e}")
            return ""

    @staticmethod
    def save_analysis_result(name: str, analysis_result: str) -> bool:
        """分析結果をファイルに保存"""
        FileUtils.ensure_directory(config.OUTPUT_DIR)
        filename = os.path.join(config.OUTPUT_DIR, f"{name}さんのAI分析.md")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(analysis_result)
            return True
        except Exception as e:
            logging.error(f"ファイル保存でエラー: {e}")
            return False


class DataLoader:
    """データ読み込みクラス"""

    @staticmethod
    def load_processed_data() -> Optional[Dict[str, Any]]:
        """処理されたデータを読み込み"""
        return FileUtils.safe_read_json(config.PROCESSED_DATA_FILE)

    @staticmethod
    def load_prompts() -> Optional[str]:
        """prompts.mdファイルを読み込み"""
        try:
            with open(config.PROMPTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            logging.error(f"ファイルが見つかりません: {config.PROMPTS_FILE}")
            return None
        except Exception as e:
            logging.error(f"プロンプトファイル読み込みエラー: {e}")
            return None


class AIAnalyzer:
    """AI分析クラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)
        self.processed_data: Dict[str, Any] = {}
        self.prompts_content: str = ""
        self.prompt_generator = PromptGenerator()
        self.file_manager = FileManager()
        self.data_loader = DataLoader()

    def load_data(self) -> bool:
        """データを読み込み"""
        # 処理されたデータを読み込み
        self.processed_data = self.data_loader.load_processed_data()
        if not self.processed_data:
            self.logger.error("処理されたデータを読み込めませんでした")
            return False

        # プロンプトファイルを読み込み
        self.prompts_content = self.data_loader.load_prompts()
        if not self.prompts_content:
            self.logger.error("プロンプトファイルを読み込めませんでした")
            return False

        self.logger.info(f"処理されたデータを読み込みました: {len(self.processed_data)}件")
        self.logger.info("プロンプトファイルを読み込みました")
        return True

    def create_analysis_prompt(self, name: str, data: Dict[str, Any]) -> str:
        """分析用のプロンプトを作成"""
        form_data = data.get('form_data', {})
        profile_info = data.get('profile_info', {})

        # 各セクションを作成
        profile_summary = self.prompt_generator.create_profile_summary(name, profile_info)
        form_summary = self.prompt_generator.create_form_summary(form_data)
        offline_meeting_info = self.prompt_generator.create_offline_meeting_info()

        # 完全なプロンプトを作成
        return self.prompt_generator.create_full_prompt(
            self.prompts_content,
            profile_summary,
            form_summary,
            offline_meeting_info
        )

    def analyze_participant(self, name: str, data: Dict[str, Any]) -> bool:
        """参加者1人の分析を実行"""
        self.logger.info(f"{name}さんのAI分析を開始...")

        try:
            # 分析用プロンプトを作成
            prompt = self.create_analysis_prompt(name, data)

            # プロンプトをファイルに保存
            filename = self.file_manager.save_analysis_prompt(name, prompt)
            if filename:
                self.logger.info(f"分析用プロンプトを保存しました: {filename}")
                self.logger.info(f"{name}さんの分析用プロンプトが準備されました。")
                self.logger.info("このプロンプトをCursorのAIに投げて分析を実行してください。")
                return True
            else:
                self.logger.error(f"{name}さんのプロンプト保存に失敗しました。")
                return False

        except Exception as e:
            self.logger.error(f"{name}さんの分析でエラー: {e}")
            return False

    def run_analysis(self) -> bool:
        """全参加者の分析を実行"""
        self.logger.info("AI分析を開始します...")

        # データ読み込み
        if not self.load_data():
            return False

        # 参加者データを取得
        participants = self.processed_data.get('participants', [])

        # 各参加者の分析を実行
        success_count = 0
        for participant in participants:
            nickname = participant.get('nickname', 'Unknown')
            if self.analyze_participant(nickname, participant):
                success_count += 1

        self.logger.info("AI分析の準備が完了しました。")
        self.logger.info(f"成功: {success_count}/{len(participants)}人")
        self.logger.info("各参加者の分析用プロンプトがoutputフォルダに保存されました。")
        self.logger.info("これらのプロンプトをCursorのAIに投げて分析を実行してください。")

        return success_count > 0


def main():
    """メイン関数"""
    analyzer = AIAnalyzer()
    success = analyzer.run_analysis()

    if success:
        analyzer.logger.info("AI分析の準備が正常に完了しました。")
    else:
        analyzer.logger.error("AI分析の準備でエラーが発生しました。")


if __name__ == "__main__":
    main()