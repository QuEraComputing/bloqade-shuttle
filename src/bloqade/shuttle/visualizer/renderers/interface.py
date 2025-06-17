from abc import ABC, abstractmethod

from bloqade.geometry.dialects import grid

from bloqade.shuttle.dialects import path


class RendererInterface(ABC):

    def local_r(self, location: grid.Grid) -> None:
        """Render the local render of the given location.

        Args:
            location (grid.Grid): The location to render.

        """

    def local_rz(self, location: grid.Grid) -> None:
        """Render the local render of the given location.

        Args:
            location (grid.Grid): The location to render.

        """

    def global_r(self) -> None:
        """Render the global render of the given location.

        Args:
            location (grid.Grid): The location to render.

        """

    def global_rz(self) -> None:
        """Render the global render of the given location.

        Args:
            location (grid.Grid): The location to render.

        """

    def top_hat_cz(
        self, location: grid.Grid, upper_buffer: float, lower_buffer: float
    ) -> None:
        """Render the top hat CZ of the given location.

        Args:
            location (grid.Grid): The location to render.

        """

    @abstractmethod
    def render_traps(self, traps: grid.Grid, zone_id: str) -> None:
        """Render the given traps.

        Args:
            traps (ilist.IList[grid.Grid, Any]): The traps to render.

        """
        ...

    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set the title of the renderer.

        Args:
            title (str): The title to set.

        """
        ...

    @abstractmethod
    def render_path(self, pth: path.Path) -> None:
        """Render the given path.

        Args:
            pth (path.Path): The path to render.

        """
        ...

    @abstractmethod
    def show(self) -> None:
        """Show all rendered entities."""
        ...

    @abstractmethod
    def clear_paths(self) -> None:
        """Clear the current renderer."""
        ...
