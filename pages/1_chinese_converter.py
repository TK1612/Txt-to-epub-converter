import streamlit as st
import zipfile
import io
import time
from modules.chinese_splitter import extract_chinese_chapters
from modules.chinese_html_converter import generate_chinese_html_files
from modules.epub_builder import create_epub

# --- PAGE SETUP ---
st.set_page_config(page_title="Chinese to EPUB (WIP)", page_icon="🇨🇳", layout="centered")

st.title("🇨🇳 Chinese Novel to EPUB Converter")
st.warning("⚠️ Note: This page is currently In Development.")
st.write("Upload Chinese raw text. It automatically extracts Author/Synopsis, converts Volumes to `<h1>`, and Chapters to `<h2>`.")

# --- INITIALIZE SESSION STATE ---
if "cn_chapters_data" not in st.session_state:
    st.session_state.cn_chapters_data = []
if "cn_epub_file" not in st.session_state:
    st.session_state.cn_epub_file = None
if "cn_html_zip" not in st.session_state:
    st.session_state.cn_html_zip = None

# --- UI: FILE UPLOAD ---
uploaded_file = st.file_uploader("1. Upload raw Chinese .txt file", type=["txt"])

default_title = "Unknown Title"
default_author = "Unknown Author"

# --- STEP 1: EXTRACT CHAPTERS ---
if uploaded_file is not None:
    text = uploaded_file.getvalue().decode("utf-8")
    
    # We run extraction immediately to auto-fill the Metadata inputs
    title, author, chapters_data = extract_chinese_chapters(text)
    default_title = title if title != "Unknown Title" else uploaded_file.name.rsplit(".", 1)[0]
    default_author = author
    
    st.subheader("2. Book Metadata & Cover")
    col1, col2 = st.columns(2)
    with col1:
        book_title = st.text_input("Book Title", value=default_title)
        book_author = st.text_input("Author", value=default_author)
    with col2:
        book_language = st.text_input("Language Code", value="zh")
        cover_image = st.file_uploader("Upload Cover Image (Optional)", type=["jpg", "jpeg", "png"])

    if st.button("3. Extract Chapters"):
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Extracting metadata, volumes, and chapters..."):
            st.session_state.cn_chapters_data = chapters_data
            st.session_state.cn_epub_file = None 
            st.session_state.cn_html_zip = None
            
        gif_placeholder.empty() 
        st.success(f"Extracted Information block and {len(chapters_data)-1} chapters successfully!")

# --- STEP 2: EDIT TOC & BUILD FILES ---
if st.session_state.cn_chapters_data:
    st.markdown("---")
    st.subheader("3. Edit Table of Contents")
    
    toc_list = [{"Chapter": i, "Title": ch["title"], "Volume": ch["volume"]} for i, ch in enumerate(st.session_state.cn_chapters_data)]
    
    edited_toc = st.data_editor(
        toc_list,
        column_config={
            "Chapter": st.column_config.NumberColumn("Index", disabled=True),
            "Title": st.column_config.TextColumn("Chapter Title (Edit me!)"),
            "Volume": st.column_config.TextColumn("Volume Header", disabled=True)
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("4. Generate HTML & Build EPUB"):
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Formatting HTML and packaging files..."):
            
            html_dict = generate_chinese_html_files(edited_toc, st.session_state.cn_chapters_data)
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_name, html_content in html_dict.items():
                    zip_file.writestr(file_name, html_content.encode('utf-8'))
            st.session_state.cn_html_zip = zip_buffer.getvalue()

            cover_bytes = cover_image.getvalue() if cover_image else None
            
            # Uses your existing epub builder
            epub_data = create_epub(
                book_title, book_author, book_language, cover_bytes, 
                html_dict, edited_toc
            )
            st.session_state.cn_epub_file = epub_data
            
        gif_placeholder.empty()
        st.success("Files successfully built!")

# --- STEP 3: DOWNLOADS ---
if st.session_state.cn_html_zip or st.session_state.cn_epub_file:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.cn_html_zip:
            st.download_button(
                label="📁 Download HTML Files (ZIP)",
                data=st.session_state.cn_html_zip,
                file_name=f"{book_title}_HTMLs.zip",
                mime="application/zip"
            )
            
    with col2:
        if st.session_state.cn_epub_file:
            st.download_button(
                label="⬇️ Download Edited EPUB",
                data=st.session_state.cn_epub_file,
                file_name=f"{book_title}.epub",
                mime="application/epub+zip"
            )
