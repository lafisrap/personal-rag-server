#!/usr/bin/env python3
"""
Tests for the template processor module.
"""

import os
import sys
import pytest
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import from the new structure
from assistants.template_processor import TemplateProcessor

# Define test templates directory
TEST_TEMPLATES_DIR = os.path.join(
    Path(__file__).parent.parent.parent, 
    "assistants", "templates"
)

@pytest.fixture
def template_processor():
    """Create a template processor for testing."""
    return TemplateProcessor(template_dir=TEST_TEMPLATES_DIR)

def test_load_templates(template_processor):
    """Test loading templates."""
    # This will implicitly test _load_templates through the fixture
    assert template_processor is not None
    assert template_processor.env is not None

def test_get_template(template_processor):
    """Test getting a template by name."""
    template = template_processor.get_template("gedankenfehler-formulieren")
    assert template is not None
    
    # Test getting a non-existent template
    template = template_processor.get_template("non-existent-template")
    assert template is None

def test_render_gedankenfehler_template(template_processor):
    """Test rendering the gedankenfehler-formulieren template."""
    worldview = "Idealismus"
    gedanke = "Der Mensch ist nur ein komplexer biologischer Mechanismus ohne geistige Dimension."
    aspekte = "Betrachte das Verhältnis von Geist und Körper."
    
    rendered = template_processor.process_gedankenfehler_template(
        worldview=worldview,
        gedanke_in_weltanschauung=gedanke,
        aspekte=aspekte
    )
    
    assert rendered is not None
    assert gedanke in rendered
    assert worldview in rendered
    assert aspekte in rendered

def test_render_glossar_template(template_processor):
    """Test rendering the gedankenfehler-glossar template."""
    worldview = "Materialismus"
    korrektur = "Das Bewusstsein ist ein Produkt neuronaler Prozesse im Gehirn."
    
    rendered = template_processor.process_glossar_template(
        worldview=worldview,
        korrektur=korrektur
    )
    
    assert rendered is not None
    assert korrektur in rendered
    assert worldview in rendered

def test_render_wiederholen_template(template_processor):
    """Test rendering the gedankenfehler-wiederholen template."""
    worldview = "Spiritualismus"
    gedanke = "Der Mensch ist ein geistiges Wesen mit einem physischen Körper."
    stichwort = "Seele, Entwicklung, Inkarnation"
    
    rendered = template_processor.process_wiederholen_template(
        worldview=worldview,
        gedanke=gedanke,
        stichwort=stichwort
    )
    
    assert rendered is not None
    assert gedanke in rendered
    assert worldview in rendered
    assert stichwort in rendered

def test_parse_template_response(template_processor):
    """Test parsing a template response."""
    response = """
    Some text before the JSON.
    
    {
        "gedanke": "This is a test gedanke.",
        "gedanke_zusammenfassung": "This is a summary.",
        "gedanke_kind": "This is for children."
    }
    
    Some text after the JSON.
    """
    
    parsed = template_processor.parse_template_response(response)
    
    assert parsed is not None
    assert isinstance(parsed, dict)
    assert "gedanke" in parsed
    assert parsed["gedanke"] == "This is a test gedanke."
    assert parsed["gedanke_zusammenfassung"] == "This is a summary."
    assert parsed["gedanke_kind"] == "This is for children."

def test_parse_template_response_error(template_processor):
    """Test parsing an invalid template response."""
    response = """
    Some text without valid JSON.
    """
    
    with pytest.raises(ValueError):
        template_processor.parse_template_response(response)

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 