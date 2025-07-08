import sys, os

def resource_path(relative_path):
    """Возвращает правильный путь к файлу как в режиме разработки, так и в собранном exe."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

