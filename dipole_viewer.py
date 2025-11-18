"""Dipole visualization and animation tool.

This module provides a simple command line interface that renders
2D electric dipoles, visualises their electric field via a quiver plot
and animates the rotation of their dipole moment.

Example:
    python dipole_viewer.py --dipole "0,0,1,0" --dipole "1,0,-1,0" \
        --grid-limit 3 --frames 120 --rotation-speed 2

"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


@dataclass
class Dipole:
    """Simple data class for a 2D dipole."""

    position: np.ndarray
    moment: np.ndarray
    color: str = "tab:blue"
    label: str | None = None

    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=float)
        self.initial_moment = np.asarray(self.moment, dtype=float)
        self.moment = self.initial_moment.copy()

    def rotated_moment(self, angle_rad: float) -> np.ndarray:
        """Return the initial dipole moment rotated by ``angle_rad``."""

        c, s = math.cos(angle_rad), math.sin(angle_rad)
        rotation = np.array([[c, -s], [s, c]])
        return rotation @ self.initial_moment


class DipoleSimulation:
    """Encapsulates dipole field computation and animation."""

    def __init__(
        self,
        dipoles: Sequence[Dipole],
        grid_limit: float = 3.0,
        grid_size: int = 20,
        softening: float = 0.15,
    ) -> None:
        if grid_size < 5:
            raise ValueError("grid_size should be >= 5 to visualise the field")
        self.dipoles = list(dipoles)
        self.grid_limit = grid_limit
        self.grid_size = grid_size
        self.softening = softening
        self._prepare_grid()

    def _prepare_grid(self) -> None:
        lin = np.linspace(-self.grid_limit, self.grid_limit, self.grid_size)
        self._grid_x, self._grid_y = np.meshgrid(lin, lin)
        self._grid_points = np.column_stack(
            (self._grid_x.ravel(), self._grid_y.ravel())
        )

    def _field_for_points(self) -> np.ndarray:
        field = np.zeros_like(self._grid_points)
        for dipole in self.dipoles:
            r = self._grid_points - dipole.position
            r2 = np.sum(r**2, axis=1) + self.softening**2
            r_norm = np.sqrt(r2)
            r3 = r_norm**3 + self.softening
            r5 = r_norm**5 + self.softening
            dot = r @ dipole.moment
            term1 = 3 * r * dot[:, None] / r5[:, None]
            term2 = dipole.moment / r3[:, None]
            field += term1 - term2
        return field

    def _normalised_field_components(self, field: np.ndarray) -> np.ndarray:
        reshaped = field.reshape(self.grid_size, self.grid_size, 2)
        magnitude = np.linalg.norm(reshaped, axis=2)
        max_magnitude = np.max(magnitude)
        if max_magnitude > 0:
            reshaped /= max_magnitude
        return reshaped

    def animate(self, frames: int, rotation_speed: float, interval: int, save: str | None) -> None:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(-self.grid_limit, self.grid_limit)
        ax.set_ylim(-self.grid_limit, self.grid_limit)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title("Animated dipole field")
        ax.set_aspect("equal")

        field = self._normalised_field_components(self._field_for_points())
        quiver = ax.quiver(
            self._grid_x,
            self._grid_y,
            field[:, :, 0],
            field[:, :, 1],
            pivot="mid",
            color="0.3",
            linewidth=0.5,
            scale=20,
        )

        dipole_artists = []
        for dip in self.dipoles:
            dipole_artist = ax.quiver(
                dip.position[0],
                dip.position[1],
                dip.moment[0],
                dip.moment[1],
                angles="xy",
                scale_units="xy",
                scale=1,
                width=0.02,
                color=dip.color,
            )
            label = dip.label or f"({dip.position[0]:.2f}, {dip.position[1]:.2f})"
            ax.text(
                dip.position[0],
                dip.position[1],
                label,
                color=dip.color,
                fontsize=9,
                ha="center",
                va="bottom",
            )
            dipole_artists.append(dipole_artist)

        def update(frame_index: int):
            angle_rad = math.radians(rotation_speed * frame_index)
            for dip, artist in zip(self.dipoles, dipole_artists):
                dip.moment = dip.rotated_moment(angle_rad)
                artist.set_UVC(dip.moment[0], dip.moment[1])
            updated_field = self._normalised_field_components(self._field_for_points())
            quiver.set_UVC(updated_field[:, :, 0], updated_field[:, :, 1])
            return [quiver, *dipole_artists]

        animation = FuncAnimation(
            fig,
            update,
            frames=frames,
            interval=interval,
            blit=True,
            repeat=True,
        )

        if save:
            animation.save(save, dpi=150)
            print(f"Animation saved to {save}")
        else:
            plt.show()


def parse_dipole(spec: str, default_color: str = "tab:blue") -> Dipole:
    """Parse a dipole specification string."""

    parts = [part.strip() for part in spec.split(",")]
    if len(parts) not in {4, 5}:
        raise argparse.ArgumentTypeError(
            "Dipole specification must be 'x,y,mx,my[,color]'"
        )
    try:
        x, y, mx, my = map(float, parts[:4])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Dipole coordinates must be numeric") from exc
    color = parts[4] if len(parts) == 5 else default_color
    return Dipole(position=np.array([x, y]), moment=np.array([mx, my]), color=color)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Visualise dipoles in 2D")
    parser.add_argument(
        "--dipole",
        action="append",
        metavar="SPEC",
        help="Dipole spec 'x,y,mx,my[,color]'. Can be given multiple times.",
    )
    parser.add_argument("--grid-limit", type=float, default=3.0, help="Plot radius")
    parser.add_argument(
        "--grid-size",
        type=int,
        default=20,
        help="Number of samples per axis for the field grid",
    )
    parser.add_argument("--frames", type=int, default=180, help="Frames per animation loop")
    parser.add_argument("--rotation-speed", type=float, default=1.5, help="Degrees per frame")
    parser.add_argument(
        "--interval",
        type=int,
        default=50,
        help="Delay between frames in ms",
    )
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="If provided, save the animation to this file instead of showing it",
    )
    return parser


def main(args: Sequence[str] | None = None) -> None:
    parser = build_arg_parser()
    parsed = parser.parse_args(args)
    dipole_specs = parsed.dipole or ["0,0,1,0"]
    dipoles = [parse_dipole(spec, default_color=f"C{i}") for i, spec in enumerate(dipole_specs)]
    sim = DipoleSimulation(
        dipoles=dipoles,
        grid_limit=parsed.grid_limit,
        grid_size=parsed.grid_size,
    )
    sim.animate(
        frames=parsed.frames,
        rotation_speed=parsed.rotation_speed,
        interval=parsed.interval,
        save=parsed.save,
    )


if __name__ == "__main__":
    main()
