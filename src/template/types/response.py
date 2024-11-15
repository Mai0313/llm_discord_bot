from pydantic import Field, BaseModel, ConfigDict, AliasChoices


class Response(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)
    name: str = Field(
        ...,
        title="Name",
        description="The name of the response.",
        validation_alias=AliasChoices("name", "Name"),
        frozen=False,
        deprecated=False,
    )
    content: str = Field(
        ...,
        title="Content",
        description="The content of the response.",
        validation_alias=AliasChoices("content", "Content"),
        frozen=False,
        deprecated=False,
    )
