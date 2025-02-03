import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF  # For PDF generation
import re

# Load API key from .env file
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def clean_text(text):
    """Removes markdown-style formatting like **bold** and emojis from the text."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Removes **bold** formatting
    text = re.sub(r"[^\x00-\x7F]+", "", text)  # Removes emojis & non-ASCII characters
    text = re.sub(r"\n{2,}", "\n", text)  # Removes extra newlines
    return text

def generate_notes(transcript_text, subject):
    """Generate structured study notes from the transcript."""
    
    prompt = f"""
        Title: Structured Study Notes on {subject}
        
        As an AI assistant, your task is to generate **structured and detailed notes** from the transcript of a YouTube video. 

        The notes should be **well-formatted** and include:
        - **Main topics & key concepts** (as section headings).
        - **Bullet points or numbered lists** for explanations.
        - **Examples, formulas, or real-world applications** (if mentioned in the video).
        - **Concise explanations** that improve readability.

        Here is the transcript of the video. Please extract and format the information into **structured and detailed notes**.
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt + transcript_text)
    return clean_text(response.text)  # Remove unwanted formatting

def generate_aptitude_questions(subject):
    """Generate possible placement aptitude questions related to the subject."""
    
    prompt = f"""
        Title: Placement Aptitude Questions for {subject}
        
        As an AI assistant, generate **5-7 placement-level aptitude questions** commonly asked in technical interviews related to {subject}. 
        Ensure the questions cover:
        - **Conceptual understanding**
        - **Problem-solving scenarios**
        - **Real-world applications**
        - **Multiple-choice or open-ended questions**

        Format the questions properly with numbering.
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return clean_text(response.text)  # Remove unwanted formatting

def extract_transcript(youtube_url):
    """Extracts transcript from a YouTube video."""
    try:
        video_id = youtube_url.split("v=")[-1]  # Extract video ID from URL
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript])
        return transcript_text
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

def save_as_pdf(notes, questions, subject):
    """Save structured notes and aptitude questions as a properly formatted PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title (Without Emojis)
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, f"Study Notes on {subject}", ln=True, align='C')
    pdf.ln(10)

    # Notes Section (Without Emojis)
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, "Detailed Notes", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", style="", size=12)
    
    # Split text into paragraphs
    for line in notes.split("\n"):
        if line.strip():
            if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                pdf.cell(10)  # Indent bullet points
            pdf.multi_cell(0, 7, line)
    
    pdf.ln(10)

    # Aptitude Questions Section (Without Emojis)
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, "Placement Aptitude Questions", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", style="", size=12)
    
    # Split questions into numbered format
    for line in questions.split("\n"):
        if line.strip():
            if re.match(r"^\d+\.", line):  # If the line starts with "1.", "2.", etc.
                pdf.ln(3)  # Add spacing between questions
            pdf.multi_cell(0, 7, line)

    # Save PDF
    pdf_filename = f"{subject}_study_notes.pdf"
    pdf.output(pdf_filename, "F")  # "F" ensures proper encoding
    return pdf_filename

def main():
    """Main function to run the Streamlit web app."""
    st.title("🎓 CS Mastery Hub – YouTube Video to Notes Converter")
    st.subheader("Extract key learnings from YouTube lectures on DBMS, OS, OOPS, and CN!")

    # Subject selection as a dropdown menu
    subject = st.selectbox("Select Core CS Subject:", 
                           ["Database Management Systems (DBMS)", 
                            "Operating Systems (OS)", 
                            "Object-Oriented Programming (OOPS)", 
                            "Computer Networks (CN)"])

    # YouTube link input
    youtube_link = st.text_input("Enter YouTube Video Link:")

    if youtube_link:
        video_id = youtube_link.split("v=")[-1]
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

    if st.button("📖 Generate Detailed Notes"):
        transcript_text = extract_transcript(youtube_link)
        
        if transcript_text and "Error" not in transcript_text:
            st.success("✅ Transcript extracted successfully!")

            # Generate study notes
            detailed_notes = generate_notes(transcript_text, subject)
            st.markdown("## 📚 Detailed Notes:")
            st.write(detailed_notes)

            # Generate placement aptitude questions
            aptitude_questions = generate_aptitude_questions(subject)
            st.markdown("## 🎯 Possible Placement Aptitude Questions:")
            st.write(aptitude_questions)

            # Allow user to download notes as PDF
            pdf_filename = save_as_pdf(detailed_notes, aptitude_questions, subject)
            with open(pdf_filename, "rb") as file:
                st.download_button(
                    label="📥 Download Notes as PDF",
                    data=file,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )

        else:
            st.error("⚠️ Failed to extract transcript. Please check the video link.")

if __name__ == "__main__":
    main()
