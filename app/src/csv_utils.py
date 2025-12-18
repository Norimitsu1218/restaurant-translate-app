from typing import List

def is_valid_row(row: List[str], ignore_keywords: List[str]) -> bool:
    """
    CSVの行が有効かどうかを判定する
    
    Args:
        row (List[str]): CSVの1行
        ignore_keywords (List[str]): 無視するキーワードのリスト
    
    Returns:
        bool: 有効な行の場合True
    """
    # 行が3列未満の場合は無効
    if len(row) < 3:
        return False
    
    # キーワード列に無視するキーワードが含まれている場合は無効
    if row[0] in ignore_keywords:
        return False
    
    # メニュー名と説明文が両方存在する場合のみ有効
    return len(row) >= 3 and row[1] and row[2]