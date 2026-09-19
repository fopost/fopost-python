"""fopost — official Python SDK for the FoPost API.

Quick start::

    from fopost import Fopost

    client = Fopost(api_key="fp_...")

    accounts = client.accounts.list(workspace_id="9b2f6c1e-...")
    post = client.posts.create(
        workspace_id="9b2f6c1e-...",
        content="Hello from Python",
        accounts=[a.id for a in accounts],
    )
    client.posts.publish(post.id)
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from ._http import DEFAULT_BASE_URL
from .client import Fopost
from .errors import (
    AuthenticationError,
    FopostError,
    NotFoundError,
    PaymentRequiredError,
    PermissionDeniedError,
    RateLimitError,
)
from .models import (
    PLATFORMS,
    POST_STATUSES,
    Ad,
    AdConnection,
    AdInsights,
    AdSource,
    AiCreditBalance,
    AiCredits,
    Audience,
    AudiencesResult,
    BoostablePost,
    CaptionResult,
    ContentBlock,
    ContentSignal,
    Delivery,
    ExternalAd,
    InboxAccount,
    InboxAccountRef,
    InboxApproval,
    InboxAttachment,
    InboxConversation,
    InboxItem,
    InboxPlatform,
    InboxPostContext,
    InboxRefreshResult,
    InboxReplyResult,
    InboxThread,
    Label,
    Lead,
    LeadForm,
    LeadFormSource,
    LeadsPage,
    MediaItem,
    Page,
    PageMeta,
    Platform,
    Post,
    PostAccount,
    PostStatus,
    RepurposeResult,
    RewriteResult,
    RewriteVariant,
    SocialAccount,
    TargetingOption,
    ValidateLengthCheck,
    ValidateLengthResult,
    ValidateMediaResult,
    ValidatePlatformCheck,
    ValidatePostResult,
    Workspace,
)

try:
    __version__ = _pkg_version("fopost")
except PackageNotFoundError:  # running from a source tree
    __version__ = "0.0.0"

#: Alias for people arriving from the TypeScript SDK, where the class is `FoPost`.
FoPost = Fopost

__all__ = [
    "DEFAULT_BASE_URL",
    "PLATFORMS",
    "POST_STATUSES",
    "Ad",
    "AdConnection",
    "AdInsights",
    "AdSource",
    "AiCreditBalance",
    "AiCredits",
    "Audience",
    "AudiencesResult",
    "AuthenticationError",
    "BoostablePost",
    "CaptionResult",
    "ContentBlock",
    "Delivery",
    "ExternalAd",
    "FoPost",
    "Fopost",
    "FopostError",
    "InboxAccount",
    "InboxAccountRef",
    "InboxApproval",
    "InboxAttachment",
    "InboxConversation",
    "InboxItem",
    "InboxPlatform",
    "InboxPostContext",
    "InboxRefreshResult",
    "InboxReplyResult",
    "InboxThread",
    "Label",
    "Lead",
    "LeadForm",
    "LeadFormSource",
    "LeadsPage",
    "MediaItem",
    "NotFoundError",
    "Page",
    "PageMeta",
    "PaymentRequiredError",
    "PermissionDeniedError",
    "Platform",
    "Post",
    "PostAccount",
    "PostStatus",
    "RateLimitError",
    "RepurposeResult",
    "RewriteResult",
    "RewriteVariant",
    "SocialAccount",
    "TargetingOption",
    "ValidateLengthCheck",
    "ValidateLengthResult",
    "ValidateMediaResult",
    "ValidatePlatformCheck",
    "ValidatePostResult",
    "ContentSignal",
    "Workspace",
    "__version__",
]
