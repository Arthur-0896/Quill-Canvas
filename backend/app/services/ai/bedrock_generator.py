import boto3
import json
import base64
import io
from typing import Optional
from PIL import Image


class AWSBedrockImageGenerator:
    """Generate images using AWS Bedrock Titan/Stable Diffusion"""
    
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name='us-east-1')
        # Using Titan Image Generator by default
        self.model_id = 'amazon.titan-image-generator-v1'
    
    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None) -> str:
        """
        Generate image using AWS Bedrock Titan
        Returns: base64 encoded image
        """
        try:
            request_body = {
                "inputText": prompt,
                "textNegative": negative_prompt or "blurry, low quality, distorted",
                "numberOfImages": 1,
                "quality": "standard",
                "cfgScale": 7.5,
                "height": 768,
                "width": 512,
                "seed": 0
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            image_base64 = response_body['images'][0]
            
            return image_base64
            
        except Exception as e:
            raise Exception(f"Bedrock image generation failed: {str(e)}")
    
    async def generate_and_save_to_s3(self, prompt: str, s3_key: str) -> str:
        """
        Generate image and save to S3
        Returns: S3 URL
        """
        import boto3
        
        try:
            image_base64 = await self.generate_image(prompt)
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)
            
            # Save to S3
            s3_client = boto3.client('s3')
            s3_client.put_object(
                Bucket='quill-canvas-images',  # Update with your bucket
                Key=s3_key,
                Body=image_bytes,
                ContentType='image/png'
            )
            
            s3_url = f"https://quill-canvas-images.s3.amazonaws.com/{s3_key}"
            return s3_url
            
        except Exception as e:
            raise Exception(f"Failed to generate and save image: {str(e)}")
