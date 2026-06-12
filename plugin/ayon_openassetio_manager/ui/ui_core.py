"""Implementation of the AYON OpenAssetIO UI delegate."""
from __future__ import annotations

import os
import pathlib
from typing import Any, Callable, Optional

import ayon_api
from ayon_core.tools.context_dialog.window import (
    ContextDialog,
    ContextDialogController,
)
from ayon_core.tools.loader import LoaderController
from ayon_core.tools.loader.ui import LoaderWindow
from ayon_core.tools.push_to_project import PushToContextController
from ayon_core.tools.push_to_project.ui import PushToContextSelectWindow
from ayon_core.tools.workfiles.control import BaseWorkfileController
from ayon_core.tools.workfiles.widgets import WorkfilesToolWindow
from openassetio import Context, EntityReference
from openassetio.managerApi import HostSession
from openassetio.trait import TraitsData
from openassetio.ui import access
from openassetio.ui.managerApi import (
    UIDelegateRequest,
    UIDelegateStateInterface,
)
from openassetio_mediacreation.traits.application import (
    ConfigTrait,
    ManifestTrait,
    WorkTrait,
)
from openassetio_mediacreation.traits.content import LocatableContentTrait
from openassetio_mediacreation.traits.identity import DisplayNameTrait
from openassetio_mediacreation.traits.imaging import CameraTrait
from openassetio_mediacreation.traits.threeDimensional import (
    GeometryTrait,
    LightingTrait,
    ShaderTrait,
    SpatialTrait,
)
from openassetio_mediacreation.traits.twoDimensional import (
    ImageCollectionTrait,
    ImageTrait,
)
from openassetio_mediacreation.traits.ui import (
    BrowserTrait,
    DetachedTrait,
    EntityProviderTrait,
    InPlaceTrait,
    SingleUseTrait,
    TabbedTrait,
)
from openassetio_mediacreation.traits.uiPolicy import ManagedTrait
from qtpy import QtCore, QtWidgets

from ayon_openassetio_manager import ayon, ayon_core_util, manager_core
from ayon_openassetio_manager.ayon_core_util import OpenAssetIOHost

# Mapping of MIME type to file extension/representation name.
_mime_to_extension = {
    "application/vnd.foundry.katana.fcurve+xml": "fcurve",
    "application/vnd.foundry.katana.histogram+xml": "hist",
    "application/vnd.foundry.katana.livegroup+xml": "livegroup",
    "application/vnd.foundry.katana.lookfile": "klf",
    "application/vnd.foundry.katana.lookfilemanager-settings+xml": "lfmexport",
    "application/vnd.foundry.katana.macro": "macro",
    "application/vnd.foundry.katana.project": "katana",
    "application/x-nuke": "nk",
    "application/vnd.aswf.opentimelineio": "otio",
    "text/x-edl": "edl",
    "image/*": "exr",  # Prefer publish to exr if we have a choice.
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/tiff": "tif",
    "image/x-deepshad": "deepshad",
    "image/x-dtex": "dtex",
    "image/x-exr": "exr",
    "image/x-rla": "rla",
    "model/vnd.usd": "usd",
    "model/vnd.usda": "usda",
    "model/vnd.usdz+zip": "usdz",
}

# Mapping of MIME type to product type. Used as a fallback when traits are
# insufficient.
_mime_to_product = {
    "application/vnd.foundry.katana.fcurve+xml": "settings",
    "application/vnd.foundry.katana.histogram+xml": "image",
    "application/vnd.foundry.katana.livegroup+xml": "layout",
    "application/vnd.foundry.katana.lookfile": "look",
    "application/vnd.foundry.katana.lookfilemanager-settings+xml": "settings",
    "application/vnd.foundry.katana.macro": "nodes",
    "application/vnd.foundry.katana.project": "workfile",
    "application/vnd.foundry.katana.rig+xml": "camera",
    "application/vnd.foundry.katana.scenegraph-bookmarks+xml": "settings",
    "inode/directory": "assembly",
    "model/vnd.usd": "usd",  # Interestingly not IANA registered,
                             # unlike usda and usdz.
    "model/vnd.usda": "usd",
    "model/vnd.usdz+zip": "usd",
}

# Unfortunately, we may need to fall back to knowing the specific host
# we're working within.
# TODO(DF): Some hosts may have multiple extensions.
_host_id_to_mime_type = {
    "com.foundry.katana.ui": "application/vnd.foundry.katana.project"}


class AyonUIDelegateState(UIDelegateStateInterface):
    """Implementation of the UI state object for the AYON UI delegate.

    The public members of the abstract base class will be exposed to the host
    application. Here, the implementation of the abstract base class methods
    simply return values stored in the object.

    Mutators (`set` methods) are added to allow mutation of the state after
    construction. Note that these methods will not be exposed to the host
    application.
    """

    # noinspection PyMissingConstructor
    def __init__(
        self,
        entity_references: Optional[list[EntityReference]] = None,
        entity_traits_datas: Optional[list[dict]] = None,
        update_request_callback: Optional[Callable] = None,
        native_data: Optional[dict] = None,
    ):
        """Construct the state object."""
        UIDelegateStateInterface.__init__(self)
        self.__entity_references = entity_references or []
        self.__entity_traits_datas = entity_traits_datas or []
        self.__update_request_callback = update_request_callback
        self.__native_data = native_data

    def setEntityReferences(self, entity_references) -> None:
        """Set the entity references.

        Args:
            entity_references (list[EntityReference]): The entity references.

        """
        self.__entity_references = entity_references

    def setEntityTraitsDatas(self, entity_traits_datas) -> None:
        """Set the entity traits datas.

        Args:
            entity_traits_datas (list[dict]): The entity traits datas.

        """
        self.__entity_traits_datas = entity_traits_datas

    def setUpdateRequestCallback(
            self, update_request_callback: Callable) -> None:
        """Set the update request callback.

        Args:
            update_request_callback (Callable): The update request callback.

        """
        self.__update_request_callback = update_request_callback

    def setNativeData(self, native_data: dict[str, Any]) -> None:
        """Set the native data.

        Args:
            native_data (dict[str, Any]): The native data.

        """
        self.__native_data = native_data

    # @override
    def entityReferences(self) -> list[EntityReference]:
        """Get the entity references.

        Returns:
            list[EntityReference]: The entity references.
        """
        return self.__entity_references

    # @override
    def entityTraitsDatas(self) -> list[TraitsData]:
        """Get the entity traits datas.

        Returns:
            list[TraitsData]: The entity traits datas.

        """
        return self.__entity_traits_datas

    # @override
    def nativeData(self) -> dict[str, Any]:
        """Get the native data.

        Returns:
            dict[str, Any]: The native data.

        """
        return self.__native_data

    # @override
    def updateRequestCallback(self) -> Optional[Callable]:
        """Get the update request callback.

        Returns:
            Optional[Callable]: The update request callback.

        """
        return self.__update_request_callback


