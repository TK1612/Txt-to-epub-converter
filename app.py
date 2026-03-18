import streamlit as st
import zipfile
import io
import time
import base64
import os
from modules.splitter import extract_chapters
from modules.scanner import check_missing_chapters
from modules.html_converter import generate_html_files
from modules.epub_builder import create_epub

# --- PAGE SETUP ---
st.set_page_config(page_title="Novel to EPUB Converter", page_icon="📚", layout="centered")

# --- ADD CHARACTER TO CORNER ---
def add_character_to_corner(image_path):
    # Check if the file actually exists before trying to open it
    if os.path.exists(image_path):
        # Read and encode the image to base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        # Inject custom CSS and the image HTML
        st.markdown(
            f"""
            <style>
                .bottom-left-character {{
                    position: fixed;
                    bottom: 0px;  /* Flushes image to the bottom */
                    left: 0px;    /* Flushes image to the left */
                    width: 250px; /* Adjust the size of the character here */
                    z-index: 9999; /* Keeps it on top of the UI */
                    pointer-events: none; /* Prevents the image from blocking clicks */
                }}
            </style>
            <img src="data:image/png;base64,{encoded_string}" class="bottom-left-character">
            """,
            unsafe_allow_html=True
        )

# Call the function (make sure character.png is in the same folder as this script)
add_character_to_corner("character.png")

# --- ABOUT US LINK ---
st.page_link("pages/about_us.py", label="About Us", icon="ℹ️")

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

# --- UI: FILE UPLOAD & METADATA ---
uploaded_file = st.file_uploader("1. Upload raw .txt file", type=["txt"])

default_title = "Raw KR name"
if uploaded_file is not None:
    
    # Check if this is a brand new file being dropped in
    if st.session_state.processed_file_id != uploaded_file.file_id:
        
        # Show the GIF
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        # Pause for 1.5 seconds so the user actually sees the GIF
        time.sleep(1.5) 
        
        # Clear it out and remember that we processed this file
        gif_placeholder.empty()
        st.session_state.processed_file_id = uploaded_file.file_id

    # Automatically get the filename without the ".txt"
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
        
        # 1. Initialize the GIF placeholder
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Scanning document and identifying chapters..."):
            text = uploaded_file.getvalue().decode("utf-8")
            
            # Splitting Branch
            chapters_data, found_numbers = extract_chapters(text)
            
            st.session_state.chapters_data = chapters_data
            st.session_state.found_numbers = found_numbers
            st.session_state.epub_file = None 
            st.session_state.html_zip = None

            # Scanning Branch
            missing_chapters = check_missing_chapters(st.session_state.found_numbers)
            
        # 2. Clear the GIF only AFTER everything above is done processing
        gif_placeholder.empty() 

        # Display results of the scan
        if missing_chapters:
            st.error("Oops, it seems the regex was not enough, please dm @thanhdeptrai101 to report to the saint about this problem")
            st.warning(f"Missing chapters detected: {', '.join(map(str, missing_chapters))}")
        else:
            st.success("Sequence is perfect! No missing chapters.")

# --- STEP 2: EDIT TOC & BUILD FILES ---
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

    if st.button("4. Generate HTML & Build EPUB"):
        
        # 1. Initialize the GIF placeholder
        gif_placeholder = st.empty()
        gif_placeholder.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")
        
        with st.spinner("Formatting HTML and packaging files..."):
            
            # HTML Converter Branch
            html_dict = generate_html_files(edited_toc, st.session_state.chapters_data)
            
            # Create a ZIP of the HTML files for Sigil
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_name, html_content in html_dict.items():
                    zip_file.writestr(file_name, html_content.encode('utf-8'))
            st.session_state.html_zip = zip_buffer.getvalue()

            # EPUB Builder Branch
            cover_bytes = cover_image.getvalue() if cover_image else None
            epub_data = create_epub(
                book_title, book_author, book_language, cover_bytes, 
                html_dict, edited_toc
            )
            st.session_state.epub_file = epub_data
            
        # 2. Clear the GIF when the files are built
        gif_placeholder.empty()
        
        st.success("Files successfully built! You can download the raw HTMLs for Sigil, or the complete EPUB.")

# --- STEP 3: DOWNLOADS ---
if st.session_state.html_zip or st.session_state.epub_file:
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
