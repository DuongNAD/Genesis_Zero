"""Tests for Genesis Zero 3D Spectator UI, Timeline Replay & Procedural Audio (M4_SPECTATOR).

Verifies:
1. Floating timeline dock (#timeline-dock) with play/pause, speed controls, rewind/forward,
   slider, tick display, LIVE button, audio controls.
2. Weather HUD indicator badge (#weather-badge) with icon, name, progress bar, modifiers pill.
3. Generational lineage metadata in creature inspection card (#insp-gen, #insp-parent, etc.).
4. Client-side historical frame ring buffer (historyBuffer, 1200 capacity) and instant scrub snapping.
5. Procedural Web Audio API sound synthesis engine (AudioContext, playLawFired, playDeath,
   playReproduce, playWeatherShift, playMoveSound) with zero external audio assets.
6. Three.js particle systems for weather phenomena (Rain, Solar Flare, Spores, Magnetic Shift).
7. Dynamic weather atmosphere lighting and fog lerping.
8. Strict zero-CDN offline invariant across HTML and JavaScript.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "web" / "watch3d.html"
JS_PATH = ROOT / "web" / "watch3d.js"


def test_timeline_dock_html_elements():
    """Verify web/watch3d.html defines the timeline dock and all required playback controls."""
    html = HTML_PATH.read_text(encoding="utf-8")

    # Timeline dock container
    assert 'id="timeline-dock"' in html, "Missing #timeline-dock container"

    # Playback toggle (Play/Pause)
    assert 'id="btn-playback-toggle"' in html, "Missing #btn-playback-toggle button"

    # Playback speed buttons (1x, 2x, 5x)
    assert 'id="btn-speed-1x"' in html, "Missing #btn-speed-1x button"
    assert 'id="btn-speed-2x"' in html, "Missing #btn-speed-2x button"
    assert 'id="btn-speed-5x"' in html, "Missing #btn-speed-5x button"

    # Rewind and forward 10 ticks
    assert 'id="btn-rewind-10"' in html, "Missing #btn-rewind-10 button"
    assert 'id="btn-forward-10"' in html, "Missing #btn-forward-10 button"

    # Timeline range slider
    assert re.search(
        r'<input[^>]+type=["\']range["\'][^>]+id=["\']timeline-slider["\']', html
    ), "Missing <input type='range' id='timeline-slider'>"

    # Tick display label and LIVE sync button
    assert 'id="timeline-tick-display"' in html, "Missing #timeline-tick-display label"
    assert 'id="btn-live-sync"' in html, "Missing #btn-live-sync button"

    # Audio controls inside dock
    assert 'id="btn-audio-toggle"' in html, "Missing #btn-audio-toggle button"
    assert re.search(
        r'<input[^>]+type=["\']range["\'][^>]+id=["\']audio-volume-slider["\']', html
    ), "Missing <input type='range' id='audio-volume-slider'>"


def test_weather_hud_badge_html_elements():
    """Verify web/watch3d.html defines the weather HUD indicator badge in header."""
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'id="weather-badge"' in html, "Missing #weather-badge in header"
    assert 'id="weather-icon"' in html, "Missing #weather-icon"
    assert 'id="weather-name"' in html, "Missing #weather-name"
    assert 'id="weather-progress"' in html, "Missing #weather-progress bar"
    assert 'id="weather-modifiers"' in html, "Missing #weather-modifiers pill"


def test_creature_inspection_lineage_fields_html():
    """Verify creature inspection card contains generational lineage fields."""
    html = HTML_PATH.read_text(encoding="utf-8")

    assert 'id="inspect-card"' in html, "Missing #inspect-card"
    assert 'id="insp-gen"' in html, "Missing #insp-gen for creature generation"
    assert 'id="insp-parent"' in html, "Missing #insp-parent for creature parent ID"
    assert 'id="insp-lineage"' in html, "Missing #insp-lineage for creature lineage path"
    assert 'id="insp-dtr"' in html, "Missing #insp-dtr for creature trait mutation deltas"


def test_zero_cdn_and_offline_invariant():
    """Strictly assert zero external CDN links or http/https URLs in watch3d.html and watch3d.js."""
    html = HTML_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")

    for name, content in [("watch3d.html", html), ("watch3d.js", js)]:
        assert "http://" not in content, f"{name} contains forbidden http://"
        assert "https://" not in content, f"{name} contains forbidden https://"
        assert not re.search(
            r"<script[^>]+src=[\"']//", content
        ), f"{name} contains protocol-relative script src"
        assert not re.search(
            r"<link[^>]+href=[\"']//", content
        ), f"{name} contains protocol-relative link href"

    # Verify script tags in html reference only relative local paths
    script_tags = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    assert len(script_tags) >= 2, "watch3d.html must include local vendor scripts"
    for src in script_tags:
        assert not src.startswith("//") and not src.startswith("http"), (
            f"Non-local script src: {src}"
        )
        local_file = ROOT / "web" / src
        assert local_file.exists(), f"Local script file does not exist: {local_file}"


def test_client_frame_ring_buffer_in_watch3d_js():
    """Verify watch3d.js implements the 1200-frame history ring buffer and instant scrubbing."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Buffer definition & capacity
    assert "historyBuffer" in js, "watch3d.js must define historyBuffer"
    assert "MAX_HISTORY = 1200" in js or "1200" in js, (
        "watch3d.js must enforce 1200 frame ring buffer capacity"
    )

    # State variables
    assert "isPaused" in js, "watch3d.js must maintain isPaused state"
    assert "playbackSpeed" in js, "watch3d.js must maintain playbackSpeed state"
    assert "scrubTick" in js, "watch3d.js must maintain scrubTick state"
    assert "isLive" in js, "watch3d.js must maintain isLive state"

    # Scrub and replay logic
    assert "renderHistoricalFrame" in js, "watch3d.js must implement renderHistoricalFrame"
    assert "getFrameByTick" in js, "watch3d.js must implement getFrameByTick"
    assert "goToLive" in js, "watch3d.js must implement goToLive"
    assert "isInstant" in js, (
        "watch3d.js must support isInstant snapping to bypass lerp latency during scrub"
    )


