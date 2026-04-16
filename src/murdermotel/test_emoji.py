from io import StringIO
from unittest.mock import patch
from bbsengine6 import io
from bbsengine6.io import common


def test_robot_emoji_renders():
    """Test that robot emoji renders correctly in echo output."""
    io.register_emojis({"robot": "\U0001f916"})

    captured = StringIO()
    with patch.object(common, "_current_output_stream", captured):
        io.echo(":robot:")

    output = captured.getvalue()
    assert "🤖" in output, f"Expected 🤖 in output, got: {output!r}"


if __name__ == "__main__":
    test_robot_emoji_renders()
    print("test_robot_emoji_renders passed")
    print("All tests passed!")
