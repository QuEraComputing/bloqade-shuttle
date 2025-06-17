from dataclasses import dataclass, field
from itertools import product

import numpy as np
from bloqade.geometry.dialects.grid.types import Grid
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.widgets import Button

from bloqade.shuttle.codegen import taskgen
from bloqade.shuttle.dialects import path

from .interface import RendererInterface


def default_ax() -> Axes:
    """Create a default matplotlib Axes object."""
    _, ax = plt.subplots(1, 1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X (um)")
    ax.set_ylabel("Y (um)")
    return ax


@dataclass
class GateDisplayOptions:
    rydberg_color: str = field(default="red")
    r_color: str = field(default="blue")
    rz_color: str = field(default="green")
    local_spot_size: float = field(default=6.0)
    alpha: float = field(default=0.3)


@dataclass
class MatplotlibRenderer(RendererInterface):
    ax: Axes = field(default_factory=default_ax, repr=False)

    gate_display_options: GateDisplayOptions = field(default_factory=GateDisplayOptions)

    active_x_tones: set[int] = field(default_factory=set, repr=False, init=False)
    active_y_tones: set[int] = field(default_factory=set, repr=False, init=False)
    curr_path_lines: list[Artist] = field(default_factory=list, repr=False, init=False)

    xmin: float = field(init=False)
    xmax: float = field(init=False)
    ymin: float = field(init=False)
    ymax: float = field(init=False)
    sleep_time: float = field(default=0.1, kw_only=True)
    sleeping: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        fig = plt.gcf()
        fig.subplots_adjust(bottom=0.2)
        continue_ax = fig.add_axes((0.01, 0.01, 0.1, 0.075))
        exit_ax = fig.add_axes((0.21, 0.01, 0.1, 0.075))

        self.continue_button = Button(continue_ax, "Continue")
        self.exit_button = Button(exit_ax, "Exit")
        self.exit_button.on_clicked(lambda event: exit())

    def update_x_bounds(self, y: float) -> None:
        xmin = min(curr_xmin := getattr(self, "xmin", float("inf")), y - 3)
        xmax = max(curr_xmax := getattr(self, "xmax", float("-inf")), y + 3)

        if xmin < curr_xmin or xmax > curr_xmax:
            self.xmin = xmin
            self.xmax = xmax
            self.ax.set_xlim(self.xmin, self.xmax)

    def update_y_bounds(self, y: float) -> None:
        ymin = min(curr_ymin := getattr(self, "ymin", float("inf")), y - 3)
        ymax = max(curr_ymax := getattr(self, "ymax", float("-inf")), y + 3)

        if ymin < curr_ymin or ymax > curr_ymax:
            self.ymin = ymin
            self.ymax = ymax
            self.ax.set_ylim(self.ymin, self.ymax)

    def render_traps(self, traps: Grid, zone_id: str) -> None:
        x, y = np.meshgrid(traps.x_positions, traps.y_positions)

        self.ax.plot(x.flatten(), y.flatten(), marker="o", markersize=3, linestyle="")
        self.update_x_bounds(traps.x_positions[0])
        self.update_x_bounds(traps.x_positions[-1])
        self.update_y_bounds(traps.y_positions[0])
        self.update_y_bounds(traps.y_positions[-1])

    def top_hat_cz(
        self, location: Grid, upper_buffer: float, lower_buffer: float
    ) -> None:
        ymin, ymax = location.y_bounds()

        assert ymin is not None and ymax is not None, "Y bounds must be defined"
        ymin = ymin - lower_buffer
        ymax = ymax + upper_buffer
        ymin_keepout = ymin - 3
        ymax_keepout = ymax + 3
        x = [self.xmin - 10, self.xmax + 10]
        inner = self.ax.fill_between(
            x,
            ymin,
            ymax,
            color=self.gate_display_options.rydberg_color,
            alpha=self.gate_display_options.alpha,
        )
        outer = self.ax.fill_between(
            x,
            ymin_keepout,
            ymax_keepout,
            color=self.gate_display_options.rydberg_color,
            alpha=self.gate_display_options.alpha / 2,
        )

        self.show()
        inner.remove()
        outer.remove()

    def local_r(self, location: Grid) -> None:
        x, y = np.meshgrid(location.x_positions, location.y_positions)

        (points,) = self.ax.plot(
            x.flatten(),
            y.flatten(),
            marker="o",
            markersize=self.gate_display_options.local_spot_size,
            linestyle="",
            color=self.gate_display_options.r_color,
            alpha=self.gate_display_options.alpha,
        )

        self.show()
        points.remove()

    def local_rz(self, location: Grid) -> None:
        x, y = np.meshgrid(location.x_positions, location.y_positions)

        (points,) = self.ax.plot(
            x.flatten(),
            y.flatten(),
            marker="o",
            markersize=self.gate_display_options.local_spot_size,
            linestyle="",
            color=self.gate_display_options.rz_color,
            alpha=self.gate_display_options.alpha,
        )

        self.show()
        points.remove()

    def global_r(self) -> None:
        x = [self.xmin - 10, self.xmax + 10]
        y = [self.ymin - 10, self.ymax + 10]

        line = self.ax.fill_between(
            x,
            y[0],
            y[1],
            color=self.gate_display_options.r_color,
            alpha=self.gate_display_options.alpha,
        )
        self.show()
        line.remove()

    def global_rz(self) -> None:
        x = [self.xmin - 10, self.xmax + 10]
        y = [self.ymin - 10, self.ymax + 10]

        line = self.ax.fill_between(
            x,
            y[0],
            y[1],
            color=self.gate_display_options.rz_color,
            alpha=self.gate_display_options.alpha / 2,
        )

        self.show()
        line.remove()

    def render_path(self, pth: path.Path) -> None:
        all_waypoints = [
            way_point
            for path_action in pth.path
            if isinstance(path_action, taskgen.WayPointsAction)
            for way_point in path_action.way_points
        ]

        if len(all_waypoints) == 0:
            return

        first_waypoint = all_waypoints[0]
        curr_x = first_waypoint.x_positions
        curr_y = first_waypoint.y_positions

        color_map = plt.get_cmap("viridis")

        num_steps = len(all_waypoints) - 1
        step = 0

        x_tones = np.array(pth.x_tones)
        y_tones = np.array(pth.y_tones)

        x = all_waypoints[0].x_positions
        y = all_waypoints[0].y_positions

        for action in pth.path:
            if isinstance(action, taskgen.WayPointsAction):
                for way_point in action.way_points:
                    x = way_point.x_positions
                    y = way_point.y_positions

                    for (x_tone, x_start, x_end), (y_tone, y_start, y_end) in product(
                        zip(pth.x_tones, curr_x, x), zip(pth.y_tones, curr_y, y)
                    ):
                        self.update_x_bounds(x_start)
                        self.update_x_bounds(x_end)
                        self.update_y_bounds(y_start)
                        self.update_y_bounds(y_end)
                        dx = x_end - x_start
                        dy = y_end - y_start

                        if dx == 0 and dy == 0:
                            continue

                        is_on = (
                            x_tone in self.active_x_tones
                            and y_tone in self.active_y_tones
                        )

                        line = self.ax.arrow(
                            x_start,
                            y_start,
                            dx,
                            dy,
                            width=0.1,
                            color=color_map(step / num_steps),
                            length_includes_head=True,
                            linestyle="-" if is_on else (0, (5, 10)),
                            alpha=1.0 if is_on else 0.5,
                            linewidth=1.0 if is_on else 0.5,
                        )

                        line.set_edgecolor(line.get_facecolor())
                        self.curr_path_lines.append(line)

                    curr_x = x
                    curr_y = y
                    step += 1

            elif isinstance(action, taskgen.TurnOnAction):
                self.active_x_tones.update(x_tones[action.x_tone_indices])
                self.active_y_tones.update(y_tones[action.y_tone_indices])

            elif isinstance(action, taskgen.TurnOffAction):
                self.active_x_tones.difference_update(x_tones[action.x_tone_indices])
                self.active_y_tones.difference_update(y_tones[action.y_tone_indices])

    def set_title(self, title: str) -> None:
        self.ax.set_title(title)

    def show(self) -> None:
        plt.show(block=False)
        self.continue_button.on_clicked(lambda event: setattr(self, "sleeping", False))

        self.sleeping = True
        while self.sleeping:
            plt.pause(self.sleep_time)

    def clear_paths(self) -> None:
        while self.curr_path_lines:
            artist = self.curr_path_lines.pop()
            artist.remove()

        self.ax.set_title("")
        plt.show(block=False)
