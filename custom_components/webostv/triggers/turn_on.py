"""LG webOS TV device turn on trigger."""

from functools import partial
from typing import TYPE_CHECKING, Any, cast, override

import voluptuous as vol

from homeassistant.const import (
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_TARGET,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.automation import move_top_level_schema_fields_to_options
from homeassistant.helpers.target import TargetEntityChangeTracker, TargetSelection
from homeassistant.helpers.trigger import (
    PluggableAction,
    Trigger,
    TriggerActionRunner,
    TriggerConfig,
    TriggerNotTriggeredReporter,
)
from homeassistant.helpers.typing import ConfigType

from ..const import DOMAIN
from ..helpers import async_get_device_entry_by_device_id

# Platform type should be <DOMAIN>.<SUBMODULE_NAME>
PLATFORM_TYPE = f"{DOMAIN}.{__name__.rsplit('.', maxsplit=1)[-1]}"

DEPRECATED_TRIGGER_ISSUE_ID = "deprecated_turn_on_trigger"

_TRIGGER_SCHEMA = vol.Schema({vol.Required(CONF_TARGET): cv.TARGET_FIELDS})

# The legacy trigger selected devices with top-level entity_id and device_id options,
# which happen to be target fields, so they are reused as the target as-is.
_LEGACY_OPTIONS_SCHEMA_DICT: dict[vol.Marker, Any] = {
    vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
}

_LEGACY_TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPTIONS): vol.All(
            _LEGACY_OPTIONS_SCHEMA_DICT,
            cv.has_at_least_one_key(ATTR_ENTITY_ID, ATTR_DEVICE_ID),
        )
    }
)


def async_get_turn_on_trigger(device_id: str) -> dict[str, str]:
    """Return data for a turn on trigger."""

    return {
        CONF_PLATFORM: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
        CONF_TYPE: PLATFORM_TYPE,
    }


@callback
def async_get_turn_on_description(hass: HomeAssistant, device_id: str) -> str:
    """Return the trigger description for a device."""
    device = async_get_device_entry_by_device_id(hass, device_id)
    return f"webostv turn on trigger for {device.name_by_user or device.name}"


class _TurnOnTargetTracker(TargetEntityChangeTracker):
    """Attach turn on actions to the webOS TV devices selected by a target."""

    def __init__(
        self,
        hass: HomeAssistant,
        target_selection: TargetSelection,
        run_action: TriggerActionRunner,
    ) -> None:
        """Initialize the tracker."""

        def entity_filter(entities: set[str]) -> set[str]:
            ent_reg = er.async_get(hass)
            return {
                entity_id
                for entity_id in entities
                if (entry := ent_reg.async_get(entity_id)) is not None
                and entry.platform == DOMAIN
                and entry.device_id is not None
            }

        super().__init__(hass, target_selection, entity_filter)
        self._run_action = run_action
        self._device_ids: set[str] = set()
        self._unsubs: list[CALLBACK_TYPE] = []

    @callback
    @override
    def _handle_entities_update(self, tracked_entities: set[str]) -> None:
        """Re-attach the turn on actions when the tracked devices change."""
        ent_reg = er.async_get(self._hass)
        device_ids = {
            device_id
            for entity_id in tracked_entities
            if (entry := ent_reg.async_get(entity_id))
            and (device_id := entry.device_id)
        }
        if device_ids == self._device_ids:
            return

        self._detach_actions()
        self._device_ids = device_ids

        for device_id in device_ids:
            self._unsubs.append(
                PluggableAction.async_attach_trigger(
                    self._hass,
                    async_get_turn_on_trigger(device_id),
                    partial(
                        self._run_turn_on_action,
                        async_get_turn_on_description(self._hass, device_id),
                    ),
                    {ATTR_DEVICE_ID: device_id},
                )
            )

    @callback
    def _run_turn_on_action(
        self,
        description: str,
        variables: dict[str, Any],
        context: Context | None = None,
    ) -> None:
        """Run the trigger action."""
        self._run_action(variables, description, context)

    @callback
    def _detach_actions(self) -> None:
        """Detach the currently attached turn on actions."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @override
    def _unsubscribe(self) -> None:
        """Unsubscribe from all events."""
        super()._unsubscribe()
        self._detach_actions()
        self._device_ids = set()


class _TurnOnTriggerBase(Trigger):
    """Shared behavior of the LG webOS TV turn on triggers."""

    _target: dict[str, Any]

    @override
    async def async_attach_runner(
        self,
        run_action: TriggerActionRunner,
        did_not_trigger: TriggerNotTriggeredReporter | None = None,
    ) -> CALLBACK_TYPE:
        """Attach a trigger."""
        target_selection = TargetSelection(self._target)
        if not target_selection.has_any_target:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="trigger_without_target"
            )

        tracker = _TurnOnTargetTracker(self._hass, target_selection, run_action)
        return await tracker.async_setup()


class TurnOnTrigger(_TurnOnTriggerBase):
    """LG webOS TV turn on trigger."""

    @classmethod
    @override
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate config."""
        return cast(ConfigType, _TRIGGER_SCHEMA(config))

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        """Initialize trigger."""
        super().__init__(hass, config)

        if TYPE_CHECKING:
            assert config.target is not None
        self._target = config.target


class LegacyTurnOnTrigger(_TurnOnTriggerBase):
    """Backwards compatible trigger for the legacy `webostv.turn_on` config.

    This trigger is deliberately absent from `triggers.yaml`, so the automation editor
    keeps treating it as unsupported rather than rendering a stored config that uses the
    legacy options against a target selector.
    """

    @classmethod
    @override
    async def async_validate_complete_config(
        cls, hass: HomeAssistant, complete_config: ConfigType
    ) -> ConfigType:
        """Validate complete config, moving the legacy top-level fields to options."""
        ir.async_create_issue(
            hass,
            DOMAIN,
            DEPRECATED_TRIGGER_ISSUE_ID,
            breaks_in_ha_version="2027.3",
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=DEPRECATED_TRIGGER_ISSUE_ID,
        )
        complete_config = move_top_level_schema_fields_to_options(
            complete_config, _LEGACY_OPTIONS_SCHEMA_DICT
        )
        return await super().async_validate_complete_config(hass, complete_config)

    @classmethod
    @override
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate config."""
        return cast(ConfigType, _LEGACY_TRIGGER_SCHEMA(config))

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        """Initialize trigger."""
        super().__init__(hass, config)

        if TYPE_CHECKING:
            assert config.options is not None
        self._target = config.options