class AyonOpenAssetIOUIDelegateInterfaceCore:
    """Core implementation of the AyonUIDelegateInterface.

    This class contains the actual implementation of the UI delegate interface,
    which relies on the runtime-imported ayon_core module.
    """
    __browser_name = "AYON Loader"
    __publish_name = "AYON Publish Context"

    @classmethod
    def uiPolicy(
        cls,
        uiTraits: set[str],
        uiAccess: access.UIAccess,
        _context: Context,
        _hostSession: HostSession,
    ):
        """Policy for UI request types.

        Hosts can call this to determine early if the UI delegate can
        potentially handle a request of this kind.

        Args:
            uiTraits (set[str]): The set of UI traits requested.
            uiAccess (access.UIAccess): The access level requested.
            context (Context): The context for the request.
            hostSession (HostSession): The host session.

        Returns:
            TraitsData: The policy traits data.

        """
        policy = TraitsData()

        # We can provide a browser that will emit entity references, regardless
        # of the access mode (i.e. we support loading and publishing).
        if {
            BrowserTrait.kId,
            EntityProviderTrait.kId,
        }.issubset(uiTraits):
            ManagedTrait.imbueTo(policy)
            # Host applications may choose to use the display name for window
            # decoration.
            DisplayNameTrait(policy).setName(
                cls.__browser_name if uiAccess == access.UIAccess.kRead else cls.__publish_name  # noqa: E501
            )

        return policy

    @classmethod
    def populateUI(
        cls,
        uiTraits: TraitsData,
        uiAccess: access.UIAccess,
        uiDelegateRequest: UIDelegateRequest,
        context: Context,
        hostSession: HostSession,
    ) -> AyonUIDelegateState | None:
        """Potentially create a UI element suitable for the given parameters.

        A return value of None indicates that the request is not supported.

        Args:
            uiTraits (TraitsData): The traits data for the UI.
            uiAccess (access.UIAccess): The access level for the UI.
            uiDelegateRequest (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            hostSession (HostSession): The host session.

        Returns:
            AyonUIDelegateState | None: The UI delegate state, or None if
                the request is not supported.

        """
        # noinspection PyBroadException
        try:
            widget = None
            initial_state = AyonUIDelegateState()

            if (
                uiAccess == access.UIAccess.kRead
                and BrowserTrait.isImbuedTo(uiTraits)
                and EntityProviderTrait.isImbuedTo(uiTraits)
            ):
                widget = cls.__create_loader(
                    uiTraits,
                    uiDelegateRequest,
                    context,
                    hostSession,
                    initial_state,
                )
            elif (
                uiAccess == access.UIAccess.kWrite
                and BrowserTrait.isImbuedTo(uiTraits)
                and EntityProviderTrait.isImbuedTo(uiTraits)
            ):
                widget = cls.__create_publisher(
                    uiTraits,
                    uiDelegateRequest,
                    context,
                    hostSession,
                    initial_state,
                )

            if widget is None:
                return None

            # If host requests an "in place" widget, then the host provided a
            # container widget that we should append to.
            if InPlaceTrait.isImbuedTo(uiTraits):
                container = uiDelegateRequest.nativeData()
                if container is not None:
                    if TabbedTrait.isImbuedTo(uiTraits):
                        tab_idx = container.addTab(widget, cls.__browser_name)
                        container.setCurrentIndex(tab_idx)
                    elif container.layout() is not None:
                        container.layout().addWidget(widget)
                    else:
                        widget.setParent(container)

            # If the host request a "detached" widget then the host wants to
            # place the widget in the hierarchy itself.
            if DetachedTrait.isImbuedTo(uiTraits):
                initial_state.setNativeData(widget)

        except Exception:  # noqa: BLE001
            import traceback

            hostSession.logger().error(
                f"Failed to display AYON UI: {traceback.format_exc()}")
            return None
        else:
            return initial_state

    @classmethod
    def __create_loader(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        host_session: HostSession,
        state: AyonUIDelegateState,
    ) -> Optional[QtWidgets.QWidget]:
        """Create a widget suitable for loading workfiles or representations.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            Optional[QtWidgets.QWidget]: The created widget, or None if
                creation failed.

        """
        if cls.__is_workfile_request(
                request.entityTraitsDatas(), host_session):
            return cls.__create_workfile_loader(
                ui_traits, request, context, host_session, state)

        return cls.__create_representation_loader(
            ui_traits, request, context, host_session, state
        )

    @classmethod
    def __create_publisher(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        host_session: HostSession,
        state: AyonUIDelegateState,
    ):
        """Create a widget for publishing workfiles or representations.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            Optional[QtWidgets.QWidget]: The created widget, or None if
                creation failed.

        """
        if cls.__is_workfile_request(
                request.entityTraitsDatas(), host_session):
            return cls.__create_workfile_publisher(
                ui_traits, request, context, host_session, state
            )

        return cls.__create_representation_publisher(
            ui_traits, request, context, host_session, state
        )

    @classmethod
    def __create_workfile_loader(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        host_session: HostSession,
        state: AyonUIDelegateState,
    ):
        """Create a widget suitable for loading workfiles.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            Optional[QtWidgets.QWidget]: The created widget, or None if
                creation failed.

        """
        entity_infos = [
            ayon.parse_entity_ref(str(ref))
            for ref in request.entityReferences()
        ]

        entity_info = ayon.EntityInfo(
            project_name=cls.__initial_project_name(entity_infos, context),
            path=cls.__initial_folder_path(entity_infos),
            task_name=cls.__initial_task_name(entity_infos),
            workfile_name=cls.__initial_representation_name(
                entity_infos, request.entityTraitsDatas(), host_session
            ),
        )

        if entity_info.workfile_name is None:
            host_session.logger().warning(
                "No file extension set for the workfiles browser.")
            return None

        # We require at least a project name to be set for the workfiles
        # browser. Show modal context selection dialog if not set.
        # TODO(DF): In hindsight, it would probably be better to shim a
        #  project combobox into the workfile loader widget.
        if entity_info.project_name is None:
            context_dialog = ContextDialog()

            context_dialog.exec_()

            selected_context = context_dialog.get_context()
            entity_info.project_name = selected_context["project_name"]
            entity_info.path = selected_context["folder_path"]
            entity_info.task_name = selected_context["task_name"]

        if entity_info.project_name is None:
            host_session.logger().warning(
                "No project name set for the workfiles browser.")
            return None

        # The workfiles browser requires a file extension. The host will report
        # the entity_info.workfile_name as the file extension.
        host = OpenAssetIOHost(entity_info)

        return WorkfileLoaderWidget(
            ui_traits, request, state, BaseWorkfileController(host))

    @classmethod
    def __create_representation_loader(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        _host_session: HostSession,
        state: AyonUIDelegateState,
    ):
        """Create a widget suitable for loading representations.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            _host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            RepresentationLoaderWidget: The created widget.

        """
        entity_infos = [
            ayon.parse_entity_ref(str(ref))
            for ref in request.entityReferences()
        ]

        entity_info = ayon.EntityInfo(
            project_name=cls.__initial_project_name(entity_infos, context),
            path=cls.__initial_folder_path(entity_infos),
            task_name=cls.__initial_task_name(entity_infos),
        )

        host = OpenAssetIOHost(
            entity_info) if entity_info is not None else None
        return RepresentationLoaderWidget(
            ui_traits, request, state, LoaderController(host))

    @classmethod
    def __create_representation_publisher(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        host_session: HostSession,
        state: AyonUIDelegateState,
    ):
        """Create a widget suitable for publishing representations.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            Optional[QtWidgets.QWidget]: The created widget, or None if
                creation failed.

        """
        entity_infos = [
            ayon.parse_entity_ref(str(ref))
            for ref in request.entityReferences()
        ]
        entity_traits_datas = request.entityTraitsDatas()

        # Calculate a product type, required for publishing.
        product_type = cls.__initial_product_type(
            entity_infos, entity_traits_datas)
        if product_type is None:
            host_session.logger().warning(
                "No product type found for the publish browser.")
            return None

        # Calculate a representation name, required for publishing.
        representation_name = cls.__initial_representation_name(
            entity_infos, entity_traits_datas, host_session
        )
        if representation_name is None:
            host_session.logger().warning(
                "No representation name found for the publish browser.")
            return None

        project_name = cls.__initial_project_name(entity_infos, context)
        folder_path = cls.__initial_folder_path(entity_infos)
        task_name = cls.__initial_task_name(entity_infos)
        variant_name = cls.__initial_variant_name(entity_infos)
        comment = cls.__initial_comment(entity_infos)

        entity_info = ayon.EntityInfo(
            project_name=project_name,
            path=folder_path,
            task_name=task_name,
            product_type=product_type,
            representation_name=representation_name,
            variant_name=variant_name,
            comment=comment,
        )

        return RepresentationPublishWidget(
            entity_info,
            ui_traits,
            request,
            state,
            RepresentationPublishController(entity_info),
        )

    @classmethod
    def __create_workfile_publisher(
        cls,
        ui_traits: TraitsData,
        request: UIDelegateRequest,
        context: Context,
        host_session: HostSession,
        state: AyonUIDelegateState,
    ):
        """Create a widget suitable for publishing workfiles.

        Args:
            ui_traits (TraitsData): The traits data for the UI.
            request (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            host_session (HostSession): The host session.
            state (AyonUIDelegateState): The UI delegate state.

        Returns:
            Optional[QtWidgets.QWidget]: The created widget, or None if
                creation failed.

        """
        entity_infos = [
            ayon.parse_entity_ref(str(ref))
            for ref in request.entityReferences()
        ]

        # For publishing, the workfile name is the same as a representation
        # name, i.e. a file extension - the file name will be generated.
        workfile_name = cls.__initial_representation_name(
            entity_infos, request.entityTraitsDatas(), host_session
        )
        if workfile_name is None:
            host_session.logger().warning(
                "No workfile name found for the publish browser.")
            return None

        entity_info = ayon.EntityInfo(
            project_name=cls.__initial_project_name(entity_infos, context),
            path=cls.__initial_folder_path(entity_infos),
            task_name=cls.__initial_task_name(entity_infos),
            workfile_name=workfile_name,
        )

        return WorkfilePublishWidget(
            entity_info,
            ui_traits,
            request,
            state,
            WorkfilePublishController(),
        )

    @staticmethod
    def __is_workfile_request(
            entity_traits_datas: list[TraitsData], host_session: HostSession):
        """Determine if we're dealing with workfiles or representations.

        We have three cases:
            1. Reading/publishing a non-workfile i.e. a representation.
            2. Reading/publishing a workfile as a representation.
            3. Reading/publishing an in-progress workfile.

        For reading, the the workfiles browser has a toggle to allow
        browsing published (representation) workfiles vs. registered
        in-progress workfiles. We do not currently have such support when
        publishing so must choose one or the other.

        For both reading and publishing, there is also the problem that _a_
        workfile might not be _the_ workfile, i.e. it might be something that
        categorises as a workfile, but is not the currently open
        project/script/scene, and is instead something that should be treated
        as a representation.

        TODO(DF): I think the correct thing to do is to allow the user to
            choose between workfile and representation in the UI. But there
            are currently no off-the-shelf AYON widgets for this.

        Args:
            entity_traits_datas (list[TraitsData]): The traits data for the
            host_session (HostSession): The host session.

        Returns:
            bool: True if we're dealing with workfiles,
                False for representations.


        """
        for traits_data in entity_traits_datas:
            # First condition to be a workfile is that the WorkTrait is imbued.
            # However, this is not sufficient - we may want something that
            # is categorised with a WorkTrait but is actually a representation,
            # e.g. a Katana Live Group.
            if not WorkTrait.isImbuedTo(traits_data):
                return False

            # Assume, for now, that if we have an entity whose MIME type does
            # not match the host's MIME type, then it is not an AYON workfile.
            target_mime_type = LocatableContentTrait(traits_data).getMimeType()
            if target_mime_type is not None:
                host_mime_type = _host_id_to_mime_type.get(
                    host_session.host().identifier())
                if (
                        host_mime_type is not None
                        and target_mime_type != host_mime_type
                ):
                    return False

        return True

    @staticmethod
    def __initial_project_name(
            entity_infos: list[ayon.EntityInfo],
            context: Context) -> Optional[str]:
        """Attempt to determine an initial target project name.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.
            context (Context): The OpenAssetIO context.

        Returns:
            Optional[str]: The initial project name, or None if not found.

        """
        for entity_info in entity_infos:
            if project_name := entity_info.project_name:
                return project_name

        # noinspection PyTypeChecker
        manager_state: manager_core.AyonManagerState = context.managerState

        if project_name := manager_state.settings.get("AYON_PROJECT_NAME"):
            return project_name

        if entity_info := manager_state.most_recent_resolved_entity_info:  # noqa: SIM102
            if project_name := entity_info.project_name:
                return project_name

        return None

    @staticmethod
    def __initial_folder_path(
        entity_infos: list[ayon.EntityInfo]
    ):
        """Attempt to determine an initial target folder path.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.

        Returns:
            Optional[str]: The initial folder path, or None if not found.

        """
        for entity_info in entity_infos:
            if folder_path := entity_info.path:
                return folder_path

        return None

    @staticmethod
    def __initial_task_name(
        entity_infos: list[ayon.EntityInfo],
    ) -> Optional[str]:
        """Attempt to determine an initial target task name.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.

        Returns:
            Optional[str]: The initial task name, or None if not found.

        """
        for entity_info in entity_infos:
            if task_name := entity_info.task_name:
                return task_name

        return None

    @staticmethod
    def __initial_product_type(  # noqa: C901, PLR0911, PLR0912
        entity_infos: list[ayon.EntityInfo],
        entity_traits_datas: list[TraitsData],
    ) -> Optional[str]:
        """Attempt to determine an initial target product type.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.
            entity_traits_datas (list[TraitsData]): The list of traits data.

        Returns:
            Optional[str]: The initial product type, or None if not found.

        """
        # Assume if an entity reference is provided, then it is the source of
        # truth.
        for entity_info in entity_infos:
            if entity_info.product_type:
                return entity_info.product_type

        # Map entity traits to product types.
        # TODO(DF): Completing this mapping unambiguously requires new
        #  MediaCreation traits/specifications - see
        #  https://docs.ayon.dev/docs/artist_publish/#product-types
        #  E.g. Image could be render, plate, layeredImage, background, ...
        #  Also should consider custom traits, e.g.
        #  katana_openassetio.traits.application.LookFileTrait
        for traits_data in entity_traits_datas:
            if ConfigTrait.isImbuedTo(traits_data):
                return "config"
            if (
                    ImageCollectionTrait.isImbuedTo(traits_data)
                    or ImageTrait.isImbuedTo(traits_data)):
                return "render"
            if CameraTrait.isImbuedTo(traits_data):
                return "camera"
            if ManifestTrait.isImbuedTo(traits_data):
                return "assembly"
            if GeometryTrait.isImbuedTo(traits_data):
                return "model"
            if (
                    LightingTrait.isImbuedTo(traits_data) or
                    ShaderTrait.isImbuedTo(traits_data)):
                return "look"
            if SpatialTrait.isImbuedTo(traits_data):
                return "layout"
            if WorkTrait.isImbuedTo(traits_data):
                return "workfile"

            # Fallback to MIME type mapping.
            locatable_content_trait = LocatableContentTrait(traits_data)
            if mime_types := locatable_content_trait.getMimeType():
                for mime_type in mime_types.split(","):
                    if product_type := _mime_to_product.get(mime_type):
                        return product_type

        return None

    @staticmethod
    def __initial_variant_name(
            entity_infos: list[ayon.EntityInfo]) -> Optional[str]:
        """Attempt to determine an initial target product variant.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.

        Returns:
            Optional[str]: The initial variant name, or None if not found.

        """
        return next(
            (
                entity_info.variant_name
                for entity_info in entity_infos
                if entity_info.variant_name
            ),
            None,
        )

    @staticmethod
    def __initial_product_name(
        entity_infos: list[ayon.EntityInfo],
        context: Context,
    ) -> Optional[str]:
        """Attempt to determine an initial target product name.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.
            context (Context): The OpenAssetIO context.

        Returns:
            Optional[str]: The initial product name, or None if not found.


        """
        for entity_info in entity_infos:
            if entity_info.product_name:
                return entity_info.product_name

        # noinspection PyTypeChecker
        manager_state: manager_core.AyonManagerState = context.managerState

        if entity_info := manager_state.most_recent_resolved_entity_info:  # noqa: SIM102
            if entity_info.product_name:
                return entity_info.product_name

        return None

    @staticmethod
    def __initial_representation_name(  # noqa: C901, PLR0911, PLR0912
        entity_infos: list[ayon.EntityInfo],
        entity_traits_datas: list[TraitsData],
        host_session: HostSession,
    ) -> Optional[str]:
        """Attempt to determine an initial target representation name.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.
            entity_traits_datas (list[TraitsData]): The list of traits data.
            host_session (HostSession): The host session.

        Returns:
            Optional[str]: The initial representation name,
                or None if not found.

        """
        # First check if we've been given an entity reference as a starting
        # point. If so, see if we can map it to a representation.
        for entity_info in entity_infos:
            if entity_info.representation_name:
                return entity_info.representation_name
            if entity_info.workfile_name:
                file_name, file_ext = os.path.splitext(
                    entity_info.workfile_name)
                if file_ext:
                    return file_ext.lstrip(".")
                if file_name:
                    return file_name

        # See if we can determine a representation name from the entity traits.
        # TODO(DF): Check and map custom traits.
        #  E.g. katana_openassetio.traits.application.LookFileTrait
        for traits_data in entity_traits_datas:
            # If the host has provided a MIME type or path, see if we can map
            # that to a representation name.
            locatable_content_trait = LocatableContentTrait(traits_data)
            if locatable_content_trait.isImbued():
                if mime_types := locatable_content_trait.getMimeType():
                    for mime_type in mime_types.split(","):
                        representation_name = _mime_to_extension.get(mime_type)
                        if representation_name is not None:
                            return representation_name

                if url := locatable_content_trait.getLocation():
                    _, representation_name = os.path.splitext(url)
                    if representation_name:
                        return representation_name.lstrip(".")

        # If we failed to determine a representation name so far, check if
        # we're publishing a workfile, and see if we have a mapping of host
        # identifier -> MIME type -> representation name.
        # TODO(DF): Also map AYON_HOST_NAME env var and/or
        #  `registered_host().extensions()`, if available.
        for traits_data in entity_traits_datas:
            if WorkTrait.isImbuedTo(traits_data):  # noqa: SIM102
                if mime_type := _host_id_to_mime_type.get(  # noqa: SIM102
                        host_session.host().identifier()):
                    if representation_name := _mime_to_extension.get(
                            mime_type):
                        return representation_name

        return None

    @staticmethod
    def __initial_comment(
        entity_infos: list[ayon.EntityInfo],
    ) -> Optional[str]:
        """Attempt to determine an initial target comment.

        Args:
            entity_infos (list[ayon.EntityInfo]): The list of entity infos.

        Returns:
            Optional[str]: The initial comment, or None if not found.

        """
        return next(
            (
                entity_info.comment
                for entity_info in entity_infos
                if entity_info.comment
            ),
            None,
        )


