import streamlit as st
import re
import io
from ebooklib import epub

# --- PAGE SETUP ---
st.set_page_config(page_title="Novel to EPUB Converter", page_icon="📚", layout="centered")

st.title("📚 Novel to EPUB Converter")
st.write("Upload your raw text, extract chapters, edit the Table of Contents, and generate your EPUB.")

# --- INITIALIZE SESSION STATE ---
# This allows the app to remember data between button clicks
if "chapters_data" not in st.session_state:
    st.session_state.chapters_data = []
if "epub_file" not in st.session_state:
    st.session_state.epub_file = None

# --- REGEX PATTERNS ---
primary_pattern = re.compile(
    r"^(?:.*?(\d+)화\s*)?(외전)\s*([\d\-]+)(?=\s|$|\W|[화편부상중하])|"
    r"^[^\w\s]*(\d+)화.*\((\d+)\)(?=\s|$|\W)|"
    r".*?\s(\d+)화$|"
    r"^[^\w\s]*(\d+)화(?![.\s]*프롤로그)(?=\s|$|\W|[편부상중하])|"
    r"^[^\w\s]*(?:0[화\.]*\s*)?(프롤로그)(?=\s|$|\W)",
    re.UNICODE
)

fallback_pattern = re.compile(
    r"^[^\w\s]*(\d+)\.\s+.*\((\d+)\)|"
    r"^[^\w\s]*(\d+)\.\s+",
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

# --- STEP 1: EXTRACT CHAPTERS ---
if uploaded_file is not None:
    if st.button("3. Extract Chapters"):
        with st.spinner("Scanning document and identifying chapters..."):
            text = uploaded_file.getvalue().decode("utf-8")
            lines = text.splitlines()
            
            chapters_data = []
            current_chapter_lines = []
            current_title = "Start"
            
            last_main_chapter = 0
            current_active_chapter_num = -1
            lines_since_last_split = 9999
            extracted_prologue = False

            for line in lines:
                clean_line = line.strip()
                lines_since_last_split += 1
                is_new_chapter = False
                val_to_check = -1
                
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
                        matched_num = int(fallback_match.group(1) or fallback_match.group(3))
                        is_sequential = (last_main_chapter == 0) or (matched_num > last_main_chapter and (matched_num - last_main_chapter) <= 5)
                        if is_sequential and not (clean_line.endswith(".") or clean_line.endswith("?") or clean_line.endswith("!")) and len(clean_line) <= 50:
                            val_to_check = matched_num
                            is_new_chapter = True

                if is_new_chapter:
                    if val_to_check == current_active_chapter_num and lines_since_last_split < 20:
                        is_new_chapter = False
                    else:
                        current_active_chapter_num = val_to_check
                        last_main_chapter = val_to_check

                if is_new_chapter:
                    if current_chapter_lines:
                        chapters_data.append({"title": current_title, "lines": current_chapter_lines})
                    current_title = clean_line 
                    current_chapter_lines = [clean_line]
                    lines_since_last_split = 0
                else:
                    current_chapter_lines.append(clean_line)

            if current_chapter_lines:
                chapters_data.append({"title": current_title, "lines": current_chapter_lines})

            # Save the extracted data into session state
            st.session_state.chapters_data = chapters_data
            # Clear any previously built EPUB so the user has to rebuild with new edits
            st.session_state.epub_file = None 

# --- STEP 2: EDIT TOC & BUILD EPUB ---
if st.session_state.chapters_data:
    st.markdown("---")
    st.subheader("3. Edit Table of Contents")
    st.info("You can rename the chapters below. The changes will be reflected in both the Table of Contents and the Chapter Headings (<h1> tags) inside the book.")
    
    # Prepare data for the data editor
    toc_list = [{"Chapter": i, "Title": ch["title"]} for i, ch in enumerate(st.session_state.chapters_data)]
    
    # Display the interactive editor
    edited_toc = st.data_editor(
        toc_list,
        column_config={
            "Chapter": st.column_config.NumberColumn("Original Index", disabled=True),
            "Title": st.column_config.TextColumn("Chapter Title (Edit me!)")
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("4. Build EPUB with Edited TOC"):
        with st.spinner("Formatting HTML and packaging EPUB..."):
            
            book = epub.EpubBook()
            book.set_identifier("id123456")
            book.set_title(book_title)
            book.set_language(book_language)
            book.add_author(book_author)

            if cover_image:
                book.set_cover("cover.jpg", cover_image.getvalue())

            epub_chapters = []
            
            for i, row in enumerate(edited_toc):
                # Use the newly edited title
                final_title = row["Title"]
                original_lines = st.session_state.chapters_data[i]["lines"]
                
                file_name = f"chapter_{i}.xhtml"
                chapter = epub.EpubHtml(title=final_title, file_name=file_name, lang=book_language)
                
                html_content = ["<html><head></head><body>"]
                
                # Force the edited title as the <h1> tag
                html_content.append(f"<h1>{final_title.replace('<', '&lt;').replace('>', '&gt;')}</h1>")
                
                # Append the rest of the lines as <p> tags, skipping index 0 (the old title)
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
            
            # Save the binary EPUB data to session state
            st.session_state.epub_file = epub_io.getvalue()
            st.success("EPUB successfully built! Click below to download.")

# --- STEP 3: DOWNLOAD ---
if st.session_state.epub_file:
    st.download_button(
        label="⬇️ Download Edited EPUB",
        data=st.session_state.epub_file,
        file_name=f"{book_title}.epub",
        mime="application/epub+zip"
    )

# --- FOOTER ---
st.markdown("---")
st.markdown("""
### About the Developer
This was created to shit on Viery, as he dares to request 800 chapters, so i'm creating this to avoid doing his requests.
Any bug problems u can send a dm through @truongkoolvg4 (i'm not gonna reply to it mueheheheheh)
""")
