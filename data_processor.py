#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-Zero Analyzer - Data Processor
スプレッドシートデータとプロフィールURLから参加者データを統合するスクリプト
"""

import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse
import os
import glob
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from config import config
from utils import Logger, FileUtils, HttpUtils, DataUtils, ValidationUtils


class ProfileExtractor:
    """プロフィール情報抽出クラス"""

    def __init__(self):
        self.logger = Logger.setup_logger(__name__)
        self.session = HttpUtils.create_session()

    def extract_profile_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URLからプロフィール情報を抽出"""
        if not ValidationUtils.is_valid_url(url):
            return None

        try:
            if "libecity.com/user_profile/" in url:
                return self._extract_libecity_profile(url)
            else:
                self.logger.warning(f"未対応のURL形式: {url}")
                return None
        except Exception as e:
            self.logger.error(f"URL処理エラー ({url}): {e}")
            return None

    def _extract_libecity_profile(self, url: str) -> Optional[Dict[str, Any]]:
        """リベシティのプロフィールページから情報を抽出"""
        try:
            # 常にログインを実行
            self._login_to_libecity()

            response = self._fetch_profile_page(url)
            if not response:
                self.logger.warning(f"プロフィールページの取得に失敗: {url}")
                return None

            profile_info = self._parse_profile_html(response, url)
            if profile_info:
                return profile_info
            else:
                self.logger.warning(f"プロフィール情報の解析に失敗: {url}")
                return None

        except Exception as e:
            self.logger.error(f"プロフィール抽出エラー ({url}): {e}")
            return None

    def _login_to_libecity(self) -> None:
        """リベシティにログイン"""
        try:
            self.logger.info("リベシティへのログインを開始します...")

            # まずメインページにアクセスしてセッションを初期化
            main_response = HttpUtils.safe_request(self.session, "https://libecity.com")
            if not main_response:
                self.logger.error("メインページへのアクセスに失敗しました")
                return

            # サインインページにアクセス
            signin_url = "https://libecity.com/signin"
            signin_response = HttpUtils.safe_request(self.session, signin_url)
            if not signin_response:
                self.logger.error("サインインページへのアクセスに失敗しました")
                return

            signin_soup = BeautifulSoup(signin_response.content, 'html.parser')
            self.logger.info(f"サインインページタイトル: {signin_soup.find('title').get_text() if signin_soup.find('title') else 'タイトルなし'}")

            # CSRFトークンを抽出
            csrf_token = self._extract_csrf_token(signin_soup)
            if csrf_token:
                self.logger.info(f"CSRFトークンを取得: {csrf_token[:20]}...")

            # ログインデータを準備
            login_data = {
                'email': 'eleven9terror@gmail.com',
                'password': 'bluearms109'
            }
            if csrf_token:
                login_data['_token'] = csrf_token

            self.logger.info("ログインを試行します...")
            login_response = self.session.post(signin_url, data=login_data, timeout=config.REQUEST_TIMEOUT, allow_redirects=True)

            self.logger.info(f"ログイン試行結果: {login_response.status_code}")
            self.logger.info(f"最終URL: {login_response.url}")

            # ログイン成功の確認
            if login_response.status_code in [200, 302]:
                # ログイン後のページ内容を確認
                login_result_soup = BeautifulSoup(login_response.content, 'html.parser')

                # ログアウトリンクの存在を確認
                logout_link = login_result_soup.find('a', href=lambda x: x and 'logout' in x)
                if logout_link:
                    self.logger.info("ログイン成功を確認: ログアウトリンクが見つかりました")
                else:
                    self.logger.warning("ログイン状態を確認できませんでした")

                # セッションクッキーを確認
                self.logger.info(f"ログイン後のセッションクッキー: {dict(self.session.cookies)}")

                # マイページにアクセスしてログイン状態を確認
                mypage_response = HttpUtils.safe_request(self.session, "https://libecity.com/mypage/home")
                if mypage_response:
                    mypage_soup = BeautifulSoup(mypage_response.content, 'html.parser')
                    mypage_title = mypage_soup.find('title')
                    if mypage_title:
                        self.logger.info(f"マイページタイトル: {mypage_title.get_text()}")

                    # マイページにアクセスできればログイン成功
                    if 'mypage' in mypage_response.url.lower():
                        self.logger.info("ログイン成功: マイページにアクセスできました")
                    else:
                        self.logger.warning("ログイン状態が不明です")
                else:
                    self.logger.warning("マイページへのアクセスに失敗しました")
            else:
                self.logger.error("ログインに失敗しました")

        except Exception as e:
            self.logger.error(f"ログインエラー: {e}")

    def _extract_csrf_token(self, soup: BeautifulSoup) -> Optional[str]:
        """CSRFトークンを抽出"""
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            return csrf_input.get('value')
        return None

    def _fetch_profile_page(self, url: str) -> Optional[requests.Response]:
        """プロフィールページを取得"""
        try:
            self.logger.info(f"プロフィールページにアクセス: {url}")

            response = HttpUtils.safe_request(self.session, url)
            if not response:
                return None

            # プロフィールページかどうかを確認
            if not self._is_valid_profile_page(response):
                self._save_debug_info(response, url)
                return None

            return response

        except Exception as e:
            self.logger.error(f"プロフィールページ取得エラー: {e}")
            return None

    def _is_valid_profile_page(self, response: requests.Response) -> bool:
        """プロフィールページかどうかを確認"""
        soup = BeautifulSoup(response.content, 'html.parser')

        # HTMLの内容をログに出力してデバッグ
        title = soup.find('title')
        title_text = title.get_text() if title else 'タイトルなし'
        self.logger.info(f"HTMLタイトル: {title_text}")

        # より柔軟な判定条件
        profile_indicators = [
            # タイトルにプロフィールが含まれる
            lambda: title and 'プロフィール' in title_text,
            # content_titleクラスが存在する
            lambda: soup.find('h3', class_='content_title') is not None,
            # 自己紹介フィールドが存在する
            lambda: soup.find('dt', string='自己紹介') is not None,
            # ユーザー名が存在する
            lambda: soup.find('h3', class_='content_title') is not None,
            # プロフィール関連の要素が存在する
            lambda: soup.find('dt') is not None and soup.find('dd') is not None,
            # ログインページでないことを確認
            lambda: 'signin' not in response.url.lower() and 'ログイン' not in soup.get_text(),
            # エラーページでないことを確認
            lambda: 'error' not in soup.get_text().lower() and 'エラー' not in soup.get_text(),
            # 認証が必要なページでないことを確認
            lambda: '認証' not in soup.get_text() and 'auth' not in response.url.lower(),
        ]

        # いずれかの条件を満たせばプロフィールページとみなす
        for i, indicator in enumerate(profile_indicators):
            try:
                if indicator():
                    self.logger.info(f"プロフィールページを確認しました (条件{i+1})")
                    return True
            except Exception as e:
                self.logger.warning(f"プロフィール判定エラー (条件{i+1}): {e}")
                continue

        # サイズチェックは警告として記録するが、判定からは除外
        if len(response.content) < config.MIN_PROFILE_SIZE:
            self.logger.warning(f"レスポンスサイズが小さい: {len(response.content)} bytes")

        # 最後の手段として、HTMLに何らかの内容があるかチェック
        if len(soup.get_text().strip()) > 100:
            self.logger.info("HTMLに十分な内容があるため、プロフィールページとして処理します")
            return True

        return False

    def _save_debug_info(self, response: requests.Response, url: str) -> None:
        """デバッグ情報を保存"""
        try:
            debug_file = config.DEBUG_FILE
            FileUtils.ensure_directory(os.path.dirname(debug_file))

            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== {url} ===\n")
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Content Length: {len(response.content)} bytes\n")
                f.write(f"Content Type: {response.headers.get('content-type', 'unknown')}\n")
                f.write(f"Final URL: {response.url}\n")
                f.write("=" * 50 + "\n")

            self.logger.info(f"デバッグ情報を追加しました: {debug_file}")

        except Exception as e:
            self.logger.error(f"デバッグ情報保存エラー: {e}")

    def _parse_profile_html(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """HTMLからプロフィール情報を解析"""
        soup = BeautifulSoup(response.content, 'html.parser')

        profile_info = {
            'url': url,
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # HTMLの内容をデバッグ出力
        self.logger.info(f"HTML内容の長さ: {len(soup.get_text())} 文字")
        self.logger.info(f"HTML要素数: {len(soup.find_all())} 個")

        # HTMLの生の内容を確認
        raw_html = response.content.decode('utf-8', errors='ignore')
        self.logger.info(f"生HTMLの長さ: {len(raw_html)} 文字")
        self.logger.info(f"生HTMLの先頭100文字: {raw_html[:100]}")

        # エンコーディングの問題を確認
        self.logger.info(f"レスポンスエンコーディング: {response.encoding}")
        self.logger.info(f"レスポンスContent-Type: {response.headers.get('content-type', 'unknown')}")

        # 各フィールドの抽出を試行
        extraction_methods = [
            self._extract_username,
            self._extract_bio_and_related,
            self._extract_basic_info,
            self._extract_skills_and_duration
        ]

        for method in extraction_methods:
            try:
                method(soup, profile_info)
            except Exception as e:
                self.logger.warning(f"プロフィール抽出エラー ({method.__name__}): {e}")

        # 抽出された情報をログ出力
        self.logger.info(f"抽出されたプロフィール情報: {list(profile_info.keys())}")

        # 最低限の情報があれば成功とする（より緩い条件）
        if len(profile_info) > 2:  # URLとextracted_at以外の情報がある
            self.logger.info(f"プロフィール情報を抽出しました: {url}")
            return profile_info
        else:
            # 部分的な情報でも保存
            self.logger.warning(f"プロフィール情報の抽出に部分的に失敗しました: {url}")
            # 基本的な情報を追加
            profile_info['partial_extraction'] = True
            profile_info['html_content_length'] = len(response.content)
            profile_info['html_text_length'] = len(soup.get_text())
            return profile_info

    def _extract_username(self, soup: BeautifulSoup, profile_info: Dict[str, Any]) -> None:
        """ユーザー名を抽出"""
        username_elem = soup.find('h3', class_='content_title')
        if username_elem:
            username_text = username_elem.get_text(strip=True)
            username_text = username_text.replace('さんのプロフィール', '').strip()
            if username_text and len(username_text) < 50:
                profile_info['username'] = username_text
                self.logger.info(f"ユーザー名を抽出: {username_text}")

    def _extract_bio_and_related(self, soup: BeautifulSoup, profile_info: Dict[str, Any]) -> None:
        """自己紹介と関連情報を抽出"""
        bio_text = DataUtils.extract_field_value(soup, '自己紹介')
        if bio_text:
            profile_info['bio'] = bio_text
            self.logger.info(f"自己紹介を抽出: {bio_text[:50]}...")

            # 自己紹介から関連情報を抽出
            self._extract_work_history_from_bio(bio_text, profile_info)
            self._extract_likes_from_bio(bio_text, profile_info)
            self._extract_strengths_from_bio(bio_text, profile_info)

    def _extract_work_history_from_bio(self, bio_text: str, profile_info: Dict[str, Any]) -> None:
        """自己紹介から仕事履歴を抽出"""
        if '仕事💼：' in bio_text:
            work_start = bio_text.find('仕事💼：')
            work_text = bio_text[work_start:]
            next_section = work_text.find('\n\n')
            if next_section != -1:
                work_text = work_text[:next_section]
            profile_info['work_history'] = work_text
            self.logger.info(f"仕事履歴を抽出: {work_text[:50]}...")

    def _extract_likes_from_bio(self, bio_text: str, profile_info: Dict[str, Any]) -> None:
        """自己紹介から好きなことを抽出"""
        if '好きなこと🌟：' in bio_text:
            likes_start = bio_text.find('好きなこと🌟：')
            likes_end = bio_text.find('得意なこと🧠：')
            if likes_start != -1 and likes_end != -1:
                likes_text = bio_text[likes_start:likes_end].replace('好きなこと🌟：', '').strip()
                profile_info['likes'] = likes_text
                self.logger.info(f"好きなことを抽出: {likes_text}")

    def _extract_strengths_from_bio(self, bio_text: str, profile_info: Dict[str, Any]) -> None:
        """自己紹介から得意なことを抽出"""
        if '得意なこと🧠：' in bio_text:
            strengths_start = bio_text.find('得意なこと🧠：')
            work_start = bio_text.find('仕事💼：')
            if strengths_start != -1 and work_start != -1:
                strengths_text = bio_text[strengths_start:work_start].replace('得意なこと🧠：', '').strip()
                profile_info['strengths'] = strengths_text
                self.logger.info(f"得意なことを抽出: {strengths_text}")

    def _extract_basic_info(self, soup: BeautifulSoup, profile_info: Dict[str, Any]) -> None:
        """基本情報を抽出"""
        basic_fields = [
            ('出身地', 'birthplace'),
            ('職種・職業', 'occupation'),
            ('家族構成', 'family'),
            ('リベ大との出会い', 'libecity_encounter'),
            ('挑戦、実践していること、これからやりたいことなど', 'challenges'),
            ('趣味・特技', 'hobbies'),
            ('好きな〇〇', 'likes')
        ]

        for field_name, key in basic_fields:
            value = DataUtils.extract_field_value(soup, field_name)
            if value:
                profile_info[key] = value
                self.logger.info(f"{field_name}を抽出: {value[:50]}...")

    def _extract_skills_and_duration(self, soup: BeautifulSoup, profile_info: Dict[str, Any]) -> None:
        """スキルと在籍期間を抽出"""
        # 経歴・スキル
        skills_text = DataUtils.extract_field_value(soup, '経歴・スキル')
        if skills_text:
            profile_info['skills'] = skills_text
            self.logger.info(f"経歴・スキルを抽出: {skills_text[:50]}...")

        # 在籍期間
        duration_text = DataUtils.extract_field_value(soup, '在籍期間')
        if duration_text:
            profile_info['duration'] = duration_text
            self.logger.info(f"在籍期間を抽出: {duration_text}")


class DataMerger:
    """データ統合クラス"""

    @staticmethod
    def merge_duplicate_participants(participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複する参加者データを統合"""
        merged_participants = []
        processed_names = set()

        for participant in participants:
            nickname = participant.get('nickname', '').strip()
            if not nickname:
                continue

            if nickname in processed_names:
                existing_index = DataMerger._find_existing_participant(merged_participants, nickname)
                if existing_index is not None:
                    merged = DataMerger._merge_participant_data(
                        merged_participants[existing_index], participant
                    )
                    merged_participants[existing_index] = merged
                    print(f"重複データを統合しました: {nickname}")
                else:
                    merged_participants.append(participant)
            else:
                merged_participants.append(participant)
                processed_names.add(nickname)

        return merged_participants

    @staticmethod
    def _find_existing_participant(participants: List[Dict[str, Any]], nickname: str) -> Optional[int]:
        """既存の参加者を検索"""
        for i, existing in enumerate(participants):
            if existing.get('nickname', '').strip() == nickname:
                return i
        return None

    @staticmethod
    def _merge_participant_data(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """参加者データを統合"""
        return DataUtils.merge_dicts(existing, new)


class DebugFileCleaner:
    """デバッグファイル整理クラス"""

    @staticmethod
    def clean_debug_files():
        """デバッグファイルを整理"""
        try:
            # 既存のdebug_infoとdebug_pageファイルを削除
            debug_files = glob.glob("output/debug_*")
            for file in debug_files:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"削除: {file}")

            # 新しいデバッグサマリーファイルを作成
            with open(config.DEBUG_FILE, 'w', encoding='utf-8') as f:
                f.write("=== デバッグ情報サマリー ===\n")
                f.write(f"作成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")

            print("デバッグファイルを整理しました")

        except Exception as e:
            print(f"デバッグファイル整理エラー: {e}")


class DataProcessor:
    """データ処理クラス"""

    def __init__(self):
        # 環境変数を読み込み
        load_dotenv()
        self.logger = Logger.setup_logger(__name__)
        self.profile_extractor = ProfileExtractor()

    def load_csv_data(self) -> Optional[pd.DataFrame]:
        """CSVファイルからデータを読み込み"""
        try:
            df = pd.read_csv(config.CSV_FILE)
            self.logger.info(f"CSVファイルを読み込みました: {len(df)}件のデータ")
            return df
        except FileNotFoundError:
            self.logger.error(f"エラー: {config.CSV_FILE} が見つかりません")
            return None
        except Exception as e:
            self.logger.error(f"CSVファイル読み込みエラー: {e}")
            return None

    def process_participant_data(self, row: pd.Series) -> Dict[str, Any]:
        """参加者データを処理"""
        participant = {
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
            'submitted': row.get('本人提出済', '') == '済'
        }

        # URLからプロフィール情報を取得
        if participant['profile_url']:
            profile_info = self.profile_extractor.extract_profile_from_url(participant['profile_url'])
            if profile_info:
                participant['profile_info'] = profile_info

        return participant

    def save_processed_data(self, participants: List[Dict[str, Any]]) -> None:
        """処理済みデータをJSONファイルに保存"""
        try:
            output_data = {
                'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_participants': len(participants),
                'participants': participants
            }

            if FileUtils.safe_write_json(output_data, config.PROCESSED_DATA_FILE):
                self.logger.info(f"処理済みデータを保存しました: {config.PROCESSED_DATA_FILE}")
                self.logger.info(f"参加者数: {len(participants)}人")
            else:
                self.logger.error("データ保存に失敗しました")

        except Exception as e:
            self.logger.error(f"データ保存エラー: {e}")

    def run(self) -> None:
        """メイン処理"""
        self.logger.info("=== Skill-Zero Analyzer - Data Processor ===")
        self.logger.info("データ処理を開始します...")

        # デバッグファイルを整理
        DebugFileCleaner.clean_debug_files()

        # CSVデータを読み込み
        df = self.load_csv_data()
        if df is None:
            return

        # 参加者データを処理
        participants = []
        for index, row in df.iterrows():
            participant = self.process_participant_data(row)
            if participant:
                participants.append(participant)
                self.logger.info(f"参加者データを処理しました: {participant['nickname'] or '名前なし'}")

        # 重複データを統合
        self.logger.info("重複データの統合を開始...")
        merged_participants = DataMerger.merge_duplicate_participants(participants)
        self.logger.info(f"統合前: {len(participants)}人 → 統合後: {len(merged_participants)}人")

        # 処理済みデータを保存
        self.save_processed_data(merged_participants)

        self.logger.info("=== データ処理完了 ===")
        self.logger.info(f"処理された参加者数: {len(merged_participants)}人")
        self.logger.info(f"出力ファイル: {config.PROCESSED_DATA_FILE}")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()