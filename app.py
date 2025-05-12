import os
import gradio as gr
import requests
import json
import tempfile
import time
from datetime import datetime
from utils import (
    generate_text_with_gemini, 
    evaluate_pronunciation, 
    get_sample_topics, 
    get_difficulty_levels
)

# API URL
API_URL = "http://127.0.0.1:8000"

def generate_sample_text(topic, difficulty):
    """Generate a sample text using Gemini API"""
    try:
        text, gen_time = generate_text_with_gemini(topic, difficulty)
        # Trả về text và tự động tạo audio và IPA cho câu vừa được tạo
        reference_audio, reference_ipa, ref_time = get_reference_audio_and_ipa(text)
        return text, reference_audio, reference_ipa, f"Text generation: {gen_time:.2f}s, Reference processing: {ref_time:.2f}s"
    except Exception as e:
        return f"Error generating text: {str(e)}", None, None, "Error"

def get_reference_audio_and_ipa(text):
    """Get reference audio and IPA for text"""
    start_time = time.time()
    
    if not text:
        return None, None, 0
        
    # Get reference audio
    reference_audio_path = text_to_speech(text)
    if not reference_audio_path or not os.path.exists(reference_audio_path):
        return None, None, 0
        
    # Get reference IPA
    reference_ipa = speech_to_ipa(reference_audio_path)
    if reference_ipa.startswith("Error"):
        return reference_audio_path, None, 0
    
    elapsed_time = time.time() - start_time
    return reference_audio_path, reference_ipa, elapsed_time

def text_to_speech(text):
    """Convert text to speech using the API"""
    try:
        response = requests.post(
            f"{API_URL}/text-to-speech",
            data={"text": text}
        )
        response.raise_for_status()
        result = response.json()
        
        if "audio_path" in result:
            return result["audio_path"]
        else:
            return None, f"Error: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def speech_to_ipa(audio_path):
    """Convert speech to IPA using the API"""
    try:
        if not audio_path:
            return "No audio file provided"
            
        with open(audio_path, "rb") as audio_file:
            files = {"audio_file": audio_file}
            response = requests.post(
                f"{API_URL}/speech-to-ipa",
                files=files
            )
        
        response.raise_for_status()
        result = response.json()
        
        if "ipa_transcription" in result:
            return result["ipa_transcription"]
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error: {str(e)}"

def format_evaluation_results(evaluation_text, eval_time):
    """Format evaluation results from plain text to display"""
    try:
        # Đơn giản hóa hàm này vì kết quả đã là văn bản thuần túy
        if evaluation_text:
            return f"{evaluation_text}\nEvaluation time: {eval_time:.2f}s"
        else:
            return "No evaluation results available"
    except Exception as e:
        # Nếu có lỗi, trả về thông báo lỗi
        return f"Error formatting results: {str(e)}"

def save_audio(audio_data):
    """Save recorded audio to a temporary file"""
    if audio_data is None:
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_path = os.path.join(tempfile.gettempdir(), f"user_recording_{timestamp}.wav")
    
    # Fix the error: check if audio_data is a string (filepath) or bytes
    if isinstance(audio_data, str):
        # If it's already a path, just return it
        return audio_data
    else:
        # Save the audio data to a file
        with open(audio_path, "wb") as f:
            f.write(audio_data)
            
    return audio_path

def process_user_audio(text, user_audio_path, reference_audio, reference_ipa):
    """Process user audio and compare with reference"""
    start_time = time.time()
    
    # Convert user audio to IPA
    if not user_audio_path or not os.path.exists(user_audio_path):
        return None, "No user audio provided", 0
    
    user_ipa = speech_to_ipa(user_audio_path)
    if user_ipa.startswith("Error"):
        return None, user_ipa, 0
    
    # Compare IPAs if we have both
    if reference_ipa and not reference_ipa.startswith("Error"):
        evaluation, eval_time = evaluate_pronunciation(reference_ipa, user_ipa)
        total_time = time.time() - start_time
        return user_ipa, evaluation, total_time
    else:
        return user_ipa, "Reference IPA not available for comparison", 0

