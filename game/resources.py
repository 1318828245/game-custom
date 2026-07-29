from __future__ import annotations

from pathlib import Path

import pygame


ASSET_ROOT = Path(__file__).resolve().parent.parent / "assets"


class ImageStore:
    def __init__(self) -> None:
        self._images: dict[str, pygame.Surface | None] = {}
        self._scaled_images: dict[tuple[str, tuple[int, int]], pygame.Surface | None] = {}

    def load(self, relative_path: str) -> pygame.Surface | None:
        if relative_path in self._images:
            return self._images[relative_path]

        image_path = ASSET_ROOT / relative_path
        try:
            image = pygame.image.load(image_path).convert_alpha()
        except (FileNotFoundError, pygame.error, OSError):
            image = None

        self._images[relative_path] = image
        return image

    def load_scaled(
        self, relative_path: str, size: tuple[int, int]
    ) -> pygame.Surface | None:
        cache_key = (relative_path, size)
        if cache_key in self._scaled_images:
            return self._scaled_images[cache_key]

        image = self.load(relative_path)
        scaled_image = None
        if image is not None:
            scaled_image = pygame.transform.smoothscale(image, size)

        self._scaled_images[cache_key] = scaled_image
        return scaled_image

    def draw_centered(
        self,
        surface: pygame.Surface,
        relative_path: str,
        center: tuple[int, int],
        size: tuple[int, int] | None = None,
        angle: float = 0.0,
    ) -> bool:
        image = self.load_scaled(relative_path, size) if size is not None else self.load(relative_path)
        if image is None:
            return False

        if angle:
            image = pygame.transform.rotate(image, angle)

        rect = image.get_rect(center=center)
        surface.blit(image, rect)
        return True


images = ImageStore()
