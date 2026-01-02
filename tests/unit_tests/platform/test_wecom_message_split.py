"""
Unit tests for WeChat Work message splitting functionality.

Tests the split_message_by_bytes method to ensure messages exceeding
the 2048-byte limit are properly split without breaking multi-byte characters.
"""

import pytest
from langbot.libs.wecom_api.api import WecomClient


class TestWecomMessageSplit:
    """Tests for WeChat Work message splitting."""

    def test_short_message_no_split(self):
        """Test that short messages are not split."""
        short_msg = "Hello, World!"
        result = WecomClient.split_message_by_bytes(short_msg, 2048)
        assert len(result) == 1
        assert result[0] == short_msg

    def test_empty_message(self):
        """Test that empty messages return empty list."""
        empty_msg = ""
        result = WecomClient.split_message_by_bytes(empty_msg, 2048)
        assert len(result) == 0

    def test_exact_limit_ascii(self):
        """Test message exactly at the byte limit with ASCII characters."""
        exact_msg = "A" * 2048
        result = WecomClient.split_message_by_bytes(exact_msg, 2048)
        assert len(result) == 1
        assert result[0] == exact_msg
        assert len(result[0].encode('utf-8')) == 2048

    def test_over_limit_ascii(self):
        """Test message slightly over the limit with ASCII characters."""
        over_msg = "A" * 2049
        result = WecomClient.split_message_by_bytes(over_msg, 2048)
        assert len(result) == 2
        assert len(result[0].encode('utf-8')) <= 2048
        assert len(result[1].encode('utf-8')) <= 2048
        assert result[0] + result[1] == over_msg

    def test_chinese_characters(self):
        """Test message with Chinese characters (3 bytes each in UTF-8)."""
        # 682 Chinese characters = 2046 bytes, 683 = 2049 bytes
        chinese_msg = "中" * 683
        result = WecomClient.split_message_by_bytes(chinese_msg, 2048)
        assert len(result) == 2
        for chunk in result:
            chunk_bytes = chunk.encode('utf-8')
            assert len(chunk_bytes) <= 2048
        assert ''.join(result) == chinese_msg

    def test_mixed_ascii_and_chinese(self):
        """Test message with mixed ASCII and Chinese characters."""
        mixed_msg = "Hello世界" * 200  # Mix of ASCII (1 byte) and Chinese (3 bytes each)
        result = WecomClient.split_message_by_bytes(mixed_msg, 2048)
        total_bytes = len(mixed_msg.encode('utf-8'))

        # Verify all chunks are within byte limit
        for chunk in result:
            chunk_bytes = chunk.encode('utf-8')
            assert len(chunk_bytes) <= 2048

        # Verify original message can be reconstructed
        assert ''.join(result) == mixed_msg

        # Verify we have the expected number of chunks
        expected_chunks = (total_bytes + 2047) // 2048
        assert len(result) == expected_chunks

    def test_very_long_message(self):
        """Test very long message (10000 characters)."""
        long_msg = "这是一条很长的消息。" * 1000
        result = WecomClient.split_message_by_bytes(long_msg, 2048)
        total_bytes = len(long_msg.encode('utf-8'))
        expected_chunks = (total_bytes + 2047) // 2048

        assert len(result) == expected_chunks

        # Verify all chunks are within byte limit
        for chunk in result:
            chunk_bytes = chunk.encode('utf-8')
            assert len(chunk_bytes) <= 2048

        # Verify original message can be reconstructed
        assert ''.join(result) == long_msg

    def test_emoji_characters(self):
        """Test message with emoji characters (4 bytes each)."""
        emoji_msg = "🎉" * 512 + "🎊" * 1  # 512*4 + 4 = 2052 bytes
        result = WecomClient.split_message_by_bytes(emoji_msg, 2048)
        assert len(result) == 2

        # Verify all chunks are within byte limit
        for chunk in result:
            chunk_bytes = chunk.encode('utf-8')
            assert len(chunk_bytes) <= 2048

        # Verify original message can be reconstructed
        assert ''.join(result) == emoji_msg

    def test_custom_byte_limit(self):
        """Test with a custom byte limit."""
        msg = "A" * 100
        result = WecomClient.split_message_by_bytes(msg, 50)
        assert len(result) == 2
        assert len(result[0].encode('utf-8')) == 50
        assert len(result[1].encode('utf-8')) == 50
        assert result[0] + result[1] == msg

    def test_single_multibyte_char_exceeds_limit(self):
        """Test when a single character exceeds the limit."""
        # Create a scenario where we set a very small limit
        msg = "中文"  # Each character is 3 bytes
        result = WecomClient.split_message_by_bytes(msg, 3)
        # Should split into two chunks, one char each
        assert len(result) == 2
        assert result[0] == "中"
        assert result[1] == "文"

    def test_newlines_preserved(self):
        """Test that newlines are preserved in the split."""
        msg = "Line1\nLine2\n" * 200
        result = WecomClient.split_message_by_bytes(msg, 2048)

        # Verify all chunks are within byte limit
        for chunk in result:
            chunk_bytes = chunk.encode('utf-8')
            assert len(chunk_bytes) <= 2048

        # Verify original message can be reconstructed with newlines intact
        assert ''.join(result) == msg
