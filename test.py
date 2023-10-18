from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

async def get_claims(
    auth_header: str,
    credentials: CredentialProvider,
    channel_service_or_provider: Union[str, ChannelProvider],
    channel_id: str,
    service_url: str = None,
    auth_configuration: AuthenticationConfiguration = None,
) -> ClaimsIdentity:
    if SkillValidation.is_skill_token(auth_header):
        return await SkillValidation.authenticate_channel_token(
            auth_header,
            credentials,
            channel_service_or_provider,
            channel_id,
            auth_configuration,
        )

    if EmulatorValidation.is_token_from_emulator(auth_header):
        return await EmulatorValidation.authenticate_emulator_token(
            auth_header, credentials, channel_service_or_provider, channel_id
        )

    is_public = (
        not channel_service_or_provider
        or isinstance(channel_service_or_provider, ChannelProvider)
        and channel_service_or_provider.is_public_azure()
    )
    is_gov = (
        isinstance(channel_service_or_provider, ChannelProvider)
        and channel_service_or_provider.is_public_azure()
        or isinstance(channel_service_or_provider, str)
        and JwtTokenValidation.is_government(channel_service_or_provider)
    )

    # If the channel is Public Azure
    if is_public:
        if service_url:
            return await ChannelValidation.authenticate_channel_token_with_service_url(
                auth_header,
                credentials,
                service_url,
                channel_id,
                auth_configuration,
            )

        return await ChannelValidation.authenticate_channel_token(
            auth_header, credentials, channel_id, auth_configuration
        )

    if is_gov:
        if service_url:
            return await GovernmentChannelValidation.authenticate_channel_token_with_service_url(
                auth_header,
                credentials,
                service_url,
                channel_id,
                auth_configuration,
            )

        return await GovernmentChannelValidation.authenticate_channel_token(
            auth_header, credentials, channel_id, auth_configuration
        )

    # Otherwise use Enterprise Channel Validation
    if service_url:
        return await EnterpriseChannelValidation.authenticate_channel_token_with_service_url(
            auth_header,
            credentials,
            service_url,
            channel_id,
            channel_service_or_provider,
            auth_configuration,
        )

    return await EnterpriseChannelValidation.authenticate_channel_token(
        auth_header,
        credentials,
        channel_id,
        channel_service_or_provider,
        auth_configuration,
    )

async def decode_auth_header(adapter: BotFrameworkAdapter, activity, auth_header, app_id):
    credentials = adapter._credential_provider
    channel_provider = await adapter.settings.channel_provider.get_channel_service()
    auth_configuration = adapter.settings.auth_configuration
    claims_identity = await adapter._authenticate_request(activity, auth_header)
    return claims_identity.claims