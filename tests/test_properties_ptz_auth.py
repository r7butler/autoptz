"""PTZ credentials load and persist independently of video credentials."""

import json

from PySide6.QtWidgets import QLineEdit

from autoptz.config.store import ConfigStore
from autoptz.ui.engine_client import EngineClient
from autoptz.ui.frames import ShmFrameSource
from autoptz.ui.widgets.properties_panel import PropertiesPanel


def test_ptz_credentials_load_and_save(qapp, tmp_path):
    client = EngineClient(store=ConfigStore(db_path=tmp_path / "cfg.db", debounce_s=0))
    cid = client.addCamera("usb://0", "Cam")
    cfg = client.getCameraConfig(cid)
    cfg["ptz"].update(username="operator", password=" original secret ")
    cfg["source"].update(username="video-user", password="video-secret")
    client.updateCameraConfig(cid, json.dumps(cfg))
    panel = PropertiesPanel(client, frame_source=ShmFrameSource())
    try:
        panel.set_camera(cid)
        assert panel._ptz_username.text() == "operator"
        assert panel._ptz_password.text() == " original secret "
        assert panel._ptz_password.echoMode() == QLineEdit.EchoMode.Password
        for widget, value in (
            (panel._ptz_username, " new-user "),
            (panel._ptz_password, " new secret "),
        ):
            panel._push_timer.stop()
            widget.setText(value)
            widget.editingFinished.emit()
            assert panel._push_timer.isActive()
        panel._push_timer.stop()
        panel._push()
        saved = client.getCameraConfig(cid)
        assert saved["ptz"]["username"] == "new-user"
        assert saved["ptz"]["password"] == " new secret "
        assert saved["source"]["username"] == "video-user"
        assert saved["source"]["password"] == "video-secret"
    finally:
        panel.deleteLater()
