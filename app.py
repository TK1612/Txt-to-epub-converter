import streamlit as st
import zipfile
import io
import time
from modules.splitter import extract_chapters
from modules.scanner import check_missing_chapters
from modules.html_converter import generate_html_files
from modules.epub_builder import create_epub

# --- PAGE SETUP ---
st.set_page_config(page_title="Novel to EPUB Converter", page_icon="📚", layout="centered")

st.page_link("pages/1_chinese_converter.py", label="Chinese Converter (WIP)", icon="🇨🇳")
st.page_link("pages/2_about_us.py", label="About Us", icon="ℹ️")

st.title("📚 Novel to EPUB Converter")
st.write("Upload your raw text, extract chapters, edit the Table of Contents, and generate your files.")

# --- INITIALIZE SESSION STATE ---
if "chapters_data" not in st.session_state:
    st.session_state.chapters_data = []
if "epub_file" not in st.session_state:
    st.session_state.epub_file = None
if "html_zip" not in st.session_state:
    st.session_state.html_zip = None
if "found_numbers" not in st.session_state:
    st.session_state.found_numbers = set()
if "processed_file_id" not in st.session_state:
    st.session_state.processed_file_id = None
if "preview_mode" not in st.session_state:
    st.session_state.preview_mode = "original"

# --- UI: FILE UPLOAD & METADATA ---
uploaded_file = st.file_uploader("1. Upload raw .txt file", type=["txt"])

default_title = "Raw KR name"
if uploaded_file is not None:
    if st.session_state.processed_file_id != uploaded_file.file_id:
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        time.sleep(1.5) 
        gif_placeholder.empty()
        st.session_state.processed_file_id = uploaded_file.file_id

    default_title = uploaded_file.name.rsplit(".", 1)[0]

st.subheader("2. Book Metadata & Cover")
col1, col2 = st.columns(2)
with col1:
    book_title = st.text_input("Book Title", value=default_title)
    book_author = st.text_input("Author", value="Unknown Author")
with col2:
    book_language = st.text_input("Language Code", value="ko")
    cover_image = st.file_uploader("Upload Cover Image (Optional)", type=["jpg", "jpeg", "png"])

# --- STEP 1: EXTRACT CHAPTERS & SCAN ---
if uploaded_file is not None:
    if st.button("3. Extract Chapters"):
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Scanning document and identifying chapters..."):
            text = uploaded_file.getvalue().decode("utf-8")
            
            chapters_data, found_numbers = extract_chapters(text)
            st.session_state.chapters_data = chapters_data
            st.session_state.found_numbers = found_numbers
            st.session_state.epub_file = None 
            st.session_state.html_zip = None

            missing_chapters = check_missing_chapters(st.session_state.found_numbers)
            
        gif_placeholder.empty() 

        if missing_chapters:
            st.error("Oops, it seems the regex was not enough, please dm @thanhdeptrai101 to report to the saint about this problem")
            st.warning(f"Missing chapters detected: {', '.join(map(str, missing_chapters))}")
        else:
            st.success("Sequence is perfect! No missing chapters.")

