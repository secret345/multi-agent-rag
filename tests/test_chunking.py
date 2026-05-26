from rag.chunking import recursive_split


class TestRecursiveSplit:
    def test_short_text(self):
        text = "这是一段短文本"
        result = recursive_split(text, chunk_size=100)
        assert len(result) == 1
        assert result[0] == text

    def test_split_by_paragraph(self):
        text = "段落一的内容。" * 10 + "\n\n" + "段落二的内容。" * 10
        result = recursive_split(text, chunk_size=50, chunk_overlap=0)
        assert len(result) > 1

    def test_overlap(self):
        text = "A" * 100
        result = recursive_split(text, chunk_size=50, chunk_overlap=10)
        assert len(result) > 1
        assert result[0][-10:] == result[1][:10]

    def test_empty_text(self):
        result = recursive_split("", chunk_size=100)
        assert result == []

    def test_chinese_text(self):
        text = "这是一段中文文本。" * 50
        result = recursive_split(text, chunk_size=100, chunk_overlap=10)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 120
