import re

def is_invisible(text):
    """
    Checks if a string is completely empty OR contains only invisible characters 
    (like zero-width spaces, ideographic spaces).
    """
    return bool(re.match(r'^[\s\u200B-\u200D\uFEFF\u3000\xA0]*$', text))

def generate_html_files(edited_toc, chapters_data, search_pattern=None, replace_pattern=None, regex_rules=None, start_index=0):
    html_files = {}
    
    # Matches inner chapter titles: "262화.", "제 311 화", "2부 1화.", "2부 80화.", "프롤로그", "vol : 01"
    inner_title_pattern = re.compile(
        r"^\s*(?:제\s*)?(?:\d+\s*[부편]\s*)?\d+\s*화\.?\s*$|"
        r"^\s*(?:프롤로그|에필로그|외전)\.?\s*$|"
        r"^[vV]ol\s*:.*", 
        re.IGNORECASE
    )
    
    for local_i, row in enumerate(edited_toc):
        # Calculate the actual chapter index (vital for the preview function)
        actual_i = start_index + local_i 
        
        final_title = row["Title"]
        original_lines = chapters_data[local_i]["lines"]
        
        html_content = [
            "<html>", 
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{final_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</title>",
            "</head>", 
            "<body>"
        ]
        
        # CRITICAL FIX: Sanitize the main H1 title for strict XML/XHTML validation
        h1_text = final_title.replace("&", "&amp;").replace('<', '&lt;').replace('>', '&gt;')
        h1_set = False
        processed_body_lines = []
        
        for line in original_lines[1:]:
            # CRITICAL FIX: Escape '&' FIRST, then replace bracket characters
            line_safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            if not h1_set:
                if is_invisible(line_safe):
                    continue 
                    
                if inner_title_pattern.match(line_safe.replace("&lt;", "<").replace("&gt;", ">")):
                    h1_text = line_safe 
                else:
                    processed_body_lines.append(f"<p>{line_safe}</p>")
                
                h1_set = True
            else:
                if is_invisible(line_safe):
                    processed_body_lines.append("<p>&nbsp;</p>")
                else:
                    clean_h1 = re.sub(r'[\s\.\-]', '', h1_text)
                    clean_line = re.sub(r'[\s\.\-]', '', line_safe)
                    
                    if clean_line and clean_h1 == clean_line:
                        continue 
                        
                    processed_body_lines.append(f"<p>{line_safe}</p>")
                    
        html_content.append(f"<h1>{h1_text}</h1>")
        html_content.extend(processed_body_lines)
        
        html_content.append("</body>")
        html_content.append("</html>")
        
        html_str = "\n".join(html_content)
        
        # --- 1. APPLY GLOBAL REGEX ---
        if search_pattern and replace_pattern:
            try:
                html_str = re.sub(search_pattern, replace_pattern, html_str)
            except Exception:
                pass 

        # --- 2. APPLY RANGED REGEX RULES ---
        if regex_rules:
            for rule in regex_rules:
                if rule["start"] <= actual_i <= rule["end"]:
                    if rule["search"] and rule["replace"]:
                        try:
                            html_str = re.sub(rule["search"], rule["replace"], html_str)
                        except Exception:
                            pass
        
        file_name = f"chapter_{actual_i:04d}.html"
        html_files[file_name] = html_str
        
    return html_files
