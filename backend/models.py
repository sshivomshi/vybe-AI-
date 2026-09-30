from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime

class MemoryInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=12000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    memory_type: Literal['QUICK','STANDARD','DETAILED','ARCHIVE_ONLY'] = 'STANDARD'
    importance: float = Field(default=0.5, ge=0, le=1)
    local_only: bool = False
    archived: bool = False
    source_chat_id: str | None = None
    source_message_ids: list[str] = Field(default_factory=list)
    @field_validator('title','summary')
    @classmethod
    def nonblank(cls, value):
        if not value.strip(): raise ValueError('Cannot be blank')
        return value.strip()
    @field_validator('tags')
    @classmethod
    def valid_tags(cls,value):
        if any(not tag.strip() or len(tag)>64 for tag in value):raise ValueError('Tags must be 1–64 characters')
        return list(dict.fromkeys(tag.strip() for tag in value))

class EditMemory(MemoryInput):
    expected_version: int = Field(ge=1)

class StoredMemory(MemoryInput):
    memory_id: str
    user_id: Literal['owner']
    created_at: str
    updated_at: str
    embedding_model: str | None
    version: int = Field(ge=1)
    device_id: str
    sync_status: Literal['LOCAL_ONLY','PENDING','SYNCING','SYNCED','FAILED','CONFLICT']
    deleted_at: str | None
    @field_validator('memory_id','device_id')
    @classmethod
    def identifier(cls,value):
        UUID(value)
        return value
    @field_validator('created_at','updated_at','deleted_at')
    @classmethod
    def timestamp(cls,value):
        if value is not None:
            parsed=datetime.fromisoformat(value)
            if parsed.tzinfo is None:raise ValueError('Timestamp must include timezone')
        return value

class ChatInput(BaseModel):
    request_id: UUID | None = None
    content: str = Field(min_length=1, max_length=16000)
    chat_id: str | None = None
    capture: bool = False
    inference: Literal['configured','local'] = 'configured'

class CaptureInput(BaseModel):
    enabled: bool

class Resolution(BaseModel):
    method: Literal['LOCAL','REMOTE','MERGE']
    merged: MemoryInput | None = None

class Operation(BaseModel):
    operation_id: str
    entity_id: str
    device_id: str
    base_version: int = Field(ge=0)
    new_version: int = Field(ge=1)
    operation_type: Literal['CREATE','UPDATE','DELETE','ARCHIVE','RESTORE','MERGE']
    timestamp: str
    payload: dict
    @field_validator('operation_id','entity_id','device_id')
    @classmethod
    def valid_id(cls,value):
        UUID(value)
        return value