class WorkfileLoaderWidget(WorkfilesToolWindow):
    """Widget for loading workfiles from AYON."""
    def __init__(self, ui_traits, request, state, controller):
        """Construct the workfile loader widget."""
        super().__init__(controller=controller)
        self.__request = request
        self.__state = state

        self.__hidden_widgets = QtWidgets.QWidget()
        # noinspection PyProtectedMember
        self._files_widget._published_btns_widget.setParent(self.__hidden_widgets)
        # noinspection PyProtectedMember
        self._files_widget._workarea_btns_widget.setParent(self.__hidden_widgets)

        self.__selected_task_id = None

        # If we want continuous updates, trigger the callback whenever
        # the selection changed. Otherwise, we need OK/Cancel buttons.
        if not SingleUseTrait.isImbuedTo(ui_traits):
            controller.register_event_callback(
                "selection.workarea.changed", self.__maybe_callback)
            controller.register_event_callback(
                "selection.representation.changed", self.__maybe_callback
            )
        else:
            controller.register_event_callback(
                "selection.workarea.changed",
                self.__on_ok_button_state_invalidated
            )
            controller.register_event_callback(
                "selection.representation.changed",
                self.__on_ok_button_state_invalidated
            )
            # The layout of this widget is a HBox, but we need a VBox
            # so we can add OK and Cancel buttons to the bottom right
            # of the window.
            ok_btn = QtWidgets.QPushButton("Open")
            ok_btn.setEnabled(False)
            cancel_btn = QtWidgets.QPushButton("Cancel")

            prev_layout = self.layout()
            content_widget = QtWidgets.QWidget()
            content_widget.setLayout(prev_layout)
            new_layout = QtWidgets.QVBoxLayout()
            self.setLayout(new_layout)
            new_layout.addWidget(content_widget)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setContentsMargins(5, 0, 5, 5)
            btn_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            btn_layout.setSpacing(5)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            new_layout.addLayout(btn_layout)

            ok_btn.clicked.connect(self.__maybe_callback)
            cancel_btn.clicked.connect(self.__on_cancel_clicked)
            self.__ok_btn = ok_btn

    def __on_cancel_clicked(self) -> None:
        """Callback for the Cancel button.

        Note this is only used if SingleUseTrait is imbued to the UI
        traits.

        This will clear the entity references. Closing the window is
        up to the host application.
        """
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is not None:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)

    def __on_ok_button_state_invalidated(self):
        project_name = self._controller.get_current_project_name()
        workfile_path = self._controller.get_selected_workfile_path()
        representation_id = self._controller.get_selected_representation_id()
        self.__ok_btn.setEnabled(bool(
            project_name and (representation_id or workfile_path)))

    def __maybe_callback(self):
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is None:
            return

        project_name = self._controller.get_current_project_name()
        workfile_path = self._controller.get_selected_workfile_path()
        representation_id = self._controller.get_selected_representation_id()

        if not project_name or not (representation_id or workfile_path):
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)
            return

        if representation_id:
            # Convert IDs to AYON URIs (i.e. entity references).
            uri_response = ayon_api.post(
                f"projects/{project_name}/uris",
                entityType="representation",
                ids=[representation_id],
            )
            entity_ref_str = uri_response.data["uris"][-1]["uri"]

            task_name = self._controller.get_selected_task_name()

            # Add the task name, if any, so that when we save it will
            # also associate with the task.
            if task_name is not None:
                entity_info = ayon.parse_entity_ref(entity_ref_str)
                entity_info.task_name = task_name
                entity_ref_str = ayon.build_entity_ref(entity_info)

        else:
            folder_id = self._controller.get_selected_folder_id()
            task_id = self._controller.get_selected_task_id()

            # TODO(DF): It is possible to have physical workfiles
            #  shown in the browser that do not have corresponding
            #  database entries, in which case resolve() will fail.

            folder_entity = ayon_api.get_folder_by_id(
                project_name, folder_id, fields=["path"])
            task_entity = ayon_api.get_task_by_id(
                project_name, task_id, fields=["name"])
            entity_info = ayon.EntityInfo(
                project_name=project_name,
                path=folder_entity["path"],
                task_name=task_entity["name"],
                workfile_name=pathlib.Path(workfile_path).name,
            )
            entity_ref_str = ayon.build_entity_ref(entity_info)

        if entity_ref_str is None:
            return

        entity_ref = EntityReference(entity_ref_str)
        self.__state.setEntityReferences([entity_ref])
        state_changed_cb(self.__state)


