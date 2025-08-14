import openai
import sys
import os
from core.config import openai_client
# Đặt API key từ biến môi trường
# openai.api_key = os.getenv("OPENAI_API_KEY")
def chat_with_gpt(prompt):
    try:
        # Gửi yêu cầu với stream=True
        response = openai_client.responses.create(
            model="gpt-4o-mini",  # Hoặc "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý thông minh."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=150,
            stream=True  # Bật streaming
        )

        # Xử lý từng chunk dữ liệu nhận được
        for chunk in response:
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content:
                sys.stdout.write(content)
                sys.stdout.flush()

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

# Ví dụ sử dụng
prompt = "Giới thiệu về GPT-4."
chat_with_gpt(prompt)
