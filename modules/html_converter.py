def generate_html_files(edited_toc, chapters_data):
    """
    Takes the edited TOC and chapter lines, returning a dictionary
    where keys are filenames and values are the formatted HTML strings.
    """
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
        
        # Force the edited title as the <h1> tag
        html_content.append(f"<h1>{final_title.replace('<', '&lt;').replace('>', '&gt;')}</h1>")
        
        # Append the rest of the lines as <p> tags, skipping index 0 (the old title)
        for line in original_lines[1:]:
            line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
            if not line_safe:
                html_content.append("<p>&nbsp;</p>")
            else:
                html_content.append(f"<p>{line_safe}</p>")
                
        html_content.append("</body>")
        html_content.append("</html>")
        
        # Pad numbers with zeros (e.g., chapter_0001.html) to keep them sorted in Sigil
        file_name = f"chapter_{i:04d}.html"
        html_files[file_name] = "\n".join(html_content)
        
    return html_files