def app_workflow(text, topic, difficulty, generate_new, audio_recording):
    """Main workflow for the app"""
    # Generate new text if requested
    if generate_new:
        text, reference_audio, reference_ipa, timing_info = generate_sample_text(topic, difficulty)
        return text, reference_audio, reference_ipa, None, "", timing_info
    
    # If no text is provided, return an error
    if not text:
        return text, None, None, None, "", "Please enter text or generate a sample"
    
    # Lấy reference audio và IPA nếu chưa có
    reference_audio = None
    reference_ipa = None
    timing_info = ""
    
    # Save recorded audio if provided
    user_audio_path = None
    user_ipa = None
    evaluation = None
    
    if audio_recording is not None:
        user_audio_path = save_audio(audio_recording)
        
        # Kiểm tra xem đã có reference audio và IPA chưa
        if not reference_audio or not reference_ipa:
            reference_audio, reference_ipa, ref_time = get_reference_audio_and_ipa(text)
            timing_info += f"Reference processing: {ref_time:.2f}s, "
        
        # Xử lý user audio
        if user_audio_path and os.path.exists(user_audio_path):
            user_ipa, evaluation, proc_time = process_user_audio(text, user_audio_path, reference_audio, reference_ipa)
            timing_info += f"User audio processing: {proc_time:.2f}s"
    else:
        # Nếu không có audio mới, chỉ lấy reference
        reference_audio, reference_ipa, ref_time = get_reference_audio_and_ipa(text)
        timing_info = f"Reference processing: {ref_time:.2f}s"
    
    # Format the evaluation results if they exist
    formatted_evaluation = ""
    if evaluation:
        formatted_evaluation = format_evaluation_results(evaluation, proc_time)
    elif user_ipa and user_ipa.startswith("Error"):
        formatted_evaluation = f"{user_ipa}"
    elif user_audio_path:
        formatted_evaluation = "Waiting for evaluation..."
    
    return text, reference_audio, reference_ipa, user_ipa, formatted_evaluation, timing_info

# Create Gradio interface
with gr.Blocks(title="Pronunciation Practice System") as demo:
    gr.Markdown("# 🎙️ Pronunciation Practice System")
    gr.Markdown("Improve your pronunciation with AI-powered feedback")
    
    # Text Generation Section
    with gr.Group():
        gr.Markdown("### 1. Text Generation")
        with gr.Row():
            topic_dropdown = gr.Dropdown(
                choices=get_sample_topics(),
                label="Topic",
                value="education"
            )
            difficulty_dropdown = gr.Dropdown(
                choices=get_difficulty_levels(),
                label="Difficulty",
                value="intermediate"
            )
        
        with gr.Row():
            text_input = gr.Textbox(
                label="Text to Pronounce",
                placeholder="Enter text here or generate a sample",
                lines=2
            )
            generate_btn = gr.Button("Generate Sample Text", variant="primary")
    
    # Reference Audio Section
    with gr.Group():
        gr.Markdown("### 2. Reference Audio")
        with gr.Row():
            reference_audio_output = gr.Audio(
                label="Reference Pronunciation",
                interactive=False
            )
            reference_ipa_output = gr.Textbox(
                label="Reference IPA",
                interactive=False
            )
    
    # Recording Section
    with gr.Group():
        gr.Markdown("### 3. Your Recording")
        with gr.Row():
            audio_input = gr.Audio(
                label="Record Your Pronunciation",
                sources=["microphone"],
                type="filepath"
            )
            user_ipa_output = gr.Textbox(
                label="Your IPA",
                interactive=False
            )
    
    # Evaluation Section
    with gr.Group():
        gr.Markdown("### 4. Evaluation")
        evaluation_output = gr.Textbox(label="Evaluation and Feedback", interactive=False)
    
    # Timing Information
    timing_info = gr.Textbox(label="Processing Time", interactive=False)
    
    # Event handlers
    generate_btn.click(
        fn=generate_sample_text,
        inputs=[topic_dropdown, difficulty_dropdown],
        outputs=[text_input, reference_audio_output, reference_ipa_output, timing_info]
    )
    
    # Process when new audio is recorded
    audio_input.change(
        fn=app_workflow,
        inputs=[
            text_input,
            topic_dropdown,
            difficulty_dropdown,
            gr.Checkbox(value=False, visible=False),  # Hidden generate_new checkbox
            audio_input
        ],
        outputs=[
            text_input,
            reference_audio_output,
            reference_ipa_output,
            user_ipa_output,
            evaluation_output,
            timing_info
        ]
    )

if __name__ == "__main__":
    # Launch the Gradio app
    demo.launch() 