from typing import List, TypedDict
class ResearchState(TypedDict):
    topic: str
    research_notes: str
    sources: List[str]
    summary: str