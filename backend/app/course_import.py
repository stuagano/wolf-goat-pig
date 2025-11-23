"""
Course Data Import Module

This module provides functionality to import real course ratings and slopes
from various external sources including USGA, GHIN, and other golf course databases.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .database import SessionLocal
from .models import Course

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CourseImportData:
    """Data structure for imported course information"""
    name: str
    description: Optional[str] = None
    total_par: int = 72
    total_yards: int = 0
    course_rating: Optional[float] = None
    slope_rating: Optional[float] = None
    holes_data: Optional[List[Dict[str, Any]]] = None
    source: str = "unknown"
    last_updated: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None

class CourseImporter:
    """Main class for importing course data from external sources"""

    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        return {
            "usga_api_key": os.getenv("USGA_API_KEY", ""),
            "ghin_api_key": os.getenv("GHIN_API_KEY", ""),
            "golf_now_api_key": os.getenv("GOLF_NOW_API_KEY", ""),
            "thegrint_api_key": os.getenv("THEGRINT_API_KEY", "")
        }

    async def import_course_by_name(self, course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
        """
        Import course data by name, trying multiple sources
        
        Args:
            course_name: Name of the course to import
            state: State abbreviation (optional, helps with search)
            city: City name (optional, helps with search)
            
        Returns:
            CourseImportData object if found, None otherwise
        """
        logger.info(f"Importing course: {course_name}")

        # Try multiple sources in order of preference
        sources = [
            self._try_usga_search,
            self._try_ghin_search,
            self._try_golf_now_search,
            self._try_thegrint_search
        ]

        for source_func in sources:
            try:
                result = await source_func(course_name, state, city)
                if result:
                    logger.info(f"Successfully imported {course_name} from {result.source}")
                    return result
            except Exception as e:
                logger.warning(f"Failed to import from {source_func.__name__}: {e}")
                continue

        logger.error(f"Failed to import course {course_name} from any source")
        return None

    async def _try_usga_search(self, course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
        """Search USGA course database"""
        if not self.api_keys["usga_api_key"]:
            logger.warning("USGA API key not configured")
            return None

        try:
            # USGA API endpoint (hypothetical - would need real endpoint)
            url = "https://api.usga.org/v1/courses/search"
            params = {
                "name": course_name,
                "api_key": self.api_keys["usga_api_key"]
            }
            if state:
                params["state"] = state
            if city:
                params["city"] = city

            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("courses"):
                course_data = data["courses"][0]  # Take first match
                return self._parse_usga_course(course_data)

        except Exception as e:
            logger.error(f"USGA search failed: {e}")

        return None

    async def _try_ghin_search(self, course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
        """Search GHIN course database"""
        try:
            # GHIN course search endpoint
            url = "https://api2.ghin.com/api/v1/courses/search.json"
            params = {
                "name": course_name,
                "limit": 10
            }
            if state:
                params["state"] = state
            if city:
                params["city"] = city

            response = await self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("courses"):
                course_data = data["courses"][0]  # Take first match
                return self._parse_ghin_course(course_data)

        except Exception as e:
            logger.error(f"GHIN search failed: {e}")

        return None

    async def _try_golf_now_search(self, course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
        """Search GolfNow course database"""
        if not self.api_keys["golf_now_api_key"]:
            logger.warning("GolfNow API key not configured")
            return None

        try:
            # GolfNow API endpoint (hypothetical)
            url = "https://api.golfnow.com/v1/courses/search"
            headers = {
                "Authorization": f"Bearer {self.api_keys['golf_now_api_key']}",
                "Content-Type": "application/json"
            }
            params = {
                "name": course_name,
                "limit": 10
            }
            if state:
                params["state"] = state
            if city:
                params["city"] = city

            response = await self.session.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("courses"):
                course_data = data["courses"][0]
                return self._parse_golf_now_course(course_data)

        except Exception as e:
            logger.error(f"GolfNow search failed: {e}")

        return None

    async def _try_thegrint_search(self, course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
        """Search TheGrint course database"""
        if not self.api_keys["thegrint_api_key"]:
            logger.warning("TheGrint API key not configured")
            return None

        try:
            # TheGrint API endpoint (hypothetical)
            url = "https://api.thegrint.com/v1/courses/search"
            headers = {
                "Authorization": f"Bearer {self.api_keys['thegrint_api_key']}",
                "Content-Type": "application/json"
            }
            params = {
                "name": course_name,
                "limit": 10
            }
            if state:
                params["state"] = state
            if city:
                params["city"] = city

            response = await self.session.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("courses"):
                course_data = data["courses"][0]
                return self._parse_thegrint_course(course_data)

        except Exception as e:
            logger.error(f"TheGrint search failed: {e}")

        return None

    def _parse_usga_course(self, course_data: Dict[str, Any]) -> CourseImportData:
        """Parse USGA course data format"""
        holes_data = []
        total_yards = 0

        # Parse holes data
        for hole in course_data.get("holes", []):
            hole_info = {
                "hole_number": hole.get("hole_number"),
                "par": hole.get("par"),
                "yards": hole.get("yards"),
                "handicap": hole.get("stroke_index"),
                "description": hole.get("description", ""),
                "tee_box": "regular"
            }
            holes_data.append(hole_info)
            total_yards += hole.get("yards", 0)

        return CourseImportData(
            name=course_data.get("name", "Unknown Course"),
            description=course_data.get("description"),
            total_par=course_data.get("total_par", 72),
            total_yards=total_yards,
            course_rating=course_data.get("course_rating"),
            slope_rating=course_data.get("slope_rating"),
            holes_data=holes_data,
            source="USGA",
            last_updated=course_data.get("last_updated"),
            location=course_data.get("location"),
            website=course_data.get("website"),
            phone=course_data.get("phone")
        )

    def _parse_ghin_course(self, course_data: Dict[str, Any]) -> CourseImportData:
        """Parse GHIN course data format"""
        holes_data = []
        total_yards = 0

        # Parse holes data
        for hole in course_data.get("holes", []):
            hole_info = {
                "hole_number": hole.get("hole_number"),
                "par": hole.get("par"),
                "yards": hole.get("yards"),
                "handicap": hole.get("stroke_index"),
                "description": hole.get("description", ""),
                "tee_box": "regular"
            }
            holes_data.append(hole_info)
            total_yards += hole.get("yards", 0)

        return CourseImportData(
            name=course_data.get("name", "Unknown Course"),
            description=course_data.get("description"),
            total_par=course_data.get("total_par", 72),
            total_yards=total_yards,
            course_rating=course_data.get("course_rating"),
            slope_rating=course_data.get("slope_rating"),
            holes_data=holes_data,
            source="GHIN",
            last_updated=course_data.get("last_updated"),
            location=course_data.get("location"),
            website=course_data.get("website"),
            phone=course_data.get("phone")
        )

    def _parse_golf_now_course(self, course_data: Dict[str, Any]) -> CourseImportData:
        """Parse GolfNow course data format"""
        holes_data = []
        total_yards = 0

        # Parse holes data
        for hole in course_data.get("holes", []):
            hole_info = {
                "hole_number": hole.get("hole_number"),
                "par": hole.get("par"),
                "yards": hole.get("yards"),
                "handicap": hole.get("stroke_index"),
                "description": hole.get("description", ""),
                "tee_box": "regular"
            }
            holes_data.append(hole_info)
            total_yards += hole.get("yards", 0)

        return CourseImportData(
            name=course_data.get("name", "Unknown Course"),
            description=course_data.get("description"),
            total_par=course_data.get("total_par", 72),
            total_yards=total_yards,
            course_rating=course_data.get("course_rating"),
            slope_rating=course_data.get("slope_rating"),
            holes_data=holes_data,
            source="GolfNow",
            last_updated=course_data.get("last_updated"),
            location=course_data.get("location"),
            website=course_data.get("website"),
            phone=course_data.get("phone")
        )

    def _parse_thegrint_course(self, course_data: Dict[str, Any]) -> CourseImportData:
        """Parse TheGrint course data format"""
        holes_data = []
        total_yards = 0

        # Parse holes data
        for hole in course_data.get("holes", []):
            hole_info = {
                "hole_number": hole.get("hole_number"),
                "par": hole.get("par"),
                "yards": hole.get("yards"),
                "handicap": hole.get("stroke_index"),
                "description": hole.get("description", ""),
                "tee_box": "regular"
            }
            holes_data.append(hole_info)
            total_yards += hole.get("yards", 0)

        return CourseImportData(
            name=course_data.get("name", "Unknown Course"),
            description=course_data.get("description"),
            total_par=course_data.get("total_par", 72),
            total_yards=total_yards,
            course_rating=course_data.get("course_rating"),
            slope_rating=course_data.get("slope_rating"),
            holes_data=holes_data,
            source="TheGrint",
            last_updated=course_data.get("last_updated"),
            location=course_data.get("location"),
            website=course_data.get("website"),
            phone=course_data.get("phone")
        )

    async def import_from_json_file(self, file_path: str) -> Optional[CourseImportData]:
        """Import course data from a JSON file"""
        try:
            with open(file_path) as f:
                course_data = json.load(f)

            # Validate required fields
            required_fields = ["name", "holes_data"]
            for field in required_fields:
                if field not in course_data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate holes data
            holes_data = course_data["holes_data"]
            if len(holes_data) != 18:
                raise ValueError("Course must have exactly 18 holes")

            # Calculate totals
            total_par = sum(hole.get("par", 0) for hole in holes_data)
            total_yards = sum(hole.get("yards", 0) for hole in holes_data)

            return CourseImportData(
                name=course_data["name"],
                description=course_data.get("description"),
                total_par=total_par,
                total_yards=total_yards,
                course_rating=course_data.get("course_rating"),
                slope_rating=course_data.get("slope_rating"),
                holes_data=holes_data,
                source="JSON File",
                last_updated=datetime.now().isoformat(),
                location=course_data.get("location"),
                website=course_data.get("website"),
                phone=course_data.get("phone")
            )

        except Exception as e:
            logger.error(f"Failed to import from JSON file {file_path}: {e}")
            return None

    def save_to_database(self, course_data: CourseImportData) -> bool:
        """Save imported course data to the database"""
        try:
            db = SessionLocal()

            # Check if course already exists
            existing_course = db.query(Course).filter_by(name=course_data.name).first()
            if existing_course:
                logger.info(f"Course {course_data.name} already exists, updating...")
                # Update existing course
                existing_course.description = course_data.description
                existing_course.total_par = course_data.total_par
                existing_course.total_yards = course_data.total_yards
                existing_course.course_rating = course_data.course_rating
                existing_course.slope_rating = course_data.slope_rating
                existing_course.holes_data = course_data.holes_data
                existing_course.updated_at = datetime.now().isoformat()
            else:
                # Create new course
                new_course = Course(
                    name=course_data.name,
                    description=course_data.description,
                    total_par=course_data.total_par,
                    total_yards=course_data.total_yards,
                    course_rating=course_data.course_rating,
                    slope_rating=course_data.slope_rating,
                    holes_data=course_data.holes_data,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                db.add(new_course)

            db.commit()
            logger.info(f"Successfully saved course {course_data.name} to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save course to database: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()

# Convenience functions for easy use
async def import_course_by_name(course_name: str, state: Optional[str] = None, city: Optional[str] = None) -> Optional[CourseImportData]:
    """Import a course by name from external sources"""
    importer = CourseImporter()
    try:
        return await importer.import_course_by_name(course_name, state, city)
    finally:
        await importer.close()

async def import_course_from_json(file_path: str) -> Optional[CourseImportData]:
    """Import a course from a JSON file"""
    importer = CourseImporter()
    try:
        return await importer.import_from_json_file(file_path)
    finally:
        await importer.close()

def save_course_to_database(course_data: CourseImportData) -> bool:
    """Save imported course data to the database"""
    importer = CourseImporter()
    return importer.save_to_database(course_data)
