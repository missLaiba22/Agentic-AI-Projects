from typing import NotRequired, TypedDict
class DebateState(TypedDict):
    question: str
    research:str
    pro_arguments: str
    con_arguments: str
    verdict:str
    execution_id: NotRequired[str]  # Session tracking
    human_approved: NotRequired[bool]  # Human approval status
    human_edits: NotRequired[dict]  # Tracks original vs edited verdict
   
