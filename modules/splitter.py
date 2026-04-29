import re

primary_pattern = re.compile(
    r"^(?:.*?(\d+)화\s*)?(외전)\s*([\d\-]+)(?=\s|$|\W|[화편부상중하])|"
    r"^[^\w\s]*(\d+)화.*\((\d+)\)(?=\s|$|\W)|"
    r".*?\s(\d+)화$|"
    r"^[^\w\s]*(\d+)화(?![.\s]*프롤로그)(?=\s|$|\W|[편부상중하])|"
    r"^[^\w\s]*(?:0[화\.]*\s*)?(프롤로그)(?=\s|$|\W)",
    re.UNICODE
)

fallback_pattern = re.compile(
    r"^[^\w\s]*(?:제\s*)?(?:(\d+)\s*부\s*)?(\d+)\s*화|" 
    r"^[^\w\s]*(\d+)\.\s+.*\((\d+)\)|"
    r"^[^\w\s]*(\d+)\.\s+",
    re.UNICODE
)

# Newest fallback pattern for Volume formatting
vol_pattern = re.compile(r"^[vV]ol\s*:.*", re.UNICODE)

def merge_vol_paragraphs(lines):
    """
    Merges broken lines into single paragraphs. Starts a new paragraph 
    only when it encounters a blank line.
    """
    merged_lines = []
    current_paragraph = []
    
    for line in lines:
        if not line.strip():  # If it's a blank line
            if current_paragraph:
                # Join the accumulated lines with a space
                merged_lines.append(" ".join(current_paragraph))
                current_paragraph = []
            merged_lines.append(line)  # Preserve the blank line to maintain structure
        else:
            current_paragraph.append(line.strip())
            
    # Flush any remaining text at the end
    if current_paragraph:
        merged_lines.append(" ".join(current_paragraph))
        
    return merged_lines

def extract_chapters(text):
    lines = text.splitlines()
    chapters_data = []
    current_chapter_lines = []
    current_title = "Start"
    
    last_main_chapter = 0
    current_active_chapter_num = -1
    lines_since_last_split = 9999
    extracted_prologue = False
    
    found_numbers = []
    
    # Tracks if the CURRENT block being read was triggered by the 'vol :' pattern
    current_is_vol_format = False 

    for line in lines:
        clean_line = line.strip()
        lines_since_last_split += 1
        is_new_chapter = False
        val_to_check = -1
        is_vol_chapter_trigger = False
        
        primary_match = primary_pattern.match(clean_line)
        
        if primary_match:
            if primary_match.group(2) == '외전': 
                val_to_check = int(primary_match.group(1)) if primary_match.group(1) else last_main_chapter
                is_new_chapter = True
            elif primary_match.group(4) or primary_match.group(6) or primary_match.group(7): 
                val_to_check = int(primary_match.group(4) or primary_match.group(6) or primary_match.group(7))
                is_new_chapter = True
            elif primary_match.group(8) == '프롤로그' and not extracted_prologue and last_main_chapter == 0:
                val_to_check = 0
                is_new_chapter = True
                extracted_prologue = True
        else:
            fallback_match = fallback_pattern.match(clean_line)
            if fallback_match:
                if fallback_match.group(2):
                    matched_num = int(fallback_match.group(2))
                    is_sequential = (last_main_chapter == 0) or (matched_num > last_main_chapter and (matched_num - last_main_chapter) <= 5)
                    if is_sequential and len(clean_line) <= 50:
                        val_to_check = matched_num
                        is_new_chapter = True
                else:
                    matched_num = int(fallback_match.group(3) or fallback_match.group(5))
                    is_sequential = (last_main_chapter == 0) or (matched_num > last_main_chapter and (matched_num - last_main_chapter) <= 5)
                    if is_sequential and not (clean_line.endswith(".") or clean_line.endswith("?") or clean_line.endswith("!")) and len(clean_line) <= 50:
                        val_to_check = matched_num
                        is_new_chapter = True
            else:
                # NEW: Check for the vol : pattern
                vol_match = vol_pattern.match(clean_line)
                if vol_match:
                    is_new_chapter = True
                    is_vol_chapter_trigger = True
                    val_to_check = -999 # Sentinel value to prevent messing up the sequence scanner

        if is_new_chapter:
            if val_to_check == current_active_chapter_num and lines_since_last_split < 20:
                is_new_chapter = False
            else:
                current_active_chapter_num = val_to_check
                if val_to_check != -999: # Only track numeric sequences
                    last_main_chapter = val_to_check
                    if val_to_check >= 0:
                        found_numbers.append(val_to_check)

        if is_new_chapter:
            # We are closing the previous chapter block
            if current_chapter_lines:
                # If the previous chapter was a Vol chapter, fix the line breaks
                if current_is_vol_format:
                    current_chapter_lines = merge_vol_paragraphs(current_chapter_lines)
                    
                chapters_data.append({"title": current_title, "lines": current_chapter_lines})
                
            # Initialize the new chapter
            current_title = clean_line 
            current_chapter_lines = [clean_line]
            lines_since_last_split = 0
            current_is_vol_format = is_vol_chapter_trigger
        else:
            current_chapter_lines.append(clean_line)

    # Final append for the very last chapter in the file
    if current_chapter_lines:
        if current_is_vol_format:
            current_chapter_lines = merge_vol_paragraphs(current_chapter_lines)
        chapters_data.append({"title": current_title, "lines": current_chapter_lines})
        
    return chapters_data, found_numbers