class RepresentationLoaderWidget(LoaderWindow):
    """Widget for loading representations from AYON."""
    def __init__(self, ui_traits, request, state, controller):
        """Construct the representation loader widget."""
        super().__init__(controller)
        self.__request = request
        self.__state = state
        self._projects_combobox.set_standard_filter_enabled(False)

        # If we want continuous updates, trigger the callback whenever
        # the selection changed. Otherwise, we need OK/Cancel buttons.
        if not SingleUseTrait.isImbuedTo(ui_traits):
            self._controller.register_event_callback(
                "selection.representations.changed", self.__maybe_callback
            )
        else:
            self._controller.register_event_callback(
                "selection.representations.changed",
                self.__on_ok_button_state_invalidated
            )
            # The layout of this widget is a HBox, but we need a VBox
            # so we can add OK and Cancel buttons to the bottom right
            # of the window.
            ok_btn = QtWidgets.QPushButton("Open")
            ok_btn.setEnabled(False)
            cancel_btn = QtWidgets.QPushButton("Cancel")

            prev_layout = self.layout()
            content_widget = QtWidgets.QWidget()
            content_widget.setLayout(prev_layout)
            new_layout = QtWidgets.QVBoxLayout()
            self.setLayout(new_layout)
            new_layout.addWidget(content_widget)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setContentsMargins(5, 0, 5, 5)
            btn_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            btn_layout.setSpacing(5)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            new_layout.addLayout(btn_layout)

            ok_btn.clicked.connect(self.__maybe_callback)
            cancel_btn.clicked.connect(self.__on_cancel_clicked)
            self.__ok_btn = ok_btn

    def __on_ok_button_state_invalidated(self):
        project_name = self._controller.get_selected_project_name()
        representation_ids = self._controller.get_selected_representation_ids()
        self.__ok_btn.setEnabled(bool(project_name and representation_ids))

    def __on_cancel_clicked(self):
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is not None:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)

    def __maybe_callback(self):
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is None:
            return
        project_name = self._controller.get_selected_project_name()
        representation_ids = self._controller.get_selected_representation_ids()
        if not project_name or not representation_ids:
            return

        representation_id = next(iter(representation_ids))
        # Convert IDs to AYON URIs (i.e. entity references).
        uri_response = ayon_api.post(
            f"projects/{project_name}/uris",
            entityType="representation",
            ids=[representation_id],
        )
        if entity_ref_strs := uri_response.data.get("uris"):
            entity_ref_str = entity_ref_strs[-1]["uri"]
            entity_ref = EntityReference(entity_ref_str)
            self.__state.setEntityReferences([entity_ref])
            state_changed_cb(self.__state)


