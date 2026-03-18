import io
from ebooklib import epub

def create_epub(book_title, book_author, book_language, cover_bytes, html_files_dict, edited_toc):
    book = epub.EpubBook()
    book.set_identifier("id123456")
    book.set_title(book_title)
    book.set_language(book_language)
    book.add_author(book_author)

    if cover_bytes:
        book.set_cover("cover.jpg", cover_bytes)

    epub_chapters = []
    
    for i, (file_name, html_string) in enumerate(html_files_dict.items()):
        # Pull the title from the TOC to label the chapter in the EPUB navigation
        final_title = edited_toc[i]["Title"]
        
        # EbookLib prefers .xhtml extensions internally
        internal_file_name = file_name.replace(".html", ".xhtml")
        
        chapter = epub.EpubHtml(title=final_title, file_name=internal_file_name, lang=book_language)
        chapter.content = html_string
        
        book.add_item(chapter)
        epub_chapters.append(chapter)

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + epub_chapters

    epub_io = io.BytesIO()
    epub.write_epub(epub_io, book)
    
    return epub_io.getvalue()
