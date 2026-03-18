def generate_chinese_html_files(edited_toc, chapters_data):
    """
    Generates HTML, formatting Volume as <h1> and Chapter as <h2>.
    """
    html_files = {}
    
    for i, row in enumerate(edited_toc):
        final_title = row["Title"]
        chap_data = chapters_data[i]
        volume_title = chap_data.get("volume", "")
        original_lines = chap_data["lines"]
        
        html_content = [
            "<html>", 
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{final_title}</title>",
            "</head>", 
            "<body>"
        ]
        
        # If it's the "Information" chapter, just use h1
        if i == 0 and final_title == "Information":
            html_content.append(f"<h1>{final_title}</h1>")
            for line in original_lines[1:]:
                line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
                html_content.append(f"<p>{line_safe}</p>")
        else:
            # Output Volume as <h1> and Chapter as <h2>
            if volume_title:
                html_content.append(f"<h1>{volume_title.replace('<', '&lt;').replace('>', '&gt;')}</h1>")
            
            html_content.append(f"<h2>{final_title.replace('<', '&lt;').replace('>', '&gt;')}</h2>")
            
            # Append the rest as <p>, skipping index 0 (the raw chapter title)
            for line in original_lines[1:]:
                line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
                if not line_safe:
                    html_content.append("<p>&nbsp;</p>")
                else:
                    html_content.append(f"<p>{line_safe}</p>")
                
        html_content.append("</body>")
        html_content.append("</html>")
        
        file_name = f"chapter_{i:04d}.html"
        html_files[file_name] = "\n".join(html_content)
        
    return html_files