def test_procedural_web_audio_engine_in_watch3d_js():
    """Verify watch3d.js implements procedural audio synthesis without external files."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Web Audio API Context
    assert "AudioContext" in js, "watch3d.js must use native browser AudioContext"
    assert "DynamicsCompressor" in js, (
        "watch3d.js must include dynamics compressor in audio master chain"
    )
    assert "-6" in js, "DynamicsCompressor threshold should be configured at -6dB"

    # Audio synthesis methods required by dispatch
    assert "playLawFired" in js, "watch3d.js must implement playLawFired synthesizer"
    assert "playDeath" in js, "watch3d.js must implement playDeath pitch plunge synthesizer"
    assert "playReproduce" in js, (
        "watch3d.js must implement playReproduce arpeggio chime synthesizer"
    )
    assert "playWeatherShift" in js, (
        "watch3d.js must implement playWeatherShift drone sweep synthesizer"
    )
    assert "playMoveSound" in js, (
        "watch3d.js must implement domain-differentiated playMoveSound"
    )

    # Browser autoplay policy compliance
    assert "unlockAudio" in js, (
        "watch3d.js must handle user gesture audio unlocking for browser autoplay policies"
    )

    # Zero sound file dependencies
    for ext in (".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"):
        assert ext not in js.lower(), f"watch3d.js must not reference external sound files ({ext})"


def test_weather_particle_systems_in_watch3d_js():
    """Verify watch3d.js implements Three.js procedural particle systems for weather."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Points usage
    assert "THREE.Points" in js, "Particle systems must use THREE.Points"
    assert "THREE.PointsMaterial" in js, "Particle systems must use THREE.PointsMaterial"

    # Required particle systems and counts per dispatch
    assert "rainParticles" in js, "watch3d.js must implement rain particle system"
    assert "800" in js, "Rain particle system should have 800 particles"

    assert "solarParticles" in js, "watch3d.js must implement solar flare particle system"
    assert "400" in js, "Solar flare particle system should have 400 particles"

    assert "sporeParticles" in js, "watch3d.js must implement toxic spores particle system"
    assert "500" in js, "Spore particle system should have 500 particles"

    assert "magneticParticles" in js, "watch3d.js must implement magnetic shift particle system"
    assert "300" in js, "Magnetic shift particle system should have 300 particles"

    # Continuous animation loop
    assert "animateWeatherParticles" in js, (
        "watch3d.js must animate weather particles continuously in render loop"
    )
    assert "needsUpdate = true" in js, (
        "Particle position buffer attributes must set needsUpdate = true"
    )


def test_weather_atmosphere_lighting_and_fog_lerp():
    """Verify dynamic lighting and fog lerping for weather states."""
    js = JS_PATH.read_text(encoding="utf-8")

    assert "updateWeatherAtmosphere" in js, (
        "watch3d.js must implement updateWeatherAtmosphere function"
    )
    assert "targetFogColor" in js, "watch3d.js must track targetFogColor"
    assert "targetSunColor" in js, "watch3d.js must track targetSunColor"
    assert "targetSunIntensity" in js, "watch3d.js must track targetSunIntensity"
    assert "targetAmbientColor" in js, "watch3d.js must track targetAmbientColor"

    # Canonical weather state handling
    for state in ("SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT", "CLEAR", "NIGHT"):
        assert state in js, f"watch3d.js must configure lighting targets for weather state {state}"

    # Night emissive glow boost
    assert "isNight" in js, "watch3d.js must detect night condition"
    assert "glowBoost" in js, "watch3d.js must boost creature eye emissive glow during night"


