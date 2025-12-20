from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid
from datetime import datetime

@dataclass
class MenuItem:
    """
    メニュー項目 (MENU_MASTERのデータ構造に対応)
    
    Attributes:
        menu_title (str): メニュー名 (NAME_JA)
        menu_content (str): 説明文 (JA_18S_TEXT)
        id (str): 一意な識別子 (UUID)
        confidence (float): AI視覚解析(Multimodal)の確信度 (0.0-1.0)
        status (str): 状態 (pending, confirmed, etc.)
        category (str): カテゴリ (optional)
        price (int): 価格 (optional)
    """
    menu_title: str
    menu_content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 1.0 
    status: str = "pending"
    category: str = ""
    price: Optional[int] = None
    pairing: str = ""      # S1-04: Pairing suggestion
    search_tags: str = ""  # S1-04: Context/Tags
    
    def __str__(self) -> str:
        base = f"【メニュー名】{self.menu_title} (ID:{self.id[:4]}..)\n【説明】{self.menu_content}"
        if self.pairing:
            base += f"\n【ペアリング】{self.pairing}"
        return base
    
    @classmethod
    def create_error(cls, error_message: str) -> 'MenuItem':
        return cls(
            menu_title="エラー",
            menu_content=error_message,
            status="error",
            confidence=0.0
        )
    
    def to_csv_row(self) -> List[str]:
        # Legacy support for CSV format - append pairing to content for export visibility
        content_export = self.menu_content
        if self.pairing:
            content_export += f" [Pairing: {self.pairing}]"
        return [self.menu_title, content_export]
    
    @classmethod
    def from_csv_row(cls, row: List[str]) -> 'MenuItem':
        if len(row) >= 2:
            return cls(menu_title=row[0], menu_content=row[1])
        return cls.create_error("CSVの行が不正です")

@dataclass
class MenuMasterRow:
    """
    MENU_MASTER テーブルの1行を表す完全なデータモデル (Suzuka Spec)
    """
    tenant_id: str
    store_id: str
    plan_code: str
    item: MenuItem
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_by: str = "system"

@dataclass
class TranslationSet:
    """
    1つのメニュー項目の多言語翻訳セット
    """
    japanese: MenuItem
    english: MenuItem
    translations: Dict[str, MenuItem]
    
    def to_csv_row(self) -> List[str]:
        row = []
        row.extend(self.japanese.to_csv_row())
        row.extend(self.english.to_csv_row())
        for menu_item in self.translations.values():
            row.extend(menu_item.to_csv_row())
        return row 