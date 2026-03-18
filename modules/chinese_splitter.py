import re

def extract_chinese_chapters(text):
    """
    Extracts metadata into an Information chapter and splits the rest by Chinese volume/chapter markers.
    """
    # Patterns for Volumes (e.g., 第一卷) and Chapters (e.g., 1、 or 第一章)
    volume_pattern = re.compile(r'^(第[一二三四五六七八九十百千万零]+卷.*)', re.MULTILINE)
    chapter_pattern = re.compile(r'^(\d+、.*|第[一二三四五六七八九十百千万零]+章.*)', re.MULTILINE)

    # 1. Split text into Info Block and Main Content
    first_vol_match = volume_pattern.search(text)
    if first_vol_match:
        info_text = text[:first_vol_match.start()].strip()
        main_text = text[first_vol_match.start():]
    else:
        info_text = text.strip()
        main_text = ""

    # 2. Extract Metadata from Info Block
    author_match = re.search(r'作者：(.*)', info_text)
    author = author_match.group(1).strip() if author_match else "Unknown Author"
    
    title = "Unknown Title"
    if author_match:
        title_segment = info_text[:author_match.start()].strip()
        title_lines = [line for line in title_segment.split('\n') if line.strip()]
        if title_lines:
            title = title_lines[-1] # The line right before the author is usually the title

    synopsis_match = re.search(r'简介：(.*)', info_text, re.DOTALL)
    synopsis = synopsis_match.group(1).strip() if synopsis_match else ""

    chapters_data = []

    # 3. Build the Information Chapter
    info_lines = ["Information", f"Title: {title}", f"Author: {author}"]
    if synopsis:
        info_lines.append("Synopsis:")
        info_lines.extend(synopsis.split('\n'))

    chapters_data.append({
        "volume": "",
        "title": "Information",
        "lines": info_lines
    })

    # 4. Parse Main Text (Volumes & Chapters)
    lines = main_text.split('\n')
    current_volume = ""
    current_chapter = ""
    current_lines = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str: continue
        
        # If we hit a Volume, we update the tracker but DO NOT create a new isolated file
        if volume_pattern.match(line_str):
            current_volume = line_str
            continue
        
        # If we hit a Chapter, we save the previous one and start a new file
        if chapter_pattern.match(line_str):
            if current_chapter:
                chapters_data.append({
                    "volume": current_volume,
                    "title": current_chapter,
                    "lines": current_lines
                })
            current_chapter = line_str
            current_lines = [current_chapter]
        else:
            if current_chapter:
                current_lines.append(line_str)

    # Append the final chapter
    if current_chapter:
        chapters_data.append({
            "volume": current_volume,
            "title": current_chapter,
            "lines": current_lines
        })

    return title, author, chapters_data
