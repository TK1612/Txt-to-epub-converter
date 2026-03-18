import streamlit as st
import re
import io
from ebooklib import epub

# --- PAGE SETUP ---
st.set_page_config(page_title="Text to EPUB Converter", page_icon="📚", layout="centered")

st.title("📚 Novel to EPUB Converter")
st.write("Upload your raw text, set your metadata, and generate a fully formatted EPUB.")

# --- REGEX PATTERNS (From your script) ---
primary_pattern = re.compile(
    ur"^(?:.*?(\d+)화\s*)?(외전)\s*([\d\-]+)(?=\s|$|\W|[화편부상중하])|"
    ur"^[^\w\s]*(\d+)화.*\((\d+)\)(?=\s|$|\W)|"
    ur".*?\s(\d+)화$|"
    ur"^[^\w\s]*(\d+)화(?![.\s]*프롤로그)(?=\s|$|\W|[편부상중하])|"
    ur"^[^\w\s]*(?:0[화\.]*\s*)?(프롤로그)(?=\s|$|\W)",
    re.UNICODE
)

fallback_pattern = re.compile(
    ur"^[^\w\s]*(\d+)\.\s+.*\((\d+)\)|"
    ur"^[^\w\s]*(\d+)\.\s+",
    re.UNICODE
)

# --- UI: FILE UPLOAD & METADATA ---
uploaded_file = st.file_uploader("1. Upload raw .txt file", type=["txt"])

st.subheader("2. Book Metadata & Cover")
col1, col2 = st.columns(2)
with col1:
    book_title = st.text_input("Book Title", value="My Awesome Novel")
    book_author = st.text_input("Author", value="Unknown Author")
with col2:
    book_language = st.text_input("Language Code", value="ko")
    cover_image = st.file_uploader("Upload Cover Image (Optional)", type=["jpg", "jpeg", "png"])

# --- CORE LOGIC ---
if uploaded_file is not None and st.button("3. Process and Build EPUB"):
    with st.spinner("Processing text and building EPUB..."):
        
        # 1. Read the uploaded file
        text = uploaded_file.getvalue().decode("utf-8")
        lines = text.splitlines()
        
        chapters_data = []
        current_chapter_lines = []
        current_title = "Start"
        
        last_main_chapter = 0
        current_active_chapter_num = -1
        lines_since_last_split = 9999
        extracted_prologue = False

        # --- STEP 1: SPLIT TEXT (Adapted from your Splitbynumber_v2) ---
        for line in lines:
            clean_line = line.strip()
            lines_since_last_split += 1
            is_new_chapter = False
            val_to_check = -1
            
            primary_match = primary_pattern.match(clean_line)
            
            if primary_match:
                if primary_match.group(2) == u'외전': 
                    val_to_check = int(primary_match.group(1)) if primary_match.group(1) else last_main_chapter
                    is_new_chapter = True
                elif primary_match.group(4) or primary_match.group(6) or primary_match.group(7): 
                    val_to_check = int(primary_match.group(4) or primary_match.group(6) or primary_match.group(7))
                    is_new_chapter = True
                elif primary_match.group(8) == u'프롤로그' and not extracted_prologue and last_main_chapter == 0:
                    val_to_check = 0
                    is_new_chapter = True
                    extracted_prologue = True
            else:
                fallback_match = fallback_pattern.match(clean_line)
                if fallback_match:
                    matched_num = int(fallback_match.group(1) or fallback_match.group(3))
                    is_sequential = (last_main_chapter == 0) or (matched_num > last_main_chapter and (matched_num - last_main_chapter) <= 5)
                    if is_sequential and not (clean_line.endswith(u".") or clean_line.endswith(u"?") or clean_line.endswith(u"!")) and len(clean_line) <= 50:
                        val_to_check = matched_num
                        is_new_chapter = True

            # Anti-duplicate check
            if is_new_chapter:
                if val_to_check == current_active_chapter_num and lines_since_last_split < 20:
                    is_new_chapter = False
                else:
                    current_active_chapter_num = val_to_check
                    last_main_chapter = val_to_check

            # If new chapter hits, save the old one and start fresh
            if is_new_chapter:
                if current_chapter_lines:
                    chapters_data.append({"title": current_title, "lines": current_chapter_lines})
                current_title = clean_line # The matched line becomes the title
                current_chapter_lines = [clean_line]
                lines_since_last_split = 0
            else:
                current_chapter_lines.append(clean_line)

        # Save the very last chapter
        if current_chapter_lines:
            chapters_data.append({"title": current_title, "lines": current_chapter_lines})

        # --- STEP 2: BUILD EPUB (Integrating your HTML logic) ---
        book = epub.EpubBook()
        book.set_identifier("id123456")
        book.set_title(book_title)
        book.set_language(book_language)
        book.add_author(book_author)

        if cover_image:
            book.set_cover("cover.jpg", cover_image.getvalue())

        epub_chapters = []
        
        for i, ch_data in enumerate(chapters_data):
            # Create an EPUB chapter
            file_name = f"chapter_{i}.xhtml"
            chapter = epub.EpubHtml(title=ch_data["title"], file_name=file_name, lang=book_language)
            
            # Apply your HTML formatting logic
            html_content = ["<html><head></head><body>"]
            has_h1 = False
            
            for line in ch_data["lines"]:
                line_safe = line.replace(u"<", u"&lt;").replace(u">", u"&gt;")
                if not line_safe:
                    html_content.append(u"<p><br/></p>")
                elif not has_h1:
                    html_content.append(u"<h1>{}</h1>".format(line_safe))
                    has_h1 = True
                else:
                    html_content.append(u"<p>{}</p>".format(line_safe))
                    
            html_content.append("</body></html>")
            chapter.content = u"\n".join(html_content)
            
            book.add_item(chapter)
            epub_chapters.append(chapter)

        # Define Table of Contents and Spine (Reading order)
        book.toc = tuple(epub_chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        spine = ['nav'] + epub_chapters
        book.spine = spine

        # Write to memory instead of disk
        epub_io = io.BytesIO()
        epub.write_epub(epub_io, book)
        
        st.success(f"Successfully processed {len(epub_chapters)} chapters!")
        
        # Provide Download Button
        st.download_button(
            label="⬇️ Download EPUB",
            data=epub_io.getvalue(),
            file_name=f"{book_title}.epub",
            mime="application/epub+zip"
        )

# --- FOOTER ---
st.markdown("---")
st.markdown("""
### About the Developer
This was created to shit on Viery, as he dares to request 800 chapters, so i'm creating this to avoid doing his requests.
Any bug problems u can send a dm though @truongkoolvg4 (i'm not gonna reply to it mueheheheheh)
""")
