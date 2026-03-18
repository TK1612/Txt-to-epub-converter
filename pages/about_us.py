import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="About Us", page_icon="ℹ️")

# --- FOREVER RUNNING GIF ---
st.image("https://media.giphy.com/media/1EgvBRIi806wnOQ4kG/giphy.gif")

# --- DIALOG POPUP ---
@st.dialog("About Us")
def show_about_us():
    st.write("This was created to shit on Viery, as he dares to request 800 chapters, so i'm creating this to avoid doing his requests.")
    st.write("Any bug problems u can send a dm though @thanhdeptrai101 (i'm not gonna reply to it mueheheheheh)")
    
    st.markdown("""
    **Thanks to our contributors:**
    * **Viery:** the sole reason i create this bullshit.
    * **Kuroh:** for being blac.
    * **Hb:** for being balls.
    * **Bobo:** for being dumb.
    * **Nekoldun:** for translating ts.
    * **Vlya:** for being emotional support.
    * **Tyuyu:** yuyuyuyuy.
    """)

# --- BUTTON TO TRIGGER DIALOG ---
if st.button("ℹ️ Click to read About Us"):
    show_about_us()
