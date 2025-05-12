import os
import tempfile
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import soundfile as sf
import torch
import librosa
from transformers import (
    WhisperProcessor, WhisperForConditionalGeneration,
    SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
)
from datasets import load_dataset

app = FastAPI(title="Pronunciation Practice API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models and processors
print("Loading Whisper IPA model...")
whisper_processor = WhisperProcessor.from_pretrained("neurlang/ipa-whisper-base")
whisper_model = WhisperForConditionalGeneration.from_pretrained("neurlang/ipa-whisper-base")
whisper_model.config.forced_decoder_ids = None
whisper_model.config.suppress_tokens = []
whisper_model.generation_config.forced_decoder_ids = None
whisper_model.generation_config._from_model_config = True

print("Loading SpeechT5 model...")
speech_processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
speech_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
speech_vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

# Load speaker embeddings from dataset (only once)
print("Loading speaker embeddings...")
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)

# Define API models
class TextToSpeechRequest(BaseModel):
    text: str

class TextToSpeechResponse(BaseModel):
    audio_path: str

class TranscriptionResponse(BaseModel):
    ipa_transcription: str

@app.get("/")
async def root():
    return {"message": "Pronunciation Practice API is running"}

@app.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(text: str = Form(...)):
    """
    Convert text to speech using SpeechT5
    
    Returns the path to the generated audio file
    """
    try:
        # Process input text
        inputs = speech_processor(text=text, return_tensors="pt")
        
        # Generate speech
        speech = speech_model.generate_speech(
            inputs["input_ids"], 
            speaker_embeddings, 
            vocoder=speech_vocoder
        )
        
        # Save to temporary file
        audio_path = os.path.join(tempfile.gettempdir(), "speech_output.wav")
        sf.write(audio_path, speech.numpy(), samplerate=16000)
        
        return {"audio_path": audio_path}
    
    except Exception as e:
        return {"error": str(e)}

@app.post("/speech-to-ipa", response_model=TranscriptionResponse)
async def speech_to_ipa(audio_file: UploadFile = File(...)):
    """
    Convert speech to IPA transcription using Whisper IPA
    
    Returns the IPA transcription of the provided audio
    """
    try:
        # Save uploaded file
        temp_audio_path = os.path.join(tempfile.gettempdir(), "temp_audio.wav")
        with open(temp_audio_path, "wb") as f:
            f.write(await audio_file.read())
        
        # Load audio
        audio_array, sampling_rate = librosa.load(temp_audio_path, sr=16000)
        
        # Process audio
        input_features = whisper_processor(
            audio_array, 
            sampling_rate=sampling_rate, 
            return_tensors="pt"
        ).input_features
        
        # Generate token IDs
        predicted_ids = whisper_model.generate(input_features)
        
        # Decode token IDs to IPA
        transcription = whisper_processor.batch_decode(
            predicted_ids, 
            skip_special_tokens=True
        )[0]
        
        return {"ipa_transcription": transcription}
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 