class RepresentationPublishController(PushToContextController):
    """Controller for publishing representations to AYON."""
    def __init__(self, entity_info):
        """Constructor."""
        super().__init__()
        # Pre-populate text boxes. Tree views are pre-populated in widget
        # constructor.
        variant_name = "Main"
        if entity_info.variant_name:
            variant_name = entity_info.variant_name
        if entity_info.comment:
            self._user_values.set_comment(entity_info.comment)

        self._user_values.set_variant(variant_name)

    def set_selected_task(self, task_id, task_name) -> None:
        """Override to invalidate when the task changes.

        Args:
            task_id (str): The selected task ID.
            task_name (str): The selected task name.

        """
        super().set_selected_task(task_id, task_name)
        self._invalidate()

    def _check_submit_validations(self) -> bool:
        """Check if the form is valid for submission.

        Override to additionally enforce a task name.

        A task name is required when calculating the product name
        during publishing.

        Returns:
            bool: True if the form is valid for submission,
                False otherwise.

        """
        is_valid = super()._check_submit_validations()
        if not is_valid:
            return False
        return bool(
            self._selection_model.get_selected_task_name()
            or self._user_values.new_folder_name
        )

    def expected_project_selected(self, project_name):
        # Doesn't exist on base, yet will be called by widget.
        pass

    def expected_folder_selected(self, folder_id):
        # Doesn't exist on base, yet will be called by widget.
        pass

    def expected_task_selected(self, folder_id, task_name):
        # Doesn't exist on base, yet will be called by widget.
        pass


