import ast
import shutil
from typing import Literal
from pathlib import Path
import itertools

import anyio
import nbformat
from pydantic import Field, BaseModel, ConfigDict, computed_field
from nbconvert import MarkdownExporter
from rich.console import Console
from rich.progress import Progress

console = Console()


class DocsGenerator(BaseModel):
    """DocsGenerator is a class that generates documentation for Python files or classes within a specified source directory.

    Attributes:
        source (str): The source directory or file path.
        output (str): The output directory path.
        exclude (str): Comma-separated list of folders or files to exclude.
        mode (Literal["file", "class"]): Mode of documentation generation, either by file or class.

    Methods:
        gen_docs() -> None:
            Generates documentation by file or class.

        __call__() -> None:
            Asynchronously calls the gen_docs method.

    Using CLI:
        ```bash
        python ./scripts/gen_docs.py --source ./src --output ./docs/Reference --exclude .venv gen_docs
        ```

    Using Rye:
        ```bash
        uv run python ./scripts/gen_docs.py
        ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    source: str = Field(..., frozen=True)
    output: str = Field(..., frozen=True)
    exclude: str = Field(
        default=".venv",
        description="Exclude the folder or file, it should be separated by comma.",
        examples=[".venv,.git,.idea"],
    )
    mode: Literal["file", "class"] = Field(
        default="class", description="Generate docs by file or class."
    )

    @computed_field
    @property
    def _source_path(self) -> Path:
        """Computed property that returns the source path as a Path object.

        Returns:
            Path: The source path.
        """
        return Path(self.source)

    @computed_field
    @property
    def _output_path(self) -> Path:
        """Computed property that returns the output path as a Path object.

        Returns:
            Path: The output path.
        """
        return Path(self.output)

    async def __remove_existing_folder(self) -> None:
        """Asynchronously removes the existing folder at the output path if it exists, and then recreates the folder.

        This method checks if the output path exists. If it does, the folder and its contents are removed. After removal, a new folder is created at the same path.
        """
        if self._output_path.exists():
            shutil.rmtree(self._output_path.absolute())
            self._output_path.mkdir(parents=True, exist_ok=True)

    async def __gen_content(self, file: Path) -> str:
        """Generates documentation content based on the specified mode.

        Args:
            file (Path): The file path for which the documentation content is to be generated.

        Returns:
            str: The generated documentation content as a string.

        Raises:
            ValueError: If the mode is not "file" or "class".

        Notes:
            - If the mode is "file", the function generates a string with the file path formatted for documentation.
            - If the mode is "class", the function reads the file, parses its AST, and generates a string with class names formatted for documentation, excluding classes with names starting with an underscore.
            - If no content is generated, a default string with the file path formatted for documentation is returned.
        """
        if self.mode == "file":
            note_content = f"::: {file.as_posix().removesuffix('.py').replace('/', '.')}\n"
        elif self.mode == "class":
            async with await anyio.open_file(file, encoding="utf-8") as f:
                contents = await f.read()
                tree = ast.parse(source=contents, filename=file)

            note_content = ""
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.startswith("_"):
                        continue
                    note_content += f"::: {file.as_posix().removesuffix('.py').replace('/', '.')}.{node.name}\n"
        else:
            raise ValueError("Invalid mode")
        if not note_content:
            note_content = f"::: {file.as_posix().removesuffix('.py').replace('/', '.')}\n"
        return note_content

    async def __gen_single_docs(self, docs_path: Path, file: Path) -> str:
        """Generates documentation for a single file.

        This asynchronous method generates documentation for a given file and saves it as a markdown file in the specified documentation path.
        It ensures that the output directory exists and removes any existing file with the same name before writing the new content.

        Args:
            docs_path (Path): The path where the documentation should be saved.
            file (Path): The file for which the documentation is to be generated.

        Returns:
            str: The path to the generated documentation file as a string.
        """
        _output_docs_path = Path(docs_path / file.with_suffix(".md").name)
        _output_docs_path.parent.mkdir(parents=True, exist_ok=True)
        _output_docs_path.unlink(missing_ok=True)
        _note_content = await self.__gen_content(file=file)
        _output_docs_path.write_text(data=_note_content, encoding="utf-8")
        return _output_docs_path.as_posix()

    async def __gen_notebook_docs(self, docs_path: Path, file: Path) -> str:
        _output_docs_path = Path(docs_path / file.with_suffix(".md").name)
        _output_docs_path.parent.mkdir(parents=True, exist_ok=True)
        _output_docs_path.unlink(missing_ok=True)
        async with await anyio.open_file(file, encoding="utf-8") as f:
            nb = nbformat.reads(await f.read(), as_version=4)

        markdown_exporter = MarkdownExporter(template_name="markdown")
        markdown_output, _ = markdown_exporter.from_notebook_node(nb)

        async with await anyio.open_file(_output_docs_path, "w", encoding="utf-8") as f:
            await f.write(markdown_output)
        return _output_docs_path.as_posix()

    async def process_file(self, docs_path: Path, file: Path) -> str:
        if file.suffix == ".ipynb":
            processed_file = await self.__gen_notebook_docs(docs_path=docs_path, file=file)
        elif file.suffix == ".py":
            processed_file = await self.__gen_single_docs(docs_path=docs_path, file=file)
        else:
            processed_file = f"Unsupported file type: {file.suffix}"
            console.log(processed_file)
        return processed_file

    async def gen_docs(self) -> None:
        """This function can generate docs by file or class.

        Raises:
            ValueError: If the source path is invalid.

        Examples:
            >>> import asyncio
            >>> pair_list = {"./src": "./docs/Reference"}
            >>> for key, value in pair_list.items():
            ...     docs_generator = DocsGenerator(source=key, output=value, exclude=".venv", mode="class")
            ...     asyncio.run(docs_generator.gen_docs())
        """
        with Progress() as progress:
            task = progress.add_task("[green]Generating docs...")
            if self._source_path.is_dir():
                await self.__remove_existing_folder()

                need_to_exclude = [*self.exclude.split(","), "__init__.py"]
                python_files = self._source_path.glob("**/*.py")
                ipynb_files = self._source_path.glob("**/*.ipynb")
                files = itertools.chain(python_files, ipynb_files)
                all_files = [
                    file for file in files if not any(f in file.parts for f in need_to_exclude)
                ]

                progress.update(
                    task_id=task, description="[cyan]Files Found...", total=len(all_files)
                )

                for file in all_files:
                    docs_path = Path(
                        f"{self._output_path}/{file.parent.relative_to(self._source_path)}"
                    )
                    processed_file = await self.process_file(docs_path=docs_path, file=file)
                    progress.update(
                        task_id=task,
                        advance=1,
                        description=f"[cyan]Processing {processed_file}...",
                        refresh=True,
                    )

            elif self._source_path.is_file():
                progress.update(task_id=task, description="[cyan]Files Found...", total=1)
                processed_file = await self.process_file(
                    docs_path=self._output_path, file=self._source_path
                )
                progress.update(
                    task_id=task,
                    advance=1,
                    description=f"[cyan]Processing {processed_file}...",
                    refresh=True,
                )
            else:
                raise ValueError("Invalid source path")

    async def __call__(self) -> None:
        """Asynchronously calls the gen_docs method.

        This method is intended to be used as a callable object, which when called, will execute the gen_docs method asynchronously.

        Examples:
            >>> import asyncio
            >>> pair_list = {"./src": "./docs/Reference"}
            >>> for key, value in pair_list.items():
            ...     docs_generator = DocsGenerator(source=key, output=value, exclude=".venv", mode="class")
            ...     asyncio.run(docs_generator())
        """
        await self.gen_docs()


if __name__ == "__main__":
    import fire

    fire.Fire(DocsGenerator)
