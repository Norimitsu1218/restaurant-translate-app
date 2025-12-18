from dataclasses import dataclass
from typing import Dict, List

@dataclass
class MenuItem:
    """
    メニュー項目を表すデータクラス
    
    Attributes:
        menu_title (str): メニューのタイトル
        menu_content (str): メニューの説明文
    """
    menu_title: str
    menu_content: str
    
    def __str__(self) -> str:
        """
        人間が読みやすい形式で表示するための文字列表現
        """
        return f"【メニュー名】\n{self.menu_title}\n\n【説明文】\n{self.menu_content}"
    
    @classmethod
    def create_error(cls, error_message: str) -> 'MenuItem':
        """
        エラーを表すMenuItemを作成
        
        Args:
            error_message (str): エラーメッセージ
            
        Returns:
            MenuItem: エラー情報を含むMenuItem
        """
        return cls(
            menu_title="エラー",
            menu_content=error_message
        )
    
    def to_csv_row(self) -> List[str]:
        """
        CSV行として出力するためのリストを返す
        
        Returns:
            List[str]: [タイトル, 説明文]形式のリスト
        """
        return [self.menu_title, self.menu_content]
    
    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'MenuItem':
        """
        CSV行からMenuItemを作成
        
        Args:
            row (List[str]): [タイトル, 説明文]形式のリスト
            
        Returns:
            MenuItem: 作成されたMenuItem
        """
        if len(row) >= 2:
            return cls(menu_title=row[0], menu_content=row[1])
        return cls.create_error("CSVの行が不正です")

@dataclass
class TranslationSet:
    """
    1つのメニュー項目の多言語翻訳セットを表すデータクラス
    
    Attributes:
        japanese (MenuItem): 日本語のメニュー項目
        english (MenuItem): 英語のメニュー項目
        translations (Dict[str, MenuItem]): 他言語の翻訳（言語名: MenuItem）
    """
    japanese: MenuItem
    english: MenuItem
    translations: Dict[str, MenuItem]
    
    def to_csv_row(self) -> List[str]:
        """
        CSV行として出力するためのリストを返す
        
        Returns:
            List[str]: [日本語タイトル, 日本語説明, 英語タイトル, 英語説明, 他言語タイトル, 他言語説明, ...]
        """
        row = []
        # 日本語
        row.extend(self.japanese.to_csv_row())
        # 英語
        row.extend(self.english.to_csv_row())
        # その他の言語
        for menu_item in self.translations.values():
            row.extend(menu_item.to_csv_row())
        return row 