class RepresentationPublishWidget(PushToContextSelectWindow):
    """Widget for publishing representations to AYON."""
    def __init__(
        self,
        entity_info,
        ui_traits,
        request,
        state,
        controller,
    ):
        """Constructor."""
        super().__init__(controller=controller)
        self.__ui_traits = ui_traits
        self.__request = request
        self.__state = state
        self.__representation_name = entity_info.representation_name
        self.__product_type = entity_info.product_type

        self.__hidden_widgets = QtWidgets.QWidget()

        # Remove buttons, we have our own logic.
        self._header_label.setParent(self.__hidden_widgets)
        self._publish_btn.parent().setParent(self.__hidden_widgets)
        self._new_folder_checkbox.setChecked(False)

        # TODO(DF): Creating new folders as part of publishing adds
        #  significant complexity. So restrict to existing folders
        #  for now.
        inputs_layout = self._folder_name_input.parent().layout()
        result = inputs_layout.takeRow(0)
        result.labelItem.widget().setParent(self.__hidden_widgets)
        result.fieldItem.widget().setParent(self.__hidden_widgets)
        result = inputs_layout.takeRow(0)
        result.labelItem.widget().setParent(self.__hidden_widgets)
        result.fieldItem.widget().setParent(self.__hidden_widgets)

        self._projects_combobox.set_standard_filter_enabled(False)
        # Pre-populate the project combobox.
        if entity_info.project_name is not None:
            self._projects_combobox._handle_expected_selection = True
            self._projects_combobox._expected_selection = (
                entity_info.project_name)

        # Pre-populate the folder tree and task tree widgets.
        if entity_info.comment:
            # For some reason setting only in the controller
            # doesn't update the UI.
            self._comment_input.setText(entity_info.comment)

        if entity_info.project_name and entity_info.path:
            folder_data = ayon_api.get_folder_by_path(
                entity_info.project_name, entity_info.path, fields=["id"]
            )
            if folder_data:
                self._folders_widget._handle_expected_selection = True
                self._folders_widget._expected_selection = folder_data["id"]

                if entity_info.task_name:
                    self._tasks_widget._handle_expected_selection = True
                    self._tasks_widget._expected_selection_data = {
                        "task_name": entity_info.task_name,
                        "folder_id": folder_data["id"],
                    }

        # If we want continuous updates, trigger the callback whenever
        # the selection changed. Otherwise, we need OK/Cancel buttons.
        if not SingleUseTrait.isImbuedTo(ui_traits):
            self._controller.register_event_callback(
                "selection.project.changed", self.__maybe_callback
            )
            self._controller.register_event_callback(
                "selection.folder.changed", self.__maybe_callback
            )
            self._controller.register_event_callback(
                "selection.task.changed", self.__maybe_callback
            )
            self._controller.register_event_callback(
                "submission.enabled.changed", self.__maybe_callback
            )
        else:
            self._controller.register_event_callback(
                "submission.enabled.changed",
                self.__on_ok_button_state_invalidated
            )
            ok_btn = QtWidgets.QPushButton("Save")
            ok_btn.setEnabled(False)
            cancel_btn = QtWidgets.QPushButton("Cancel")

            # prev_layout = self.layout()
            # content_widget = QtWidgets.QWidget()
            # content_widget.setLayout(prev_layout)
            # new_layout = QtWidgets.QVBoxLayout()
            # self.setLayout(new_layout)
            # new_layout.addWidget(content_widget)
            #
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setContentsMargins(5, 0, 5, 5)
            btn_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            btn_layout.setSpacing(5)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            self._main_context_widget.layout().addLayout(btn_layout)

            ok_btn.clicked.connect(self.__maybe_callback)
            cancel_btn.clicked.connect(self.__on_cancel_clicked)
            self.__ok_btn = ok_btn

    def __on_ok_button_state_invalidated(self, event) -> None:
        self.__ok_btn.setEnabled(event.data["enabled"])

    def __on_cancel_clicked(self) -> None:
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is not None:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)

    def _on_user_input_timer(self) -> None:
        super()._on_user_input_timer()
        if not SingleUseTrait.isImbuedTo(self.__ui_traits):
            self.__maybe_callback()

    def __maybe_callback(self) -> None:
        """Callback to notify host of selection.

        Notify the host application of currently selected entities, if
        any.

        """
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is None:
            return
        # noinspection PyProtectedMember
        if not self._controller._submission_enabled:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)
            return

        # Extract fields from models.
        # noinspection PyProtectedMember
        project_name = (
            self._controller._selection_model.get_selected_project_name())
        # noinspection PyProtectedMember
        selected_folder_id = (
            self._controller._selection_model.get_selected_folder_id())
        # noinspection PyProtectedMember
        task_name = self._controller._selection_model.get_selected_task_name()
        # noinspection PyProtectedMember
        variant_name = self._controller._user_values.variant
        # noinspection PyProtectedMember
        comment = self._controller._user_values.comment

        # Get path of selected folder.
        selected_folder_path = ayon_api.get_folder_by_id(
            project_name, selected_folder_id, fields=["path"]
        )["path"]

        entity_info = ayon.EntityInfo(
            project_name=project_name,
            path=selected_folder_path,
            task_name=task_name,
            variant_name=variant_name,
            comment=comment,
            representation_name=self.__representation_name,
            product_type=self.__product_type,
        )

        # Construct a product name
        product_name = ayon_core_util.query_product_name_for_entity(entity_info)
        if product_name:
            entity_info.product_name = product_name

        entity_ref = EntityReference(ayon.build_entity_ref(entity_info))

        self.__state.setEntityReferences([entity_ref])
        state_changed_cb(self.__state)


