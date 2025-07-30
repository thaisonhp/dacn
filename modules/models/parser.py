from markitdown import MarkItDown


class MarkItDownParser:
    def __init__(self, enable_plugins=False):
        self.md = MarkItDown(enable_plugins=enable_plugins)

    def parse(self, file_path: str) -> dict:
        # Thử các encoding khác nhau nếu UTF-8 fail
        result = self.md.convert(file_path)
        print(
            f"Parsed content from {file_path}: {result.text_content[:100]}..."
        )  # Hiển thị 100 ký tự đầu tiên
        return {
            "text": result.text_content,
            "metadata": {
                "file_path": file_path,
                "html": getattr(result, "html", None),
                "toc": getattr(result, "toc", None),
            },
        }
