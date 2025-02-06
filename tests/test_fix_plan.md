1. **Current Test Failures Analysis**:
   ```
   - test_end_to_end_workflow: ERROR (qtbot fixture not found)
   - test_performance_preview_generation: PASSED
   - test_memory_usage: PASSED
   - test_bookmark_detection_performance: PASSED
   - test_concurrent_operations: ERROR (qtbot fixture not found)
   - test_memory_pressure_handling: PASSED
   ```

2. **Root Cause Analysis**:
   - Primary Issue: Qt testing infrastructure not properly set up
   - Secondary Issues:
     - Tests are mixing UI testing with business logic testing
     - Tests are trying to verify third-party behavior (PyMuPDF, Qt)
     - Performance/memory tests are environment-dependent
     - End-to-end tests are too broad in scope

3. **Task Plan**:

   Phase 1: Test Infrastructure
   - [ ] Fix Qt testing setup (pytest-qt integration)
   - [ ] Establish proper test isolation
   - [ ] Set up consistent mocking strategy

   Phase 2: Test Refactoring
   - [ ] Split end-to-end test into focused component tests
   - [ ] Move performance tests to separate benchmark suite
   - [ ] Refactor UI tests to focus on state changes, not implementation

   Phase 3: Test Implementation
   - [ ] Implement component integration tests
   - [ ] Implement UI state tests
   - [ ] Implement error handling tests

4. **Detailed Changes Required**:

   a. **End-to-end workflow test**:
      - Current: Tests entire UI workflow with file operations
      - Change to: Test state transitions and component integration
      ```python
      def test_pdf_loading_integration():
          """Test PDF loading and component initialization."""
          
      def test_preview_cache_integration():
          """Test preview generation and cache interaction."""
          
      def test_bookmark_integration():
          """Test bookmark detection and range management."""
      ```

   b. **Performance tests**:
      - Move to separate file: `benchmarks/test_performance.py`
      - Add configuration for thresholds
      - Focus on relative performance, not absolute timings

   c. **UI tests**:
      - Focus on state changes and user feedback
      - Mock PDF operations
      - Test error handling paths

5. **Implementation Strategy**:

   1. First PR: Infrastructure Setup
      ```python
      # conftest.py
      import pytest
      from PyQt6.QtWidgets import QApplication
      
      @pytest.fixture(scope="session")
      def qapp():
          """Create QApplication instance."""
          app = QApplication.instance()
          if app is None:
              app = QApplication([])
          return app
      
      @pytest.fixture
      def mock_pdf():
          """Create mock PDF document."""
      ```

   2. Second PR: Component Tests
      ```python
      # test_integration.py
      def test_pdf_loading_integration(qapp, mock_pdf):
          """Test PDF loading and initialization."""
          
      def test_preview_cache_integration(qapp, mock_pdf):
          """Test preview generation and caching."""
      ```

   3. Third PR: UI Tests
      ```python
      # test_ui.py
      def test_ui_state_changes(qapp, mock_pdf):
          """Test UI state transitions."""
          
      def test_error_handling(qapp, mock_pdf):
          """Test error handling and user feedback."""
      ```

6. **Success Criteria**:
   - Tests focus on our business logic
   - Clear separation of concerns
   - Reliable test execution
   - Meaningful test coverage
   - Easy to maintain and extend