class WorkfilePublishController(ContextDialogController):
    """A controller for publishing workfiles to AYON."""
    def expected_task_selected(self, folder_id: str, task_name: str) -> None:
        """Selection of expected task handler.

        Doesn't exist on base, yet will be called by tasks widget.

        Args:
            folder_id (str): The folder ID.
            task_name (str): The task name.

        """


class WorkfilePublishWidget(ContextDialog):
    """A dialog for publishing workfiles to AYON."""
    def __init__(
        self,
        entity_info,
        ui_traits,
        request,
        state,
        controller,
    ):
        """Initialize the workfile publish widget."""
        super().__init__(controller=controller)
        self.__request = request
        self.__state = state
        self.__workfile_name = entity_info.workfile_name
        # We need to treat this QDialog like any other widget, so
        # disable the Dialog flag.
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.Dialog)

        # Must do this or get_context() will return all None.
        self._controller.confirm_selection()

        # Attempt to pre-select fields. Note that the "initial
        # context" mechanism, if used, disables the project combobox.
        if entity_info.project_name:
            self._controller.set_initial_context(
                entity_info.project_name, entity_info.path)
            initial_context = self._controller.get_initial_context()
            initial_folder_id = initial_context["folder_id"]

            # Attempt to pre-select the task name.
            if initial_folder_id and entity_info.task_name:
                self._tasks_widget._handle_expected_selection = True
                self._tasks_widget._expected_selection_data = {
                    "folder_id": initial_folder_id,
                    "task_name": entity_info.task_name,
                }

        # Hide the default OK button, we have our own logic.
        self.__hidden_widgets = QtWidgets.QWidget()
        self._ok_btn.setParent(self.__hidden_widgets)

        # If we want continuous updates, trigger the callback whenever
        # the selection changed. Otherwise, we need OK/Cancel buttons.
        if not SingleUseTrait.isImbuedTo(ui_traits):
            self._controller.register_event_callback(
                "selection.project.changed", self.__maybe_callback
            )
            self._controller.register_event_callback(
                "selection.folder.changed", self.__maybe_callback
            )
            self._controller.register_event_callback(
                "selection.task.changed", self.__maybe_callback
            )
        else:
            self._controller.register_event_callback(
                "selection.project.changed",
                self.__on_ok_button_state_invalidated
            )
            self._controller.register_event_callback(
                "selection.folder.changed",
                self.__on_ok_button_state_invalidated
            )
            self._controller.register_event_callback(
                "selection.task.changed",
                self.__on_ok_button_state_invalidated
            )
            ok_btn = QtWidgets.QPushButton("Save")
            ok_btn.setEnabled(False)
            cancel_btn = QtWidgets.QPushButton("Cancel")

            prev_layout = self.layout()
            content_widget = QtWidgets.QWidget()
            content_widget.setLayout(prev_layout)
            new_layout = QtWidgets.QVBoxLayout()
            self.setLayout(new_layout)
            new_layout.addWidget(content_widget)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setContentsMargins(5, 0, 5, 5)
            btn_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            btn_layout.setSpacing(5)
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            new_layout.addLayout(btn_layout)

            ok_btn.clicked.connect(self.__maybe_callback)
            cancel_btn.clicked.connect(self.__on_cancel_clicked)
            self.__ok_btn = ok_btn

    def _set_init_context(self, init_context: dict[str, Any]) -> None:
        """Handler for initial context change on controller.

        Override to undo the disabling of project and folder selection.

        Args:
            init_context (dict[str, Any]): Initial context data.

        """
        super()._set_init_context(init_context)
        self._project_combobox.setEnabled(True)
        self._folders_widget.setEnabled(True)

    def __on_ok_button_state_invalidated(self) -> None:
        selected_context = self._controller.get_selected_context()
        project_name = selected_context["project_name"]
        path = selected_context["folder_path"]
        task_name = selected_context["task_name"]

        self.__ok_btn.setEnabled(bool(project_name and path and task_name))

    def __on_cancel_clicked(self) -> None:
        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is not None:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)

    def __maybe_callback(self) -> None:
        selected_context = self._controller.get_selected_context()
        project_name = selected_context["project_name"]
        path = selected_context["folder_path"]
        task_name = selected_context["task_name"]

        state_changed_cb = self.__request.stateChangedCallback()
        if state_changed_cb is None:
            return
        if not project_name or not path or not task_name:
            self.__state.setEntityReferences([])
            state_changed_cb(self.__state)
            return
        entity_info = ayon.EntityInfo(
            project_name=project_name,
            path=path,
            task_name=task_name,
            workfile_name=self.__workfile_name,
        )

        entity_ref_str = ayon.build_entity_ref(entity_info)
        entity_ref = EntityReference(entity_ref_str)
        self.__state.setEntityReferences([entity_ref])
        state_changed_cb(self.__state)
