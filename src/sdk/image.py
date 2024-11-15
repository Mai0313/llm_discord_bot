import httpx

from src.types.config import Config


class ImageGenerator(Config):
    async def gen_image(self, prompt: str) -> bytes:
        async with httpx.AsyncClient(
            base_url="https://api-inference.huggingface.co/models"
        ) as client:
            response = await client.post(
                url="/strangerzonehf/Flux-Animex-v2-LoRA",
                headers={"Authorization": f"Bearer {self.huggingface_api_token}"},
                json={"inputs": prompt},
                timeout=60,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to generate image: {response.status_code} {response.text}"
                )
            return response.content
