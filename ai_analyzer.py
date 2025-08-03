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


class ProfileAnalyzer:
    """プロフィール分析クラス"""

    @staticmethod
    def create_profile_summary(name: str, profile_info: Dict[str, Any]) -> str:
        """プロフィール情報のサマリーを作成"""
        if not ValidationUtils.is_valid_profile_data(profile_info):
            return ""

        return f"""
## プロフィール情報
**名前**: {name}

**職種・職業**: {profile_info.get('job', '未登録')}

**自己紹介**: {profile_info.get('bio', '未登録')}

**出身地**: {profile_info.get('location', '未登録')}

**家族構成**: {profile_info.get('family', '未登録')}

**リベ大との出会い**: {profile_info.get('libecity_meeting', '未登録')}

**挑戦・実践**: {profile_info.get('challenges', '未登録')}

**趣味・特技**: {profile_info.get('hobbies', '未登録')}

**好きなこと**: {profile_info.get('likes', '未登録')}

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


class PromptGenerator:
    """プロンプト生成クラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)
        self.prompts_content = self._load_prompts()

    def _load_prompts(self) -> str:
        """プロンプトテンプレートを読み込み"""
        try:
            prompts_file = os.path.join(config.DATA_DIR, 'prompts.md')
            if os.path.exists(prompts_file):
                with open(prompts_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.error(f"プロンプトファイルが見つかりません: {prompts_file}")
                return ""
        except Exception as e:
            self.logger.error(f"プロンプト読み込みエラー: {e}")
            return ""

    def create_analysis_prompt(self, name: str, profile_info: Dict[str, Any],
                              form_data: Dict[str, Any]) -> str:
        """分析用プロンプトを作成"""
        try:
            # 各セクションを作成
            profile_summary = ProfileAnalyzer.create_profile_summary(name, profile_info)
            form_summary = ProfileAnalyzer.create_form_summary(form_data)
            offline_meeting_info = ProfileAnalyzer.create_offline_meeting_info()

            # 完全なプロンプトを組み立て
            full_prompt = f"""{self.prompts_content}

{profile_summary}

{form_summary}

{offline_meeting_info}"""

            return full_prompt

        except Exception as e:
            self.logger.error(f"プロンプト生成エラー ({name}): {e}")
            return ""


class FileManager:
    """ファイル管理クラス"""

    @staticmethod
    def save_analysis_prompt(name: str, prompt: str) -> str:
        """分析用プロンプトを保存"""
        try:
            # 出力ディレクトリを作成
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)

            # ファイル名を生成
            filename = f"{name}_analysis_prompt.txt"
            filepath = os.path.join(config.OUTPUT_DIR, filename)

            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(prompt)

            return filepath

        except Exception as e:
            Logger.setup_logger(__name__).error(f"プロンプト保存エラー ({name}): {e}")
            return ""

    @staticmethod
    def save_analysis_result(name: str, analysis_result: str) -> bool:
        """分析結果を保存"""
        try:
            # 出力ディレクトリを作成
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)

            # ファイル名を生成
            filename = f"{name}さんのAI分析.md"
            filepath = os.path.join(config.OUTPUT_DIR, filename)

            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(analysis_result)

            return True

        except Exception as e:
            Logger.setup_logger(__name__).error(f"分析結果保存エラー ({name}): {e}")
            return False


class DataLoader:
    """データ読み込みクラス"""

    @staticmethod
    def load_processed_data() -> Optional[Dict[str, Any]]:
        """処理済みデータを読み込み"""
        try:
            if not os.path.exists(config.PROCESSED_DATA_FILE):
                Logger.setup_logger(__name__).error(f"処理済みデータファイルが見つかりません: {config.PROCESSED_DATA_FILE}")
                return None

            with open(config.PROCESSED_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            Logger.setup_logger(__name__).info(f"処理されたデータを読み込みました: {data.get('total_participants', 0)}件")
            return data

        except Exception as e:
            Logger.setup_logger(__name__).error(f"データ読み込みエラー: {e}")
            return None


class AIAnalyzer:
    """AI分析メインクラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)
        self.prompt_generator = PromptGenerator()
        self.data = None

    def load_data(self) -> bool:
        """データを読み込み"""
        try:
            self.data = DataLoader.load_processed_data()
            if self.data is None:
                return False

            self.logger.info(f"処理されたデータを読み込みました: {len(self.data.get('participants', []))}件")
            return True

        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}")
            return False

    def create_analysis_prompt(self, name: str, participant_data: Dict[str, Any]) -> str:
        """参加者の分析用プロンプトを作成"""
        try:
            profile_info = participant_data.get('profile_info', {})
            form_data = participant_data.get('form_data', {})

            return self.prompt_generator.create_analysis_prompt(name, profile_info, form_data)

        except Exception as e:
            self.logger.error(f"プロンプト作成エラー ({name}): {e}")
            return ""

    def analyze_participant(self, name: str, participant_data: Dict[str, Any]) -> bool:
        """参加者の分析を実行"""
        try:
            self.logger.info(f"{name}さんのAI分析を開始...")

            # 分析用プロンプトを作成
            prompt = self.create_analysis_prompt(name, participant_data)
            if not prompt:
                self.logger.error(f"プロンプト作成に失敗: {name}")
                return False

            # プロンプトを保存
            filepath = FileManager.save_analysis_prompt(name, prompt)
            if filepath:
                self.logger.info(f"分析用プロンプトを保存しました: {filepath}")
                self.logger.info(f"{name}さんの分析用プロンプトが準備されました。")
                self.logger.info("このプロンプトをCursorのAIに投げて分析を実行してください。")
                return True
            else:
                self.logger.error(f"プロンプト保存に失敗: {name}")
                return False

        except Exception as e:
            self.logger.error(f"分析エラー ({name}): {e}")
            return False

    def run_analysis(self) -> bool:
        """全参加者の分析を実行"""
        try:
            self.logger.info("AI分析を開始します...")

            if not self.load_data():
                return False

            participants = self.data.get('participants', [])
            if not participants:
                self.logger.error("分析対象の参加者が見つかりません")
                return False

            success_count = 0
            total_count = len(participants)

            for participant in participants:
                name = participant.get('nickname', 'Unknown')
                if self.analyze_participant(name, participant):
                    success_count += 1

            self.logger.info("AI分析の準備が完了しました。")
            self.logger.info(f"成功: {success_count}/{total_count}人")
            self.logger.info("各参加者の分析用プロンプトがoutputフォルダに保存されました。")
            self.logger.info("これらのプロンプトをCursorのAIに投げて分析を実行してください。")

            return success_count == total_count

        except Exception as e:
            self.logger.error(f"AI分析エラー: {e}")
            return False


def main():
    """メイン関数"""
    analyzer = AIAnalyzer()
    success = analyzer.run_analysis()

    if success:
        print("AI分析の準備が正常に完了しました。")
    else:
        print("AI分析の準備中にエラーが発生しました。")


if __name__ == "__main__":
    main()