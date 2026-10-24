"""Exercise the actual Streamlit application without modifying the JSON files."""
from pathlib import Path
import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = Path(__file__).resolve().parents[1] / "src" / "app.py"


@pytest.mark.parametrize("change", ["facts", "goals", "method", "conditions", "knowledge"])
def test_old_result_hidden_when_request_or_kb_changes(change):
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    next(b for b in app.button if b.label == "Giải bài toán").click().run()
    assert not app.exception
    assert app.session_state["last"]["results"]
    if change == "facts":
        app.text_area(key="hyp_text").set_value("S")
    elif change == "goals":
        app.text_area(key="goal_text").set_value("HCl")
    elif change == "method":
        app.radio(key="method").set_value("optimal")
    elif change == "conditions":
        app.checkbox(key="cond_t").set_value(False)
    else:
        app.session_state["kb"].reactions[0].cost += 1
    app.run()
    assert not app.exception
    assert any("đã thay đổi" in w.value for w in app.warning)
    assert not any("Tìm được lời giải" in s.value for s in app.success)
