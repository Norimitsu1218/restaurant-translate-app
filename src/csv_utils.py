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
    # 行が20列未満の場合は無効（最低でもT列=19まで必要）
    if len(row) < 20:
        return False
    
    # 0列目（A列）に無視キーワードが含まれているかチェック
    if row[0] in ignore_keywords:
        return False
    
    # S列(index 18) = メニュー名、T列(index 19) = 説明文
    # これらが存在する場合のみ有効
    return row[18] and row[19]