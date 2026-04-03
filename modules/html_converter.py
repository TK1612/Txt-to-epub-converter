import re

def is_invisible(text):
    """
    Checks if a string is completely empty OR contains only invisible characters 
    (like zero-width spaces, ideographic spaces).
    """
    return bool(re.match(r'^[\s\u200B-\u200D\uFEFF\u3000\xA0]*$', text))

def generate_html_files(edited_toc, chapters_data, search_pattern=None, replace_pattern=None):
    html_files = {}
    
    # Matches inner chapter titles: "262화.", "제 311 화", "2부 1화.", "2부 80화.", "프롤로그"
    inner_title_pattern = re.compile(
        r"^\s*(?:제\s*)?(?:\d+\s*[부편]\s*)?\d+\s*화\.?\s*$|"
        r"^\s*(?:프롤로그|에필로그|외전)\.?\s*$", 
        re.IGNORECASE
    )
    
    for i, row in enumerate(edited_toc):
        final_title = row["Title"]
        original_lines = chapters_data[i]["lines"]
        
        html_content = [
            "<html>", 
            "<head>",
            "<meta charset='UTF-8'>",
            # The <title> tag remains the primary title (e.g., 제311화)
            f"<title>{final_title}</title>",
            "</head>", 
            "<body>"
        ]
        
        # Default H1 is the primary title, but we will try to overwrite it
        h1_text = final_title.replace('<', '&lt;').replace('>', '&gt;')
        h1_set = False
        processed_body_lines = []
        
        for line in original_lines[1:]:
            line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
            
            if not h1_set:
                if is_invisible(line_safe):
                    continue  # Skip leading grey blocks/empty spaces before the H1
                    
                # We found the first visible line of the chapter text!
                # Check if it matches our secondary chapter criteria (like "311화.")
                if inner_title_pattern.match(line_safe.replace("&lt;", "<").replace("&gt;", ">")):
                    h1_text = line_safe  # Overwrite H1 with this secondary title
                else:
                    # It doesn't match, so we keep the default H1 and add this as a paragraph
                    processed_body_lines.append(f"<p>{line_safe}</p>")
                
                h1_set = True
            else:
                if is_invisible(line_safe):
                    processed_body_lines.append("<p>&nbsp;</p>")
                else:
                    # DUPLICATE CHECK: Prevent identical <p> directly under <h1>
                    # We strip out punctuation and spaces to make sure they are truly identical
                    clean_h1 = re.sub(r'[\s\.\-]', '', h1_text)
                    clean_line = re.sub(r'[\s\.\-]', '', line_safe)
                    
                    if clean_line and clean_h1 == clean_line:
                        continue  # Skip this line entirely
                        
                    processed_body_lines.append(f"<p>{line_safe}</p>")
                    
        # Insert the finalized H1 before the body lines
        html_content.append(f"<h1>{h1_text}</h1>")
        html_content.extend(processed_body_lines)
        
        html_content.append("</body>")
        html_content.append("</html>")
        
        html_str = "\n".join(html_content)
        
        # --- APPLY UI CUSTOM REGEX (if checked in the app) ---
        if search_pattern and replace_pattern:
            try:
                html_str = re.sub(search_pattern, replace_pattern, html_str)
            except Exception:
                pass 
        
        file_name = f"chapter_{i:04d}.html"
        html_files[file_name] = html_str
        
    return html_files