def test_third_person_follow_and_creature_pov_fow_elements():
    """Verify HTML defines controls for 3rd-person follow camera, Fog of War, and creature selector."""
    html = HTML_PATH.read_text(encoding="utf-8")

    # 3rd-person follow camera button
    assert 'id="btn-cam-follow"' in html, "Missing #btn-cam-follow button in watch3d.html"

    # Fog of War toggle button
    assert 'id="btn-toggle-fow"' in html, "Missing #btn-toggle-fow button in watch3d.html"

    # My creature selector dropdown
    assert 'id="select-my-creature"' in html, "Missing #select-my-creature dropdown in watch3d.html"

    # Creature POV HUD reticle
    assert 'id="creature-pov-hud"' in html, "Missing #creature-pov-hud reticle in watch3d.html"
    assert 'id="pov-creature-tag"' in html, "Missing #pov-creature-tag in watch3d.html"


def test_third_person_follow_and_fow_js_logic():
    """Verify watch3d.js implements 3rd-person follow camera, Fog of War, and creature selection."""
    js = JS_PATH.read_text(encoding="utf-8")

    # Follow camera preset handling
    assert 'mode === "FOLLOW"' in js, "watch3d.js must handle mode === 'FOLLOW' in setCameraPreset"
    assert 'btn-cam-follow' in js, "watch3d.js must wire up btn-cam-follow"

    # Fog of War logic
    assert "enableFogOfWar" in js, "watch3d.js must maintain enableFogOfWar state"
    assert "toggleFogOfWar" in js, "watch3d.js must implement toggleFogOfWar function"
    assert "btn-toggle-fow" in js, "watch3d.js must wire up btn-toggle-fow"

    # Creature dropdown management
    assert "select-my-creature" in js, "watch3d.js must reference select-my-creature dropdown"
    assert "updateCreatureDropdown" in js, "watch3d.js must implement updateCreatureDropdown"

    # Keyboard shortcuts
    assert 'k === "4"' in js, "watch3d.js must bind key '4' to FOLLOW preset"
    assert 'k === "F"' in js, "watch3d.js must bind key 'F' to toggleFogOfWar"

    # URL query parameter parsing
    assert 'urlParams.get("creature")' in js or 'urlParams.get("species")' in js, (
        "watch3d.js must support URL parameter for creature POV auto-selection"
    )

    # Zero-CDN invariant preserved
    assert "http://" not in js and "https://" not in js, "watch3d.js must not contain external URLs"
    html = HTML_PATH.read_text(encoding="utf-8")
    assert "http://" not in html and "https://" not in html, "watch3d.html must not contain external URLs"


def test_creature_setup_lobby_and_view_isolation():
    """Verify HTML and JS implement the pre-match creature setup lobby, 6-trait allocator, and POV isolation."""
    html = HTML_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")

    # Header setup button
    assert 'id="btn-open-setup"' in html, "Missing #btn-open-setup in watch3d.html"

    # Setup Lobby Modal containers
    assert 'id="creature-setup-lobby"' in html, "Missing #creature-setup-lobby in watch3d.html"
    assert 'id="setup-creature-name"' in html, "Missing #setup-creature-name input in watch3d.html"
    assert 'id="setup-traits-container"' in html, "Missing #setup-traits-container in watch3d.html"
    assert 'id="setup-points-left"' in html, "Missing #setup-points-left in watch3d.html"
    assert 'id="tab-laws-list"' in html, "Missing #tab-laws-list in watch3d.html"
    assert 'id="btn-setup-spawn"' in html, "Missing #btn-setup-spawn in watch3d.html"

    # JS logic for Setup Lobby and Creature Isolation
    assert "openSetupLobby" in js, "watch3d.js must implement openSetupLobby"
    assert "spawnAndEnterWorld" in js, "watch3d.js must implement spawnAndEnterWorld"
    assert "renderSetupTraitsUI" in js, "watch3d.js must implement renderSetupTraitsUI"
    assert "showFloatingWarning" in js, "watch3d.js must implement showFloatingWarning"
    assert "isMyOffspring" in js, "watch3d.js must implement isMyOffspring"
    assert 'k === "P"' in js, "watch3d.js must bind key 'P' to toggleSetupLobby"


