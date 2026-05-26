def recursive_split(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: list[str] | None = None,
) -> list[str]:
    if separators is None:
        separators = ["\n\n", "\n", "。", "，", " ", ""]

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    for sep in separators:
        if sep == "":
            return _character_split(text, chunk_size, chunk_overlap)

        parts = text.split(sep)
        if len(parts) <= 1:
            continue

        chunks = []
        current = ""
        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > chunk_size:
                    sub_chunks = recursive_split(
                        part, chunk_size, chunk_overlap, separators[separators.index(sep) + 1:]
                    )
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part
        if current:
            chunks.append(current)

        if len(chunks) > 1:
            return _apply_overlap(chunks, chunk_overlap)

    return [text] if text.strip() else []


def _character_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return [c for c in chunks if c.strip()]


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap:]
        result.append(prev_tail + chunks[i])
    return result
