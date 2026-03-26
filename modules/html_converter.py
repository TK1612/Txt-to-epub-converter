# modules/html_converter.py
import re

def generate_html_files(edited_toc, chapters_data, search_pattern=None, replace_pattern=None):
    html_files = {}
    
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
            if not line_safe:
                html_content.append("<p>&nbsp;</p>")
            else:
                html_content.append(f"<p>{line_safe}</p>")
                
        html_content.append("</body>")
        html_content.append("</html>")
        
        html_str = "\n".join(html_content)
        
        if search_pattern and replace_pattern:
            try:
                html_str = re.sub(search_pattern, replace_pattern, html_str)
            except Exception:
                pass 
        
        file_name = f"chapter_{i:04d}.html"
        html_files[file_name] = html_str
        
    return html_files
