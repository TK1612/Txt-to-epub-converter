import re

def is_invisible(text):
    """
    Checks if a string is completely empty OR contains only invisible characters 
    (like the grey blocks: zero-width spaces, ideographic spaces, non-breaking spaces).
    """
    return bool(re.match(r'^[\s\u200B-\u200D\uFEFF\u3000\xA0]*$', text))

def generate_html_files(edited_toc, chapters_data, search_pattern=None, replace_pattern=None):
    html_files = {}
    
    # NEW SCANNER REGEX:
    # 1. Finds an empty <h1> (even if filled with grey blocks/spaces)
    # 2. Finds any optional empty <p> tags right after it
    # 3. Finds the first <p> that contains chapter keywords (화, 부, 편, 프롤로그, 에필로그, 외전)
    # 4. Captures that title text to promote it to the H1.
    auto_scanner_pattern = re.compile(
        r"<h1>(?:[\s\u200B-\u200D\uFEFF\u3000\xA0]|&nbsp;)*</h1>"  
        r"(?:\s*<p>(?:[\s\u200B-\u200D\uFEFF\u3000\xA0]|&nbsp;)*</p>)*" 
        r"\s*<p>((?:(?!</p>).)*(?:\d+\s*[화편부]|프롤로그|에필로그|외전)(?:(?!</p>).)*)</p>", 
        re.IGNORECASE | re.DOTALL
    )
    
    for i, row in enumerate(edited_toc):
        final_title = row["Title"]
        original_lines = chapters_data[i]["lines"]
        
        html_content = [
            "<html>", 
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{final_title}</title>",
            "</head>", 
            "<body>"
        ]
        
        html_content.append(f"<h1>{final_title.replace('<', '&lt;').replace('>', '&gt;')}</h1>")
        
        for line in original_lines[1:]:
            line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
            
            # Check if the line is just one of those weird grey blocks or empty spaces
            if is_invisible(line_safe):
                html_content.append("<p>&nbsp;</p>")
            else:
                html_content.append(f"<p>{line_safe}</p>")
                
        html_content.append("</body>")
        html_content.append("</html>")
        
        html_str = "\n".join(html_content)
        
        # --- AUTOMATIC SCAN & FIX ---
        # If the H1 is blank and the next text is a title, fix it automatically!
        # If the H1 already has text (like your Image 3), this pattern won't match and it safely ignores it.
        html_str = auto_scanner_pattern.sub(r"<h1>\1</h1>", html_str)
        
        # --- APPLY UI CUSTOM REGEX (if checked in the app) ---
        if search_pattern and replace_pattern:
            try:
                html_str = re.sub(search_pattern, replace_pattern, html_str)
            except Exception:
                pass 
        
        file_name = f"chapter_{i:04d}.html"
        html_files[file_name] = html_str
        
    return html_files
