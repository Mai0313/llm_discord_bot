import base64
from pathlib import Path
from mimetypes import guess_type

from pydantic import Field, BaseModel


class Attachment(BaseModel):
    file_path: str = Field(..., description="The path to the file to be converted to a data URL")

    def get_data_url(self) -> str:
        # Guess the MIME type of the image based on the file extension
        data_path = Path(self.file_path)
        mime_type, _ = guess_type(data_path)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default MIME type if none is found

        file_content = data_path.read_bytes()
        base64_encoded_data = base64.b64encode(file_content).decode("utf-8")

        # Construct the data URL
        return f"data:{mime_type};base64,{base64_encoded_data}"


if __name__ == "__main__":
    file_path = "<path_to_image>"
    attachment = Attachment(file_path=file_path)
    data_url = attachment.get_data_url()
