# -*- coding: utf-8 -*-
"""
AudioScribe Web — استخراج النص من الصوت
نسخة Streamlit للرفع المجاني على Streamlit Community Cloud
"""

import streamlit as st
from faster_whisper import WhisperModel

st.set_page_config(page_title="استخراج النص من الصوت", page_icon="🎙️", layout="wide")

LANGS = {
    "كشف تلقائي": None,
    "العربية": "ar",
    "English": "en",
    "Français": "fr",
    "Español": "es",
    "Deutsch": "de",
    "Türkçe": "tr",
    "اردو / Urdu": "ur",
    "हिंदी / Hindi": "hi",
}


@st.cache_resource
def load_model(size):
    return WhisperModel(size, device="cpu", compute_type="int8")


st.title("🎙️ استخراج النص من الصوت")
st.caption("MP3 · WAV · M4A · AAC · OGG · FLAC · WEBM · MP4 — كل المعالجة تتم على الخادم")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("ارفع الملف الصوتي", type=["mp3", "wav", "m4a", "aac", "ogg", "flac", "webm", "mp4"])
with col2:
    lang_label = st.selectbox("لغة الصوت", list(LANGS.keys()), index=0)
    model_size = st.selectbox("دقة النموذج", ["tiny (أسرع)", "base (متوازن)"], index=1)

if st.button("▶ ابدأ التحويل", type="primary", disabled=not uploaded):
    size = "tiny" if "tiny" in model_size else "base"
    suffix = "." + uploaded.name.rsplit(".", 1)[-1].lower()
    tmp_path = "temp_audio" + suffix
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    with st.status("جاري المعالجة...", expanded=True):
        st.write(f"تحميل النموذج ({size})...")
        model = load_model(size)
        st.write("قراءة الصوت وتحويله إلى نص... قد يستغرق عدة دقائق")

        progress_bar = st.progress(0)
        segments, info = model.transcribe(
            tmp_path,
            language=LANGS[lang_label],
            task="transcribe",
            beam_size=1,
            vad_filter=True,
        )

        lines = []
        total = max(info.duration, 0.1)
        for s in segments:
            lines.append(s.text.strip())
            progress_bar.progress(min(int(s.end / total * 100), 99))

    detected = LANGS[lang_label] if LANGS[lang_label] else {v: k for k, v in LANGS.items()}.get(info.language, info.language)
    text = "\n".join(lines) if lines else "لم يتم التعرف على كلام في هذا الملف."

    st.success(f"تم! اللغة: {detected} | المدة: {info.duration / 60:.1f} دقيقة | الكلمات: {len(text.split())}")
    st.text_area("النص المستخرج — حدده وانسخه", value=text, height=300)
    st.download_button("⬇ حفظ النص TXT", text, file_name="transcript.txt")

    import os
    os.remove(tmp_path)
