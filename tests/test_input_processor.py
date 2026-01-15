import pytest
from app.services.input_processor import AddressInputProcessor

@pytest.fixture
def processor():
    return AddressInputProcessor()

class TestSanitization:
    def test_basic_trim(self, processor):
        result = processor.process("  123 Main St  ")
        assert result.sanitized_input == "123 Main St"

    def test_unicode_normalization(self, processor):
        # Full-width characters (e.g. １２３ Ｍａｉｎ Ｓｔ) should become ASCII
        input_str = "\uff11\uff12\uff13\u0020\uff2d\uff41\uff49\uff4e\u0020\uff33\uff54"
        result = processor.process(input_str)
        assert result.sanitized_input == "123 Main St"

    def test_strip_control_characters(self, processor):
        # Tabs and newlines should be removed/stripped or handled
        # Requirement says "Strip invisible control characters"
        result = processor.process("123\tMain\nSt\0")
        # Depending on implementation, these might be removed or replaced.
        # Ideally normalized to spaces or removed if strictly control codes.
        # Assuming strip removes them or they are normalized out.
        assert "123" in result.sanitized_input
        assert "\t" not in result.sanitized_input
        assert "\n" not in result.sanitized_input
        assert "\0" not in result.sanitized_input

class TestValidation:
    def test_min_length(self, processor):
        result = processor.process("123")
        assert not result.is_valid
        assert "minimum length" in result.error_message.lower()

    def test_max_length(self, processor):
        long_string = "1" * 201
        result = processor.process(long_string)
        assert not result.is_valid
        assert "maximum length" in result.error_message.lower()

    def test_allowed_characters(self, processor):
        # <script> is not allowed
        result = processor.process("123 Main St <script>")
        assert not result.is_valid
        assert "invalid characters" in result.error_message.lower()

    def test_must_contain_digit(self, processor):
        result = processor.process("Main Street")
        assert not result.is_valid
        assert "must contain at least one digit" in result.error_message.lower()

    def test_valid_address(self, processor):
        result = processor.process("123 Main St.")
        assert result.is_valid
        assert result.error_message is None

class TestNormalization:
    def test_lowercase(self, processor):
        result = processor.process("123 MAIN ST")
        assert result.canonical_key == "123 main street"

    def test_remove_punctuation(self, processor):
        result = processor.process("123 Main St., #4")
        # Punctuation removed, abbrev expanded
        assert result.canonical_key == "123 main street 4"

    def test_collapse_spaces(self, processor):
        result = processor.process("123   Main    St")
        assert result.canonical_key == "123 main street"

    def test_abbreviation_expansion(self, processor):
        # st -> street, ave -> avenue, apt -> apartment
        result = processor.process("123 Main St Ave Apt 1")
        assert result.canonical_key == "123 main street avenue apartment 1"

    def test_abbreviation_boundaries(self, processor):
        # Should not expand inside words (e.g., 'star' should not become 'streetar')
        result = processor.process("123 Starburst Lane")
        assert result.canonical_key == "123 starburst lane"

    def test_complex_flow(self, processor):
        # Integration of all steps
        input_str = "  123   Ｍａｉｎ   St.,   #4B  "
        result = processor.process(input_str)
        
        assert result.is_valid
        # Sanitize: NFKC + strip control + trim ends (internal spaces preserved until normalization)
        assert result.sanitized_input == "123   Main   St.,   #4B"
        # Normalize: lower -> remove punct -> collapse space -> expand
        # "123 main st 4b" -> "123 main street 4b"
        assert result.canonical_key == "123 main street 4b"

    def test_leading_zip_code(self, processor):
        # "07055 130 jackson st" -> "130 jackson st 07055"
        input_str = "07055 130 jackson st"
        result = processor.process(input_str)
        
        assert result.is_valid
        # Logic should move zip to end for canonical key AND sanitized input
        assert result.sanitized_input == "130 jackson st 07055"
        assert result.canonical_key == "130 jackson street 07055"

    def test_zip_in_middle(self, processor):
        # "130 07055 jackson st" -> "130 jackson st 07055"
        input_str = "130 07055 jackson st"
        result = processor.process(input_str)
        assert result.sanitized_input == "130 jackson st 07055"

    def test_zip_at_end_stays(self, processor):
        # "130 jackson st 07055" -> "130 jackson st 07055"
        input_str = "130 jackson st 07055"
        result = processor.process(input_str)
        assert result.sanitized_input == "130 jackson st 07055"

    def test_house_number_vs_zip(self, processor):
        # "12345 Main St" -> Should treat 12345 as house number, not zip (no move)
        input_str = "12345 Main St"
        result = processor.process(input_str)
        assert result.sanitized_input == "12345 Main St"

    def test_leading_zip_with_house_number(self, processor):
        # "90210 123 Main St" -> Move 90210 to end
        input_str = "90210 123 Main St"
        result = processor.process(input_str)
        assert result.sanitized_input == "123 Main St 90210"

    def test_two_five_digit_numbers(self, processor):
        # "12345 Main St 54321" -> Assume last is zip, first is house. No change.
        input_str = "12345 Main St 54321"
        result = processor.process(input_str)
        assert result.sanitized_input == "12345 Main St 54321"
