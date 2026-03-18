import io
from ebooklib import epub

def create_epub(book_title, book_author, book_language, cover_bytes, edited_toc, chapters_data):
    book = epub.EpubBook()
    book.set_identifier("id123456")
    book.set_title(book_title)
    book.set_language(book_language)
    book.add_author(book_author)

    if cover_bytes:
        book.set_cover("cover.jpg", cover_bytes)

    epub_chapters = []
    
    for i, row in enumerate(edited_toc):
        final_title = row["Title"]
        original_lines = chapters_data[i]["lines"]
        
        file_name = f"chapter_{i}.xhtml"
        chapter = epub.EpubHtml(title=final_title, file_name=file_name, lang=book_language)
        
        html_content = ["<html><head></head><body>"]
        html_content.append(f"<h1>{final_title.replace('<', '&lt;').replace('>', '&gt;')}</h1>")
        
        for line in original_lines[1:]:
            line_safe = line.replace("<", "&lt;").replace(">", "&gt;")
            if not line_safe:
                html_content.append("<p>&nbsp;</p>")
            else:
                html_content.append(f"<p>{line_safe}</p>")
                
        html_content.append("</body></html>")
        chapter.content = "\n".join(html_content)
        
        book.add_item(chapter)
        epub_chapters.append(chapter)

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + epub_chapters

    epub_io = io.BytesIO()
    epub.write_epub(epub_io, book)
    
    return epub_io.getvalue()
