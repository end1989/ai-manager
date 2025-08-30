"""Basic tests for AI Manager functionality."""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_package_imports():
    """Test that core packages can be imported."""
    import manager
    from manager.config import settings
    from manager.core.schemas import TaskSpec
    
    assert manager is not None
    assert settings is not None
    assert TaskSpec is not None


def test_task_spec_creation():
    """Test TaskSpec can be created."""
    from manager.core.schemas import TaskSpec
    
    task = TaskSpec(
        task_id="test-001",
        title="Test Task",
        goal="Test goal",
        background="Test background",
        inputs={},
        deliverables=[],
        acceptance_criteria=[],
        definition_of_done=[],
        risk_checks=[],
        run_instructions={},
        timebox_hours=1.0
    )
    
    assert task.task_id == "test-001"
    assert task.title == "Test Task"
    assert task.timebox_hours == 1.0


def test_settings_loading():
    """Test that settings can be loaded."""
    from manager.config import settings
    
    assert hasattr(settings, 'environment')
    assert isinstance(settings.environment, str)


if __name__ == "__main__":
    pytest.main([__file__])