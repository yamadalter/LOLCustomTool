import json
from datetime import timedelta
from cassiopeia.data import Side


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):  # Arrowオブジェクトはisoformat()メソッドを持つ
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)  # 文字列に変換
        elif isinstance(obj, Side):  # Sideオブジェクトを処理
            return obj.name  # Sideオブジェクトのname属性を返す
        return super().default(obj)  # その他のオブジェクトはデフォルトの処理