# --- STEP 2: EDIT TOC & PREVIEW ---
if st.session_state.chapters_data:
    st.markdown("---")
    st.subheader("3. Edit Table of Contents")
    st.info("You can rename the chapters below. The changes will be reflected in the HTML files and the EPUB.")
    
    toc_list = [{"Chapter": i, "Title": ch["title"]} for i, ch in enumerate(st.session_state.chapters_data)]
    
    edited_toc = st.data_editor(
        toc_list,
        column_config={
            "Chapter": st.column_config.NumberColumn("Original Index", disabled=True),
            "Title": st.column_config.TextColumn("Chapter Title (Edit me!)")
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("4. Advanced Regex Formatting & Preview")
    
    col_fmt1, col_fmt2 = st.columns(2)
    with col_fmt1:
        handle_blank_space = st.checkbox("Handle empty `<p>` tags (blank space before title)", value=False)
    with col_fmt2:
        use_custom_regex = st.checkbox("Use custom Regex for Titles")

    if use_custom_regex:
        search_pattern = st.text_input("Search Regex:", value=r"<title>[^<]*</title>\s*</head>\s*<body>\s*<h1>[^<]*</h1>\s*<p>(?:&nbsp;|\s*)</p>\s*<p>([^<]+)</p>")
        replace_pattern = st.text_input("Replace Regex:", value=r"<title>\1</title>\n</head>\n<body>\n<h1>\1</h1>")
    else:
        if handle_blank_space:
            search_pattern = r"<title>[^<]*</title>\s*</head>\s*<body>\s*<h1>[^<]*</h1>\s*<p>(?:&nbsp;|\s*)</p>\s*<p>([^<]+)</p>"
        else:
            search_pattern = r"<title>[^<]*</title>\s*</head>\s*<body>\s*<h1>[^<]*</h1>\s*<p>([^<]+)</p>"
        replace_pattern = r"<title>\1</title>\n</head>\n<body>\n<h1>\1</h1>"

    # 1. ADDED CHECKBOX BACK FOR PREVIEW
    preview_file = st.checkbox("🔍 Show HTML Preview for a chapter")
    if preview_file:
        st.write("#### Chapter Preview Actions")
        preview_idx = st.selectbox(
            "Select chapter to preview:", 
            options=range(len(edited_toc)), 
            format_func=lambda x: f"Chapter {x}: {edited_toc[x]['Title']}"
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("👁️ Preview Original HTML", use_container_width=True):
                st.session_state.preview_mode = "original"
        with col_btn2:
            if st.button("✨ Apply Regex to Preview", type="primary", use_container_width=True):
                st.session_state.preview_mode = "regex"

        if st.session_state.preview_mode == "regex":
            preview_dict = generate_html_files(
                [edited_toc[preview_idx]], 
                [st.session_state.chapters_data[preview_idx]], 
                search_pattern, 
                replace_pattern
            )
            st.success("✨ Showing preview WITH Regex applied.")
        else:
            preview_dict = generate_html_files(
                [edited_toc[preview_idx]], 
                [st.session_state.chapters_data[preview_idx]]
            )
            st.info("👁️ Showing ORIGINAL HTML (No Regex applied).")
            
        preview_html = list(preview_dict.values())[0]
        
        tab1, tab2 = st.tabs(["Raw HTML Code", "Rendered Visual Preview"])
        with tab1:
            st.code(preview_html, language="html")
        with tab2:
            # 2. FIXED THE VISUAL PREVIEW MODE (Force white background, black text)
            styled_preview_html = preview_html.replace(
                "<head>", 
                "<head>\n<style>body { background-color: #ffffff; color: #000000; padding: 1.5rem; font-family: sans-serif; }</style>"
            )
            st.components.v1.html(styled_preview_html, height=400, scrolling=True)

    st.markdown("---")
    st.subheader("5. Build Final EPUB")
    
    apply_regex_final = st.checkbox("Apply the selected Regex formatting to all chapters during build?", value=False)

    if st.button("Generate HTML & Build EPUB"):
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Formatting HTML and packaging files..."):
            
            sp = search_pattern if apply_regex_final else None
            rp = replace_pattern if apply_regex_final else None
            
            html_dict = generate_html_files(
                edited_toc, 
                st.session_state.chapters_data, 
                sp, 
                rp
            )
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_name, html_content in html_dict.items():
                    zip_file.writestr(file_name, html_content.encode('utf-8'))
            st.session_state.html_zip = zip_buffer.getvalue()

            cover_bytes = cover_image.getvalue() if cover_image else None
            epub_data = create_epub(
                book_title, book_author, book_language, cover_bytes, 
                html_dict, edited_toc
            )
            st.session_state.epub_file = epub_data
            
        gif_placeholder.empty()
        st.success("Files successfully built! Please download them below.")

# --- STEP 3: DOWNLOADS ---
# 3. RESTORED EXACT DOWNLOAD CODE
if st.session_state.html_zip or st.session_state.epub_file:
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.html_zip:
            st.download_button(
                label="📁 Download HTML Files (ZIP)",
                data=st.session_state.html_zip,
                file_name=f"{book_title}_HTMLs.zip",
                mime="application/zip"
            )
            
    with col2:
        if st.session_state.epub_file:
            st.download_button(
                label="⬇️ Download Edited EPUB",
                data=st.session_state.epub_file,
                file_name=f"{book_title}.epub",
                mime="application/epub+zip"
            )
