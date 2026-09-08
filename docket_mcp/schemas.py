from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    """Output models are frozen and forbid unknown fields.

    These shapes are the tool contract: if the upstream mapping ever produces
    a field the schema does not declare, that is a bug worth failing on, not
    silently shipping to the model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class DocketSummary(_Model):
    id: str
    title: str | None
    docket_type: str | None
    agency_id: str | None
    last_modified: str | None
    match_context: str | None


class SearchDocketsResult(_Model):
    query: str
    total: int
    page: int
    page_size: int
    has_next_page: bool
    dockets: list[DocketSummary]


class DocketDetail(_Model):
    id: str
    title: str | None
    agency_id: str | None
    docket_type: str | None
    abstract: str | None
    keywords: list[str] | None
    rin: str | None
    last_modified: str | None


class DocumentSummary(_Model):
    id: str
    title: str | None
    document_type: str | None
    docket_id: str | None
    posted_date: str | None
    fr_doc_num: str | None
    open_for_comment: bool | None
    comment_end_date: str | None
    withdrawn: bool | None


class ListDocumentsResult(_Model):
    docket_id: str
    total: int
    page: int
    page_size: int
    has_next_page: bool
    documents: list[DocumentSummary]
