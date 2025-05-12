# Pronunciation Practice System

Hệ thống luyện tập phát âm sử dụng Whisper IPA, SpeechT5 và Gemini API.

## Tính năng

- Tạo câu mẫu (có thể tự động gen bằng Gemini)
- Chuyển đổi văn bản thành giọng nói mẫu (text-to-speech)
- Chuyển đổi âm thanh thành biểu diễn IPA (International Phonetic Alphabet)
- Ghi âm giọng nói người dùng
- So sánh phát âm người dùng với mẫu
- Đưa ra gợi ý cải thiện phát âm

## Cài đặt

1. Cài đặt các thư viện cần thiết:
   ```
   pip install -r requirements.txt
   ```

2. Tạo file `.env` với API key của Gemini:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. Khởi động API:
   ```
   uvicorn api:app --reload
   ```

4. Khởi động giao diện Gradio:
   ```
   python app.py
   ```

## Cấu trúc dự án

- `api.py`: FastAPI server cung cấp API cho Whisper IPA và SpeechT5
- `app.py`: Giao diện Gradio
- `utils.py`: Các hàm tiện ích
- `requirements.txt`: Danh sách các thư viện cần thiết
- `.env`: Chứa API key 