from typing import Literal

import cv2
import numpy as np
from pydantic import Field, BaseModel


class ASCIIGenerator(BaseModel):
    input_path: str = Field(..., description="Path to input image")
    output_path: str = Field(..., description="Path to output text file")
    result_string: str = Field(default="", description="Result string")

    def gen_img2txt(
        self, mode: Literal["simple", "complex"] = "complex", num_cols: int = 150
    ) -> str:
        if mode == "simple":
            chars = "@%#*+=-:. "
        else:
            chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        num_chars = len(chars)
        num_cols = num_cols
        image = cv2.imread(self.input_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = image.shape
        cell_width = width / num_cols
        cell_height = 2 * cell_width
        num_rows = int(height / cell_height)
        if num_cols > width or num_rows > height:
            cell_width = 6
            cell_height = 12
            num_cols = int(width / cell_width)
            num_rows = int(height / cell_height)

        result = []  # Use a list to store the result
        for i in range(num_rows):
            row = ""
            for j in range(num_cols):
                row += chars[
                    min(
                        int(
                            np.mean(
                                image[
                                    int(i * cell_height) : min(int((i + 1) * cell_height), height),
                                    int(j * cell_width) : min(int((j + 1) * cell_width), width),
                                ]
                            )
                            * num_chars
                            / 255
                        ),
                        num_chars - 1,
                    )
                ]
            result.append(row)
        self.result_string = "\n".join(result)
        return self.result_string

    def export(self) -> None:
        with open(self.output_path, "w") as f:
            f.write(self.result_string)


if __name__ == "__main__":
    gen_ascii = ASCIIGenerator(
        input_path="./src/ascii/example_image.png", output_path="output.txt"
    )
    gen_ascii.gen_img2txt()
    gen_ascii.export()
