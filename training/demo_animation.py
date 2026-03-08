"""Render a real-time stellarator optimization animation as MP4.

Usage:
    uv run python training/demo_animation.py --seed 0 --output demo.mp4

The animation shows:
- 3D stellarator boundary morphing as the agent adjusts parameters
- Live metrics overlay (feasibility, score, reward, constraints)
- Step-by-step action labels
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from fusion_lab.llm_agent import action_label
from fusion_lab.models import LowDimBoundaryParams, StellaratorAction
from server.environment import StellaratorEnvironment
from server.physics import build_boundary_from_params

matplotlib.use("Agg")

# Actions that reliably push toward feasibility for demo purposes
DEMO_ACTIONS: list[StellaratorAction] = [
    StellaratorAction(
        intent="run",
        parameter="triangularity_scale",
        direction="increase",
        magnitude="large",
    ),
    StellaratorAction(
        intent="run",
        parameter="rotational_transform",
        direction="increase",
        magnitude="large",
    ),
    StellaratorAction(
        intent="run",
        parameter="elongation",
        direction="decrease",
        magnitude="medium",
    ),
    StellaratorAction(
        intent="run",
        parameter="triangularity_scale",
        direction="increase",
        magnitude="medium",
    ),
    StellaratorAction(
        intent="run",
        parameter="rotational_transform",
        direction="increase",
        magnitude="small",
    ),
    StellaratorAction(intent="submit"),
]

THETA_RES = 60
PHI_RES = 120
INTERP_FRAMES = 15
HOLD_FRAMES = 8


def boundary_xyz(
    params: LowDimBoundaryParams,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    boundary = build_boundary_from_params(params)
    nfp = boundary.n_field_periods
    r_cos = np.array(boundary.r_cos)
    z_sin = np.array(boundary.z_sin)
    m_modes = np.array(boundary.poloidal_modes)
    n_modes = np.array(boundary.toroidal_modes)

    theta = np.linspace(0, 2 * np.pi, THETA_RES)
    phi = np.linspace(0, 2 * np.pi, PHI_RES)
    tg, pg = np.meshgrid(theta, phi, indexing="ij")

    r = np.zeros_like(tg)
    z = np.zeros_like(tg)
    n_pol, n_tor = r_cos.shape
    for i in range(n_pol):
        for j in range(n_tor):
            angle = m_modes[i, j] * tg - n_modes[i, j] * nfp * pg
            r += r_cos[i, j] * np.cos(angle)
            z += z_sin[i, j] * np.sin(angle)

    return r * np.cos(pg), r * np.sin(pg), z


def interpolate_params(
    p1: LowDimBoundaryParams, p2: LowDimBoundaryParams, t: float
) -> LowDimBoundaryParams:
    return LowDimBoundaryParams(
        aspect_ratio=p1.aspect_ratio + (p2.aspect_ratio - p1.aspect_ratio) * t,
        elongation=p1.elongation + (p2.elongation - p1.elongation) * t,
        rotational_transform=p1.rotational_transform
        + (p2.rotational_transform - p1.rotational_transform) * t,
        triangularity_scale=p1.triangularity_scale
        + (p2.triangularity_scale - p1.triangularity_scale) * t,
    )


def run_demo_episode(
    seed: int,
) -> list[tuple[LowDimBoundaryParams, str, dict[str, object]]]:
    """Run demo actions and collect params + metrics at each step."""
    env = StellaratorEnvironment()
    obs = env.reset(seed=seed)
    snapshots: list[tuple[LowDimBoundaryParams, str, dict[str, object]]] = []

    snapshots.append(
        (
            env.state.current_params.model_copy(),
            "Initial Design",
            {
                "reward": 0.0,
                "total_reward": 0.0,
                "feasibility": obs.p1_feasibility,
                "score": obs.p1_score,
                "max_elongation": obs.max_elongation,
                "constraints": obs.constraints_satisfied,
                "step": 0,
            },
        )
    )

    total_reward = 0.0
    for action in DEMO_ACTIONS:
        obs = env.step(action)
        r = float(obs.reward) if obs.reward is not None else 0.0
        total_reward += r
        label = action_label(action)
        snapshots.append(
            (
                env.state.current_params.model_copy(),
                label,
                {
                    "reward": r,
                    "total_reward": total_reward,
                    "feasibility": obs.p1_feasibility,
                    "score": obs.p1_score,
                    "max_elongation": obs.max_elongation,
                    "constraints": obs.constraints_satisfied,
                    "step": len(snapshots),
                },
            )
        )
        if obs.done:
            break

    return snapshots


def build_animation(seed: int, output: Path, fps: int = 20) -> None:
    snapshots = run_demo_episode(seed)

    # Precompute all xyz for interpolation
    all_xyz: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for params, _, _ in snapshots:
        all_xyz.append(boundary_xyz(params))

    # Build frame list: (xyz, label, metrics, azimuth)
    frames: list[tuple[np.ndarray, np.ndarray, np.ndarray, str, dict[str, object]]] = []

    # Initial hold
    x, y, z = all_xyz[0]
    _, label, metrics = snapshots[0]
    for _ in range(HOLD_FRAMES):
        frames.append((x, y, z, label, metrics))

    # Step transitions
    for i in range(1, len(snapshots)):
        p_prev = snapshots[i - 1][0]
        p_next = snapshots[i][0]
        _, label, metrics = snapshots[i]

        for f in range(INTERP_FRAMES):
            t = f / INTERP_FRAMES
            p_interp = interpolate_params(p_prev, p_next, t)
            xi, yi, zi = boundary_xyz(p_interp)
            frames.append((xi, yi, zi, f"→ {label}", metrics))

        x, y, z = all_xyz[i]
        for _ in range(HOLD_FRAMES):
            frames.append((x, y, z, label, metrics))

    # Final extra hold
    for _ in range(HOLD_FRAMES * 3):
        frames.append((x, y, z, label, metrics))

    # Setup figure
    fig = plt.figure(figsize=(12, 8), facecolor="black")
    ax = fig.add_subplot(111, projection="3d", facecolor="black")

    # Style
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_axis_off()
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.8, 1.8)
    ax.set_zlim(-0.7, 0.7)

    fig.text(
        0.5,
        0.95,
        "Fusion Design Lab — Stellarator Optimization",
        ha="center",
        va="top",
        fontsize=18,
        fontweight="bold",
        color="white",
        family="monospace",
    )
    action_text = fig.text(
        0.5,
        0.06,
        "",
        ha="center",
        va="bottom",
        fontsize=14,
        color="#00ff88",
        family="monospace",
    )
    metrics_text = fig.text(
        0.02,
        0.88,
        "",
        ha="left",
        va="top",
        fontsize=11,
        color="white",
        family="monospace",
    )
    reward_text = fig.text(
        0.02,
        0.06,
        "",
        ha="left",
        va="bottom",
        fontsize=11,
        color="#ffaa00",
        family="monospace",
    )

    surface = [
        ax.plot_surface(
            frames[0][0],
            frames[0][1],
            frames[0][2],
            cmap="plasma",
            alpha=0.9,
            edgecolor="none",
            rstride=2,
            cstride=2,
        )
    ]

    def update(frame_idx: int) -> list[object]:
        x, y, z, label, m = frames[frame_idx]

        surface[0].remove()
        surface[0] = ax.plot_surface(
            x, y, z, cmap="plasma", alpha=0.9, edgecolor="none", rstride=2, cstride=2
        )

        azim = 30 + frame_idx * 0.5
        ax.view_init(elev=22, azim=azim)

        action_text.set_text(f"Step {m['step']}: {label}")

        constraint_str = "SATISFIED" if m["constraints"] else "VIOLATED"
        constraint_color = "#00ff88" if m["constraints"] else "#ff4444"
        metrics_text.set_text(
            f"max_elongation: {m['max_elongation']:.4f}\n"
            f"feasibility:    {m['feasibility']:.4f}\n"
            f"score:          {m['score']:.4f}\n"
            f"constraints:    {constraint_str}"
        )
        metrics_text.set_color(constraint_color)

        reward_text.set_text(f"step reward: {m['reward']:+.3f}  |  total: {m['total_reward']:+.3f}")

        return [surface[0], action_text, metrics_text, reward_text]

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=1000 // fps,
        blit=False,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    ani.save(str(output), writer="ffmpeg", fps=fps, dpi=120)
    print(f"Saved {output} ({len(frames)} frames, {len(frames) / fps:.1f}s)")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render stellarator optimization demo")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, default=Path("training/artifacts/demo.mp4"))
    parser.add_argument("--fps", type=int, default=20)
    args = parser.parse_args()
    build_animation(args.seed, args.output, args.fps)


if __name__ == "__main__":
    main()
