from openai import OpenAI
import base64
import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

client = OpenAI(
  api_key=os.getenv('API_KEY_01AI'),
  base_url=os.getenv('API_BASE_01AI')
)

# Use local images and encode them to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return "data:image/jpeg;base64," + base64.b64encode(image_file.read()).decode('utf-8')

# Local image paths
image = encode_image_to_base64("/Users/peizhengma/Downloads/测试图片/001.PNG")

completion = client.chat.completions.create(
  model="yi-vision",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "请详细描述一下这张图片。"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": image
          }
        }
      ]
    },
  ]
)
print(completion)
