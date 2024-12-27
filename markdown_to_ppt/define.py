from pydantic import BaseModel, Field

class TraceHeaders(BaseModel):
    b3_traceid: str = Field(default="", alias="x-b3-traceid")
    b3_spanid: str = Field(default="", alias="x-b3-spanid")
    b3_sampled: str = Field(default="", alias="x-b3-sampled")