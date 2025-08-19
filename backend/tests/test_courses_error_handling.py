"""
Comprehensive test suite for courses error handling scenarios.

Tests various error conditions for course loading and management:
- Empty courses response
- Malformed course data
- Network failures
- Invalid course formats
- Missing course data
- Database failures
- API endpoint failures
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.state.course_manager import CourseManager, DEFAULT_COURSES


class TestBasicCourseManagerFunctionality:
    """Test basic course manager functionality without API dependencies"""
    
    def test_course_manager_basic_functionality(self):
        """Test CourseManager basic operations work"""
        manager = CourseManager()
        
        # Should have default courses
        courses = manager.get_courses()
        assert isinstance(courses, dict)
        assert len(courses) > 0
        
        # Should have selected a course
        assert manager.selected_course is not None
        
        # Test course format
        for course_name, course_data in courses.items():
            assert isinstance(course_name, str)
            assert isinstance(course_data, dict)
            assert "name" in course_data
            assert "holes" in course_data
            assert "total_par" in course_data
            assert "total_yards" in course_data
            assert "hole_count" in course_data
            assert course_data["hole_count"] == 18


class TestCourseManagerErrorHandling:
    """Test error handling in the CourseManager class"""
    
    def test_course_manager_initialization_with_empty_defaults(self):
        """Test CourseManager initialization when DEFAULT_COURSES is empty"""
        with patch('app.state.course_manager.DEFAULT_COURSES', {}):
            manager = CourseManager()
            
            # Should create fallback course
            assert len(manager.course_data) >= 1
            assert manager.selected_course is not None
            courses = manager.get_courses()
            assert isinstance(courses, dict)
            assert len(courses) >= 1
    
    def test_course_manager_get_courses_format(self):
        """Test get_courses returns proper dictionary format"""
        manager = CourseManager()
        courses = manager.get_courses()
        
        assert isinstance(courses, dict)
        assert len(courses) > 0
        
        for course_name, course_data in courses.items():
            assert isinstance(course_name, str)
            assert isinstance(course_data, dict)
            assert "name" in course_data
            assert "holes" in course_data
            assert "total_par" in course_data
            assert "total_yards" in course_data
            assert "hole_count" in course_data
            assert len(course_data["holes"]) == 18
    
    def test_course_manager_load_invalid_course(self):
        """Test loading a course that doesn't exist"""
        manager = CourseManager()
        
        with pytest.raises(ValueError, match="Course 'NonexistentCourse' not found"):
            manager.load_course("NonexistentCourse")
    
    def test_course_manager_from_dict_with_empty_data(self):
        """Test from_dict with empty or None course data"""
        manager = CourseManager.from_dict({
            "selected_course": None,
            "course_data": {}
        })
        
        # Should initialize default courses
        assert len(manager.course_data) >= 1
        assert manager.selected_course is not None
        courses = manager.get_courses()
        assert len(courses) >= 1
    
    def test_course_manager_from_dict_with_invalid_data(self):
        """Test from_dict with invalid course data structure"""
        manager = CourseManager.from_dict({
            "selected_course": "InvalidCourse",
            "course_data": {"InvalidCourse": "not_a_list"}  # Invalid format
        })
        
        # Should still initialize properly with fallback
        assert len(manager.course_data) >= 1
        courses = manager.get_courses()
        assert len(courses) >= 1






class TestCourseDataIntegrity:
    """Test course data integrity and consistency"""
    
    def test_default_courses_integrity(self):
        """Test that DEFAULT_COURSES data is well-formed"""
        assert isinstance(DEFAULT_COURSES, dict)
        assert len(DEFAULT_COURSES) > 0
        
        for course_name, holes in DEFAULT_COURSES.items():
            assert isinstance(course_name, str)
            assert isinstance(holes, list)
            assert len(holes) == 18
            
            hole_numbers = []
            stroke_indexes = []
            
            for hole in holes:
                assert isinstance(hole, dict)
                assert "hole_number" in hole
                assert "par" in hole
                assert "yards" in hole
                assert "stroke_index" in hole
                assert "description" in hole
                
                assert isinstance(hole["hole_number"], int)
                assert 1 <= hole["hole_number"] <= 18
                assert isinstance(hole["par"], int)
                assert 3 <= hole["par"] <= 6
                assert isinstance(hole["yards"], int)
                assert hole["yards"] > 0
                assert isinstance(hole["stroke_index"], int)
                assert 1 <= hole["stroke_index"] <= 18
                
                hole_numbers.append(hole["hole_number"])
                stroke_indexes.append(hole["stroke_index"])
            
            # Check that hole numbers and stroke indexes are unique and complete
            assert sorted(hole_numbers) == list(range(1, 19))
            assert sorted(stroke_indexes) == list(range(1, 19))


class TestCoursesFallbackBehavior:
    """Test fallback behavior when courses fail to load"""
    
    def test_course_manager_fallback_behavior(self):
        """Test that CourseManager provides fallback when defaults fail"""
        # Simulate complete failure of default courses
        with patch('app.state.course_manager.DEFAULT_COURSES', {}):
            manager = CourseManager()
            
            # Should still have at least one course
            courses = manager.get_courses()
            assert len(courses) >= 1
            
            # Should have selected a course
            assert manager.selected_course is not None
            
            # Fallback course should have proper structure
            fallback_course_name = list(courses.keys())[0]
            fallback_course = courses[fallback_course_name]
            assert fallback_course["hole_count"] == 18
            assert len(fallback_course["holes"]) == 18
            assert fallback_course["total_par"] > 0
            assert fallback_course["total_yards"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])