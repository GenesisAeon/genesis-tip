"""GenesisAeon Diamond Interface — canonical runtime contract for UTAC packages.

Γ (Gamma) is an **attractor property**: numeric values are only valid after at
least one completed :meth:`run_cycle`. Before that, :meth:`get_crep_state` and
:meth:`get_utac_state` raise :class:`NotConvergedError`.

Version 2.2.0 adds the optional sixth Diamond method ``get_resilience_state()``
and the :class:`ResilienceState` Pydantic model for Ρ-quantification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field, field_validator


class NotConvergedError(RuntimeError):
    """Raised when CREP/UTAC state is read before the first ``run_cycle()``."""

    def __init__(self, method: str) -> None:
        super().__init__(
            f"{method} requires at least one completed run_cycle() "
            f"(Gamma is an attractor property, not an initial value)."
        )
        self.method = method


# Alias used in GenesisAeon documentation (P40/P41)
NotInitializedError = NotConvergedError


class ResilienceState(BaseModel):
    """Canonical Ρ snapshot returned by ``get_resilience_state()``.

    All fields map directly to the UTAC fixed-point formula::

        Ρ = |λ*| · (1 - Γ/Γ_max) · (1 - Σ|C_ij|/C_critical)
    """

    rho: float | None = Field(default=None, ge=0.0)
    lambda_star: float | None = Field(default=None, ge=0.0)
    recovery_time: float | None = Field(default=None, ge=0.0)
    criticality_margin: float | None = Field(default=None, ge=0.0, le=1.0)
    coupling_load: float | None = Field(default=None, ge=0.0, le=1.0)
    near_collapse: bool | None = Field(default=None)
    implemented: bool = Field(default=True)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class CREPState(BaseModel):
    """Canonical CREP snapshot. Gamma uses geometric mean (any zero → 0)."""

    C: float = Field(ge=0.0, le=1.0)
    R: float = Field(ge=0.0, le=1.0)
    E: float = Field(ge=0.0, le=1.0)
    P: float = Field(ge=0.0, le=1.0)
    Gamma: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Set after convergence; None only before first run_cycle.",
    )

    @field_validator("C", "R", "E", "P", mode="before")
    @classmethod
    def _clamp_unit(cls, value: float) -> float:
        return float(max(0.0, min(1.0, float(value))))

    def model_post_init(self, __context: Any) -> None:
        if self.Gamma is None:
            product = self.C * self.R * self.E * self.P
            object.__setattr__(self, "Gamma", float(product**0.25) if product > 0 else 0.0)

    def as_dict(self) -> dict[str, float | None]:
        return {
            "C": self.C,
            "R": self.R,
            "E": self.E,
            "P": self.P,
            "Gamma": self.Gamma,
        }


class UTACState(BaseModel):
    """Canonical UTAC entropy snapshot."""

    H: float = Field(ge=0.0, le=1.0)
    H_star: float = Field(ge=0.0, le=1.0)
    K_eff: float = Field(gt=0.0)

    def as_dict(self) -> dict[str, float]:
        return {"H": self.H, "H_star": self.H_star, "K_eff": self.K_eff}


class ZenodoCreator(BaseModel):
    name: str
    affiliation: str | None = None


class ZenodoRecord(BaseModel):
    """Minimum Zenodo metadata for Diamond packages."""

    title: str
    description: str
    creators: list[ZenodoCreator] = Field(min_length=1)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "creators": [c.model_dump(exclude_none=True) for c in self.creators],
        }


class DiamondPackage(ABC):
    """Abstract base for GenesisAeon Diamond-interface packages.

    Subclasses implement the four private hooks; the public five-method API
    enforces convergence and return-type contracts.
    """

    def __init__(self) -> None:
        self._cycles_completed: int = 0

    @property
    def cycles_completed(self) -> int:
        return self._cycles_completed

    def run_cycle(self) -> dict[str, Any]:
        """Execute one simulation cycle and mark the package as converged."""
        result = self._run_cycle()
        self._cycles_completed += 1
        return result

    def get_crep_state(self) -> dict[str, float | None]:
        self._require_converged("get_crep_state")
        return self._build_crep_state().as_dict()

    def get_utac_state(self) -> dict[str, float]:
        self._require_converged("get_utac_state")
        return self._build_utac_state().as_dict()

    def get_phase_events(self) -> list[dict[str, Any]]:
        return self._build_phase_events()

    def to_zenodo_record(self) -> dict[str, Any]:
        return self._build_zenodo_record().as_dict()

    def get_resilience_state(self) -> dict[str, Any]:
        """Optional sixth Diamond method — system resilience Ρ.

        Returns a dict compatible with :class:`ResilienceState`.
        The default implementation signals that the method is not implemented;
        packages that depend on ``resilience-core`` should override this.
        """
        return {"rho": None, "implemented": False}

    def _require_converged(self, method: str) -> None:
        if self._cycles_completed < 1:
            raise NotConvergedError(method)

    @abstractmethod
    def _run_cycle(self) -> dict[str, Any]:
        """Subclass: one UTAC/simulation step."""

    @abstractmethod
    def _build_crep_state(self) -> CREPState:
        """Subclass: current CREP (called only after first run_cycle)."""

    @abstractmethod
    def _build_utac_state(self) -> UTACState:
        """Subclass: current UTAC (called only after first run_cycle)."""

    @abstractmethod
    def _build_phase_events(self) -> list[dict[str, Any]]:
        """Subclass: phase transition log."""

    @abstractmethod
    def _build_zenodo_record(self) -> ZenodoRecord:
        """Subclass: Zenodo deposition metadata."""


# Typing.Protocol alias for static checkers / documentation
DiamondProtocol = DiamondPackage
