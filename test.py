from typing import Dict, List, Union
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes
from botframework.connector.auth import (
    ClaimsIdentity,
    CredentialProvider,
    ChannelProvider,
    AuthenticationConfiguration,
    JwtTokenValidation,
    ChannelValidation,
    EnterpriseChannelValidation,
    AuthenticationConstants,
    JwtTokenExtractor,
)

async def validate_identity(
        identity: ClaimsIdentity, credentials: CredentialProvider
):
    if not identity:
        # No valid identity. Not Authorized.
        raise PermissionError("Unauthorized. No valid identity.")

    if not identity.is_authenticated:
        # The token is in some way invalid. Not Authorized.
        raise PermissionError("Unauthorized. Is not authenticated")

    # Now check that the AppID in the claimset matches
    # what we're looking for. Note that in a multi-tenant bot, this value
    # comes from developer code that may be reaching out to a service, hence the
    # Async validation.

    # Look for the "aud" claim, but only if issued from the Bot Framework
    if (
        identity.get_claim_value(AuthenticationConstants.ISSUER_CLAIM)
        != AuthenticationConstants.TO_BOT_FROM_CHANNEL_TOKEN_ISSUER
    ):
        # The relevant Audience Claim MUST be present. Not Authorized.
        raise PermissionError("Unauthorized. Audience Claim MUST be present.")

    # The AppId from the claim in the token must match the AppId specified by the developer.
    # Note that the Bot Framework uses the Audience claim ("aud") to pass the AppID.
    aud_claim = identity.get_claim_value(AuthenticationConstants.AUDIENCE_CLAIM)
    return aud_claim

async def decode_auth_header(adapter: BotFrameworkAdapter, activity: Activity, auth_header, app_id):
    credentials = adapter._credential_provider
    channel_provider = await adapter.settings.channel_provider.get_channel_service()
    auth_configuration = adapter.settings.auth_configuration
    metadata_endpoint = (
        ChannelValidation.open_id_metadata_endpoint
        if ChannelValidation.open_id_metadata_endpoint
        else AuthenticationConstants.TO_BOT_FROM_CHANNEL_OPEN_ID_METADATA_URL
    )

    token_extractor = JwtTokenExtractor(
        ChannelValidation.TO_BOT_FROM_CHANNEL_TOKEN_VALIDATION_PARAMETERS,
        metadata_endpoint,
        AuthenticationConstants.ALLOWED_SIGNING_ALGORITHMS,
    )
    identity = await token_extractor.get_identity_from_auth_header(
        auth_header, activity.channel_id, auth_configuration.required_endorsements
    )
    # claims_identity = await get_claims(auth_header, credentials, channel_provider, activity.channel_id, activity.service_url, auth_configuration)
    return await validate_identity(identity, credentials)